# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import logging
import time
from datetime import datetime
from functools import wraps
from multiprocessing.pool import ThreadPool
from typing import (
    Any, Iterator, List, Union,
)

from pyhocon import ConfigFactory, ConfigTree
from pytz import UTC

from databuilder import Scoped
from databuilder.extractor.base_extractor import Extractor
from databuilder.extractor.sql_alchemy_extractor import SQLAlchemyExtractor
from databuilder.filesystem.filesystem import FileSystem, is_client_side_error
from databuilder.models.table_last_updated import TableLastUpdated

LOGGER = logging.getLogger(__name__)
OLDEST_TIMESTAMP = datetime.fromtimestamp(0, UTC)


def fs_error_handler(f: Any) -> Any:
    """
    A Decorator that handles error from FileSystem for HiveTableLastUpdatedExtractor use case
    If it's client side error, it logs in INFO level, and other errors is logged as error level with stacktrace.
    The decorator is intentionally not re-raising exception so that it can isolate the error.
    :param f:
    :return:
    """

    @wraps(f)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return f(*args, **kwargs)
        except Exception as e:
            if is_client_side_error(e):
                LOGGER.info('Invalid metadata. Skipping. args: %s, kwargs: %s. error: %s', args, kwargs, e)
                return None
            else:
                LOGGER.exception('Unknown exception while processing args: %s, kwargs: %s', args, kwargs)
                return None

    return wrapper


