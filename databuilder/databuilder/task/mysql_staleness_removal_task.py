# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import logging
import time
from typing import (
    Any, Dict, Set, Type,
)

from amundsen_rds.models import RDSModel
from amundsen_rds.models.base import Base
from pyhocon import ConfigFactory, ConfigTree
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker

from databuilder import Scoped
from databuilder.task.base_task import Task

LOGGER = logging.getLogger(__name__)


class MySQLStalenessRemovalTask(Task):
    """
    A Specific task to remove stale records in MySQL. It will use either the "published_tag" or
    "publisher_last_updated_epoch_ms" attribute assigned from the MySqlCsvPublisher. If "published tag" is different
    from the one it is getting from the config or if the "publisher_last_updated_epoch_ms" is less than the cutoff,
    it will regard the record as stale. Not all resources are being published by MySQLCSVPublisher and you can only
    set specific model table names to perform this deletion.
    Note: This task performs a cascade delete and will delete all the orphan records in the child tables of the stale
    records.

    """
    # Connection string
    CONN_STRING = "conn_string"
    # If its value is true, SQLAlchemy engine will log all statements
    ENGINE_ECHO = 'engine_echo'
    # Additional arguments used for engine
    CONNECT_ARGS = 'connect_args'

    TARGET_TABLES = "target_tables"
    DRY_RUN = "dry_run"
    # Staleness max percentage. Safety net to prevent majority of data being deleted.
    STALENESS_MAX_PCT = "staleness_max_pct"
    # Staleness max percentage per table. Safety net to prevent majority of data being deleted.
    STALENESS_PCT_MAX_DICT = "staleness_max_pct_dict"
    # If the published_tag value is different from the one in config, the record is determined to be stale
    PUBLISHED_TAG = "job_publish_tag"
    # Using this milliseconds and published timestamp to determine staleness
    MS_TO_EXPIRE = "milliseconds_to_expire"
    MIN_MS_TO_EXPIRE = "minimum_milliseconds_to_expire"

    _DEFAULT_CONFIG = ConfigFactory.from_dict({STALENESS_MAX_PCT: 5,
                                              TARGET_TABLES: [],
                                              STALENESS_PCT_MAX_DICT: {},
                                              MIN_MS_TO_EXPIRE: 86400000,
                                              DRY_RUN: False,
                                              ENGINE_ECHO: False})

    def get_scope(self) -> str:
        return 'task.mysql_remove_stale_data'

    def init(self, conf: ConfigTree) -> None:
        conf = Scoped.get_scoped_conf(conf, self.get_scope()) \
            .with_fallback(conf) \
            .with_fallback(MySQLStalenessRemovalTask._DEFAULT_CONFIG)
        self.target_tables = set(conf.get_list(MySQLStalenessRemovalTask.TARGET_TABLES))
        self.target_table_model_dict = self._get_target_table_model_dict(self.target_tables)
        self.dry_run = conf.get_bool(MySQLStalenessRemovalTask.DRY_RUN)
        self.staleness_max_pct = conf.get_int(MySQLStalenessRemovalTask.STALENESS_MAX_PCT)
        self.staleness_max_pct_dict = conf.get(MySQLStalenessRemovalTask.STALENESS_PCT_MAX_DICT)

        if MySQLStalenessRemovalTask.PUBLISHED_TAG in conf and MySQLStalenessRemovalTask.MS_TO_EXPIRE in conf:
            raise Exception(f'Cannot have both {MySQLStalenessRemovalTask.PUBLISHED_TAG} and '
                            f'{MySQLStalenessRemovalTask.MS_TO_EXPIRE} in job config')

        self.ms_to_expire = None
        if MySQLStalenessRemovalTask.MS_TO_EXPIRE in conf:
            self.ms_to_expire = conf.get_int(MySQLStalenessRemovalTask.MS_TO_EXPIRE)
            if self.ms_to_expire < conf.get_int(MySQLStalenessRemovalTask.MIN_MS_TO_EXPIRE):
                raise Exception(f'{MySQLStalenessRemovalTask.MS_TO_EXPIRE} is too small')
            self.marker = self.ms_to_expire
        else:
            self.marker = conf.get_string(MySQLStalenessRemovalTask.PUBLISHED_TAG)

        connect_args = {k: v for k, v in conf.get_config(MySQLStalenessRemovalTask.CONNECT_ARGS,
                                                         default=ConfigTree()).items()}
        self._engine = create_engine(conf.get_string(MySQLStalenessRemovalTask.CONN_STRING),
                                     echo=conf.get_bool(MySQLStalenessRemovalTask.ENGINE_ECHO),
                                     connect_args=connect_args)
        self._session_factory = sessionmaker(bind=self._engine)
        self._session = self._session_factory()

    def _get_target_table_model_dict(self, target_tables: Set[str]) -> Dict[str, Type[RDSModel]]:
        """
        Returns a dictionary with a table name to the corresponding RDS model class mapping.
        :param target_tables:
        :return:
        """
        target_table_model_dict: Dict[str, Type[RDSModel]] = {}
        for model in Base._decl_class_registry.values():
            if hasattr(model, '__tablename__') and model.__tablename__ in target_tables:
                target_table_model_dict[model.__tablename__] = model
        return target_table_model_dict

    def run(self) -> None:
        """
        For each table performs a safety check to make sure this operation does not delete more than a threshold
        where default threshold is 5%. Once it passes a safety check, it cascade deletes the stale records and all
        the referencing records. The target tables are traversed acc. to foreign key dependency (i.e in the order of
        child tables to parent tables) to try to keep the actual deleted record count consistent with the validation
        percentage (which reflects the staleness pct only from a single table and does not take into account the
        referenced tables data which will be deleted in a cascade delete)
        :return:
        """
        sorted_table_names = [table.name for table in Base.metadata.sorted_tables]
        sorted_target_tables = sorted(
            self.target_tables, key=lambda table: sorted_table_names.index(table), reverse=True)
        try:
            for table_name in sorted_target_tables:
                target_model_class = self.target_table_model_dict.get(table_name, None)
                if target_model_class:
                    staleness_pct = self._validate_record_staleness_pct(target_model_class=target_model_class)
                    if self.dry_run:
                        LOGGER.info('Skipping deleting records since it is a Dry Run.')
                        continue
                    if staleness_pct > 0:
                        self._delete_stale_records(target_model_class=target_model_class)
                else:
                    raise Exception(f'Failed to get corresponding model for {table_name}')
        except Exception as e:
            self._session.rollback()
            raise e
        finally:
            self._session.close()

    def _validate_record_staleness_pct(self, target_model_class: Type[RDSModel]) -> int:
        """
        Validation method.Focused on limit the risk of deleting records.
        - Check if deleted records for a table will be within 5% of the total records in the table.
        :param target_model_class:
        :return:
        """
        total_records_count = self._session.query(func.count('*')).select_from(target_model_class).scalar()
        stale_records_count = self._session.query(func.count('*')).select_from(target_model_class) \
            .filter(self._get_stale_records_filter_condition(target_model_class=target_model_class)).scalar()

        staleness_pct = 0
        target_table = target_model_class.__tablename__
        if stale_records_count:
            staleness_pct = stale_records_count * 100 / total_records_count
            threshold = self.staleness_max_pct_dict.get(target_table, self.staleness_max_pct)
            if staleness_pct >= threshold:
                raise Exception(f'Staleness percentage of {target_table} is {staleness_pct} %. '
                                f'Stopping due to over threshold {threshold} %')
            LOGGER.info(f'Will be deleting {stale_records_count} {target_table} '
                        f'record(s) or {staleness_pct}% of {target_table} data.')
        else:
            LOGGER.info(f'No stale records in {target_table}')
        return staleness_pct

    def _delete_stale_records(self, target_model_class: Type[RDSModel]) -> None:
        target_table = target_model_class.__tablename__
        try:
            deleted_records_count = self._session.query(target_model_class).filter(
                self._get_stale_records_filter_condition(target_model_class=target_model_class)).delete()
            self._session.commit()
            LOGGER.info(f'Deleted {deleted_records_count} record(s) of {target_table}')
        except Exception as e:
            LOGGER.exception(f'Failed to delete stale records for {target_table}')
            raise e

    def _get_stale_records_filter_condition(self, target_model_class: Type[RDSModel]) -> Any:
        """
        Return the appropriate stale records filter condition depending on which field is used to expire stale data.
        :param target_model_class:
        :return:
        """
        if self.ms_to_expire:
            current_time = int(time.time() * 1000)
            filter_condition = target_model_class.publisher_last_updated_epoch_ms < (
                current_time - self.marker)
        else:
            filter_condition = target_model_class.published_tag != self.marker
        return filter_condition
