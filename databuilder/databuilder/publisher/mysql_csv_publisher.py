# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import logging
import time
from os import listdir
from os.path import (
    basename, isfile, join, splitext,
)
from typing import (
    Dict, List, Optional, Type,
)

import pandas
from amundsen_rds.models import RDSModel
from amundsen_rds.models.base import Base
from pyhocon import ConfigFactory, ConfigTree
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from databuilder.publisher.base_publisher import Publisher

LOGGER = logging.getLogger(__name__)


class MySQLCSVPublisher(Publisher):
    """
    A Publisher takes the table record folder as input and publishes csv to MySQL.
    The folder contains CSV file(s) for table records.

    The publish job works with rds models and SQLAlchemy ORM for data ingestion into MySQL.
    For more information:
    rds models: https://github.com/amundsen-io/amundsenrds
    SQLAlchemy ORM: https://docs.sqlalchemy.org/en/13/orm/
    """
    # Config keys
    # A directory that contains CSV files for records
    RECORD_FILES_DIR = 'record_files_directory'
    # It is used to provide unique tag to each record
    JOB_PUBLISH_TAG = 'job_publish_tag'

    # Connection string
    CONN_STRING = 'conn_string'
    # If its value is true, SQLAlchemy engine will log all statements
    ENGINE_ECHO = 'engine_echo'
    # Additional arguments used for engine
    CONNECT_ARGS = 'connect_args'
    # A transaction size that determines how often it commits.
    TRANSACTION_SIZE = 'transaction_size'
    # A progress report frequency that determines how often it report the progress.
    PROGRESS_REPORT_FREQUENCY = 'progress_report_frequency'

    _DEFAULT_CONFIG = ConfigFactory.from_dict({TRANSACTION_SIZE: 500,
                                               PROGRESS_REPORT_FREQUENCY: 500,
                                               ENGINE_ECHO: False})

    def __init__(self) -> None:
        super(MySQLCSVPublisher, self).__init__()

    def init(self, conf: ConfigTree) -> None:
        conf = conf.with_fallback(MySQLCSVPublisher._DEFAULT_CONFIG)

        self._count: int = 0
        self._progress_report_frequency = conf.get_int(MySQLCSVPublisher.PROGRESS_REPORT_FREQUENCY)
        self._record_files = self._list_files(conf, MySQLCSVPublisher.RECORD_FILES_DIR)
        self._sorted_record_files = self._sort_record_files(self._record_files)
        self._record_files_iter = iter(self._sorted_record_files)

        connect_args = {k: v for k, v in conf.get_config(MySQLCSVPublisher.CONNECT_ARGS,
                                                         default=ConfigTree()).items()}
        self._engine = create_engine(conf.get_string(MySQLCSVPublisher.CONN_STRING),
                                     echo=conf.get_bool(MySQLCSVPublisher.ENGINE_ECHO),
                                     connect_args=connect_args)
        self._session_factory = sessionmaker(bind=self._engine)
        self._transaction_size = conf.get_int(MySQLCSVPublisher.TRANSACTION_SIZE)

        self._publish_tag: str = conf.get_string(MySQLCSVPublisher.JOB_PUBLISH_TAG)
        if not self._publish_tag:
            raise Exception(f'{MySQLCSVPublisher.JOB_PUBLISH_TAG} should not be empty')

    def _list_files(self, conf: ConfigTree, path_key: str) -> List[str]:
        """
        List files from directory
        :param conf:
        :param path_key:
        :return: List of file paths
        """
        if path_key not in conf:
            return []

        path = conf.get_string(path_key)
        return [join(path, f) for f in listdir(path) if isfile(join(path, f))]

    def _sort_record_files(self, files: List[str]) -> List[str]:
        """
        Sort record files in the order of table dependencies
        :param files:
        :return:
        """
        sorted_table_names = [table.name for table in Base.metadata.sorted_tables]
        return sorted(files, key=lambda file: sorted_table_names.index(self._get_table_name_from_file(file)))

    def _get_table_name_from_file(self, file: str) -> str:
        """
        Get table name from file path
        :param file:
        :return:
        """
        try:
            filename = splitext(basename(file))[0]
            table_name, _ = filename.rsplit('_', 1)
            return table_name
        except Exception as e:
            LOGGER.exception(f'Error encountered while getting table name from file: {file}')
            raise e

    def publish_impl(self) -> None:
        """
        Publish records
        :return:
        """
        start = time.time()

        LOGGER.info(f'Publishing record files: {self._sorted_record_files}')
        session = self._session_factory()
        try:
            while True:
                try:
                    record_file = next(self._record_files_iter)
                    self._publish(record_file=record_file, session=session)
                except StopIteration:
                    break

            LOGGER.info(f'Committed total {self._count} statements')
            LOGGER.info(f'Successfully published. Elapsed: {time.time() - start} seconds')
        except Exception as e:
            LOGGER.exception('Failed to publish. Rolling back.')
            session.rollback()
            raise e
        finally:
            session.close()

    def _publish(self, record_file: str, session: Session) -> None:
        """
        Iterate over each row of the given csv file and convert each record to a rds model instance.
        Then the model instance will be inserted/updated in mysql.
        :param record_file:
        :param session:
        :return:
        """
        with open(record_file, 'r', encoding='utf8') as record_csv:
            table_name = self._get_table_name_from_file(record_file)
            table_model = self._get_model_from_table_name(table_name)
            if not table_model:
                raise RuntimeError(f'Failed to get model for table: {table_name}')

            for record_dict in pandas.read_csv(record_csv, na_filter=False).to_dict(orient='records'):
                record = self._create_record(model=table_model, record_dict=record_dict)
                session.merge(record)
                self._execute(session)
            session.commit()

    def _get_model_from_table_name(self, table_name: str) -> Optional[Type[RDSModel]]:
        """
        Get rds model for the given table name
        :param table_name:
        :return:
        """
        for model in Base._decl_class_registry.values():
            if hasattr(model, '__tablename__') and model.__tablename__ == table_name:
                return model
        return None

    def _create_record(self, model: Type[RDSModel], record_dict: Dict) -> RDSModel:
        """
        Convert the record dict to an instance of the given rds model
        and set additional attributes for the record instance
        :param model:
        :param record_dict:
        :return:
        """
        record = model(**record_dict)
        record.published_tag = self._publish_tag
        record.publisher_last_updated_epoch_ms = int(time.time() * 1000)
        return record

    def _execute(self, session: Session) -> None:
        """
        Commit pending record changes
        :param session:
        :return:
        """
        try:
            self._count += 1
            if self._count > 1 and self._count % self._transaction_size == 0:
                session.commit()
                LOGGER.info(f'Committed {self._count} records so far')

            if self._count > 1 and self._count % self._progress_report_frequency == 0:
                LOGGER.info(f'Processed {self._count} records so far')

        except Exception as e:
            LOGGER.exception('Failed to commit changes')
            raise e

    def get_scope(self) -> str:
        return 'publisher.mysql'
