# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import logging
from typing import Iterator, Union

from pyhocon import ConfigFactory, ConfigTree

from databuilder.extractor import sql_alchemy_extractor
from databuilder.extractor.base_extractor import Extractor
from databuilder.models.table_last_updated import TableLastUpdated

LOGGER = logging.getLogger(__name__)


class SnowflakeTableLastUpdatedExtractor(Extractor):
    """
    Extracts Snowflake table last update time from INFORMATION_SCHEMA metadata tables using SQLAlchemyExtractor.
    Requirements:
        snowflake-connector-python
        snowflake-sqlalchemy
    """
    # https://docs.snowflake.com/en/sql-reference/info-schema/views.html#columns
    # 'last_altered' column in 'TABLES` metadata view under 'INFORMATION_SCHEMA' contains last time when the table was
    # updated (both DML and DDL update). Below query fetches that column for each table.
    SQL_STATEMENT = """
        SELECT
            lower({cluster_source}) AS cluster,
            lower(t.table_schema) AS schema,
            lower(t.table_name) AS table_name,
            DATE_PART(EPOCH, t.last_altered) AS last_updated_time
        FROM
            {database}.INFORMATION_SCHEMA.TABLES t
        {where_clause_suffix};
        """

    # CONFIG KEYS
    WHERE_CLAUSE_SUFFIX_KEY = 'where_clause_suffix'
    CLUSTER_KEY = 'cluster_key'
    USE_CATALOG_AS_CLUSTER_NAME = 'use_catalog_as_cluster_name'
    # Database Key, used to identify the database type in the UI.
    DATABASE_KEY = 'database_key'
    # Snowflake Database Key, used to determine which Snowflake database to connect to.
    SNOWFLAKE_DATABASE_KEY = 'snowflake_database'

    # Default values
    DEFAULT_CLUSTER_NAME = 'master'

    DEFAULT_CONFIG = ConfigFactory.from_dict(
        {WHERE_CLAUSE_SUFFIX_KEY: ' WHERE t.last_altered IS NOT NULL ',
         CLUSTER_KEY: DEFAULT_CLUSTER_NAME,
         USE_CATALOG_AS_CLUSTER_NAME: True,
         DATABASE_KEY: 'snowflake',
         SNOWFLAKE_DATABASE_KEY: 'prod'}
    )

    def init(self, conf: ConfigTree) -> None:
        conf = conf.with_fallback(SnowflakeTableLastUpdatedExtractor.DEFAULT_CONFIG)
        self._cluster = conf.get_string(SnowflakeTableLastUpdatedExtractor.CLUSTER_KEY)

        if conf.get_bool(SnowflakeTableLastUpdatedExtractor.USE_CATALOG_AS_CLUSTER_NAME):
            cluster_source = "t.table_catalog"
        else:
            cluster_source = f"'{self._cluster}'"

        self._database = conf.get_string(SnowflakeTableLastUpdatedExtractor.DATABASE_KEY)
        self._snowflake_database = conf.get_string(SnowflakeTableLastUpdatedExtractor.SNOWFLAKE_DATABASE_KEY)

        self.sql_stmt = SnowflakeTableLastUpdatedExtractor.SQL_STATEMENT.format(
            where_clause_suffix=conf.get_string(SnowflakeTableLastUpdatedExtractor.WHERE_CLAUSE_SUFFIX_KEY),
            cluster_source=cluster_source,
            database=self._snowflake_database
        )

        LOGGER.info('SQL for snowflake table last updated timestamp: %s', self.sql_stmt)

        # use an sql_alchemy_extractor to execute sql
        self._alchemy_extractor = sql_alchemy_extractor.from_surrounding_config(conf, self.sql_stmt)
        self._extract_iter: Union[None, Iterator] = None

    def close(self) -> None:
        if getattr(self, '_alchemy_extractor', None) is not None:
            self._alchemy_extractor.close()

    def extract(self) -> Union[TableLastUpdated, None]:
        if not self._extract_iter:
            self._extract_iter = self._get_extract_iter()
        try:
            return next(self._extract_iter)
        except StopIteration:
            return None

    def get_scope(self) -> str:
        return 'extractor.snowflake_table_last_updated'

    def _get_extract_iter(self) -> Iterator[TableLastUpdated]:
        """
        Provides iterator of result row from SQLAlchemy extractor
        """
        tbl_last_updated_row = self._alchemy_extractor.extract()
        while tbl_last_updated_row:
            yield TableLastUpdated(table_name=tbl_last_updated_row['table_name'],
                                   last_updated_time_epoch=tbl_last_updated_row['last_updated_time'],
                                   schema=tbl_last_updated_row['schema'],
                                   db=self._database,
                                   cluster=tbl_last_updated_row['cluster'])
            tbl_last_updated_row = self._alchemy_extractor.extract()