class HiveTableLastUpdatedExtractor(Extractor):
    """
    Uses Hive metastore and underlying storage to figure out last updated timestamp of table.

    It turned out that we cannot use table param "last_modified_time", as it provides DDL date not DML date.
    For this reason, we are utilizing underlying file of Hive to fetch latest updated date.
    However, it is not efficient to poke all files in Hive, and it only poke underlying storage for non-partitioned
    table. For partitioned table, it will fetch partition created timestamp, and it's close enough for last updated
    timestamp.

    """
    PARTITION_TABLE_SQL_STATEMENT = """
    SELECT
    DBS.NAME as `schema`,
    TBL_NAME as table_name,
    MAX(PARTITIONS.CREATE_TIME) as last_updated_time
    FROM TBLS
    JOIN DBS ON TBLS.DB_ID = DBS.DB_ID
    JOIN PARTITIONS ON TBLS.TBL_ID = PARTITIONS.TBL_ID
    {where_clause_suffix}
    GROUP BY `schema`, table_name
    ORDER BY `schema`, table_name;
    """

    NON_PARTITIONED_TABLE_SQL_STATEMENT = """
    SELECT
    DBS.NAME as `schema`,
    TBL_NAME as table_name,
    SDS.LOCATION as location
    FROM TBLS
    JOIN DBS ON TBLS.DB_ID = DBS.DB_ID
    JOIN SDS ON TBLS.SD_ID = SDS.SD_ID
    {where_clause_suffix}
    ORDER BY `schema`, table_name;
    """

    # Additional where clause for non partitioned table SQL
    ADDTIONAL_WHERE_CLAUSE = """ NOT EXISTS (SELECT * FROM PARTITIONS WHERE PARTITIONS.TBL_ID = TBLS.TBL_ID)
    AND NOT EXISTS (SELECT * FROM PARTITION_KEYS WHERE PARTITION_KEYS.TBL_ID = TBLS.TBL_ID)
    """

    DATABASE = 'hive'

    # CONFIG KEYS
    PARTITIONED_TABLE_WHERE_CLAUSE_SUFFIX_KEY = 'partitioned_table_where_clause_suffix'
    NON_PARTITIONED_TABLE_WHERE_CLAUSE_SUFFIX_KEY = 'non_partitioned_table_where_clause_suffix'
    CLUSTER_KEY = 'cluster'
    # number of threads that fetches metadata from FileSystem
    FS_WORKER_POOL_SIZE = 'fs_worker_pool_size'
    FS_WORKER_TIMEOUT_SEC = 'fs_worker_timeout_sec'
    # If number of files that it needs to fetch metadata is larger than this threshold, it will skip the table.
    FILE_CHECK_THRESHOLD = 'file_check_threshold'

    DEFAULT_CONFIG = ConfigFactory.from_dict({PARTITIONED_TABLE_WHERE_CLAUSE_SUFFIX_KEY: ' ',
                                              NON_PARTITIONED_TABLE_WHERE_CLAUSE_SUFFIX_KEY: ' ',
                                              CLUSTER_KEY: 'gold',
                                              FS_WORKER_POOL_SIZE: 500,
                                              FS_WORKER_TIMEOUT_SEC: 60,
                                              FILE_CHECK_THRESHOLD: -1})

    def init(self, conf: ConfigTree) -> None:
        self._conf = conf.with_fallback(HiveTableLastUpdatedExtractor.DEFAULT_CONFIG)

        pool_size = self._conf.get_int(HiveTableLastUpdatedExtractor.FS_WORKER_POOL_SIZE)
        LOGGER.info('Using thread pool size: %s', pool_size)
        self._fs_worker_pool = ThreadPool(processes=pool_size)
        self._fs_worker_timeout = self._conf.get_int(HiveTableLastUpdatedExtractor.FS_WORKER_TIMEOUT_SEC)
        LOGGER.info('Using thread timeout: %s seconds', self._fs_worker_timeout)

        self._cluster = self._conf.get_string(HiveTableLastUpdatedExtractor.CLUSTER_KEY)

        self._partitioned_table_extractor = self._get_partitioned_table_sql_alchemy_extractor()
        self._non_partitioned_table_extractor = self._get_non_partitioned_table_sql_alchemy_extractor()
        self._fs = self._get_filesystem()
        self._last_updated_filecheck_threshold \
            = self._conf.get_int(HiveTableLastUpdatedExtractor.FILE_CHECK_THRESHOLD)

        self._extract_iter: Union[None, Iterator] = None

    def _get_partitioned_table_sql_alchemy_extractor(self) -> Extractor:
        """
        Getting an SQLAlchemy extractor that extracts last updated timestamp for partitioned table.
        :return: SQLAlchemyExtractor
        """

        sql_stmt = HiveTableLastUpdatedExtractor.PARTITION_TABLE_SQL_STATEMENT.format(
            where_clause_suffix=self._conf.get_string(
                HiveTableLastUpdatedExtractor.PARTITIONED_TABLE_WHERE_CLAUSE_SUFFIX_KEY, ' '))

        LOGGER.info('SQL for partitioned table against Hive metastore: %s', sql_stmt)

        sql_alchemy_extractor = SQLAlchemyExtractor()
        sql_alchemy_conf = Scoped.get_scoped_conf(self._conf, sql_alchemy_extractor.get_scope()) \
            .with_fallback(ConfigFactory.from_dict({SQLAlchemyExtractor.EXTRACT_SQL: sql_stmt}))
        sql_alchemy_extractor.init(sql_alchemy_conf)
        return sql_alchemy_extractor

    def _get_non_partitioned_table_sql_alchemy_extractor(self) -> Extractor:
        """
        Getting an SQLAlchemy extractor that extracts storage location for non-partitioned table for further probing
        last updated timestamp

        :return: SQLAlchemyExtractor
        """
        if HiveTableLastUpdatedExtractor.NON_PARTITIONED_TABLE_WHERE_CLAUSE_SUFFIX_KEY in self._conf:
            where_clause_suffix = """
            {}
            AND {}
            """.format(self._conf.get_string(
                HiveTableLastUpdatedExtractor.NON_PARTITIONED_TABLE_WHERE_CLAUSE_SUFFIX_KEY),
                HiveTableLastUpdatedExtractor.ADDTIONAL_WHERE_CLAUSE)
        else:
            where_clause_suffix = 'WHERE {}'.format(HiveTableLastUpdatedExtractor.ADDTIONAL_WHERE_CLAUSE)

        sql_stmt = HiveTableLastUpdatedExtractor.NON_PARTITIONED_TABLE_SQL_STATEMENT.format(
            where_clause_suffix=where_clause_suffix)

        LOGGER.info('SQL for non-partitioned table against Hive metastore: %s', sql_stmt)

        sql_alchemy_extractor = SQLAlchemyExtractor()
        sql_alchemy_conf = Scoped.get_scoped_conf(self._conf, sql_alchemy_extractor.get_scope()) \
            .with_fallback(ConfigFactory.from_dict({SQLAlchemyExtractor.EXTRACT_SQL: sql_stmt}))
        sql_alchemy_extractor.init(sql_alchemy_conf)
        return sql_alchemy_extractor

    def _get_filesystem(self) -> FileSystem:
        fs = FileSystem()
        fs.init(Scoped.get_scoped_conf(self._conf, fs.get_scope()))
        return fs

    def extract(self) -> Union[TableLastUpdated, None]:
        if not self._extract_iter:
            self._extract_iter = self._get_extract_iter()
        try:
            return next(self._extract_iter)
        except StopIteration:
            return None

    def get_scope(self) -> str:
        return 'extractor.hive_table_last_updated'

    def _get_extract_iter(self) -> Iterator[TableLastUpdated]:
        """
        An iterator that utilizes Generator pattern. First it provides TableLastUpdated objects for partitioned
        table, straight from partitioned_table_extractor (SQLAlchemyExtractor)

        Once partitioned table is done, it uses non_partitioned_table_extractor to get storage location of table,
        and probing files under storage location to get max timestamp per table.
        :return:
        """

        partitioned_tbl_row = self._partitioned_table_extractor.extract()
        while partitioned_tbl_row:
            yield TableLastUpdated(table_name=partitioned_tbl_row['table_name'],
                                   last_updated_time_epoch=partitioned_tbl_row['last_updated_time'],
                                   schema=partitioned_tbl_row['schema'],
                                   db=HiveTableLastUpdatedExtractor.DATABASE,
                                   cluster=self._cluster)
            partitioned_tbl_row = self._partitioned_table_extractor.extract()

        LOGGER.info('Extracting non-partitioned table')
        count = 0
        non_partitioned_tbl_row = self._non_partitioned_table_extractor.extract()
        while non_partitioned_tbl_row:
            count += 1
            if count % 10 == 0:
                LOGGER.info('Processed %i non-partitioned tables', count)

            if not non_partitioned_tbl_row['location']:
                LOGGER.warning('Skipping as no storage location available. %s', non_partitioned_tbl_row)
                non_partitioned_tbl_row = self._non_partitioned_table_extractor.extract()
                continue

            start = time.time()
            table_last_updated = self._get_last_updated_datetime_from_filesystem(
                table=non_partitioned_tbl_row['table_name'],
                schema=non_partitioned_tbl_row['schema'],
                storage_location=non_partitioned_tbl_row['location'])
            LOGGER.info('Elapsed: %i seconds', time.time() - start)

            if table_last_updated:
                yield table_last_updated

            non_partitioned_tbl_row = self._non_partitioned_table_extractor.extract()

    def _get_last_updated_datetime_from_filesystem(self,
                                                   table: str,
                                                   schema: str,
                                                   storage_location: str,
                                                   ) -> Union[TableLastUpdated, None]:
        """
        Fetching metadata within files under storage_location to get latest timestamp.
        (First level only under storage_location)
        Utilizes thread pool to enhance performance. Not using processpool, as it's almost entirely IO bound operation.

        :param table:
        :param schema:
        :param storage_location:
        :return:
        """

        if LOGGER.isEnabledFor(logging.DEBUG):
            LOGGER.debug(f'Getting last updated datetime for {schema}.{table} in {storage_location}')

        last_updated = OLDEST_TIMESTAMP

        paths = self._ls(storage_location)
        if not paths:
            LOGGER.info(f'{schema}.{table} does not have any file in path {storage_location}. Skipping')
            return None

        LOGGER.info(f'Fetching metadata for {schema}.{table} of {len(paths)} files')

        if 0 < self._last_updated_filecheck_threshold < len(paths):
            LOGGER.info(f'Skipping {schema}.{table} due to too many files. '
                        f'{len(paths)} files exist in {storage_location}')
            return None

        time_stamp_futures = \
            [self._fs_worker_pool.apply_async(self._get_timestamp, (path, schema, table, storage_location))
             for path in paths]
        for time_stamp_future in time_stamp_futures:
            try:
                time_stamp = time_stamp_future.get(timeout=self._fs_worker_timeout)
                if time_stamp:
                    last_updated = max(time_stamp, last_updated)
            except TimeoutError:
                LOGGER.warning('Timed out on paths %s . Skipping', paths)

        if last_updated == OLDEST_TIMESTAMP:
            LOGGER.info(f'No timestamp was derived on {schema}.{table} from location: {storage_location} . Skipping')
            return None

        result = TableLastUpdated(table_name=table,
                                  last_updated_time_epoch=int((last_updated - OLDEST_TIMESTAMP).total_seconds()),
                                  schema=schema,
                                  db=HiveTableLastUpdatedExtractor.DATABASE,
                                  cluster=self._cluster)

        return result

    @fs_error_handler
    def _ls(self, path: str) -> List[str]:
        """
        An wrapper to FileSystem.ls to use fs_error_handler decorator
        :param path:
        :return:
        """
        return self._fs.ls(path)

    @fs_error_handler
    def _get_timestamp(self,
                       path: str,
                       schema: str,
                       table: str,
                       storage_location: str,
                       ) -> Union[datetime, None]:
        """
        An wrapper to FileSystem.ls to use fs_error_handler decorator
        :param path:
        :param schema:
        :param table:
        :param storage_location:
        :return:
        """
        if not path:
            LOGGER.info(f'Empty path {path} on {schema}.{table} in storage location {storage_location} . Skipping')
            return None

        if not self._fs.is_file(path):
            return None

        file_metadata = self._fs.info(path)
        return file_metadata.last_updated
