# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0


import logging
from collections import namedtuple
from itertools import groupby
from typing import (
    Any, Dict, Iterator, Union,
)

from pyhocon import ConfigFactory, ConfigTree
from unidecode import unidecode

from databuilder.extractor import sql_alchemy_extractor
from databuilder.extractor.base_extractor import Extractor
from databuilder.models.table_metadata import ColumnMetadata, TableMetadata

TableKey = namedtuple('TableKey', ['schema', 'table_name'])

LOGGER = logging.getLogger(__name__)


class SnowflakeMetadataExtractor(Extractor):
    """
    Extracts Snowflake table and column metadata from underlying meta store database using SQLAlchemyExtractor.
    Requirements:
        snowflake-connector-python
        snowflake-sqlalchemy
    """
    # SELECT statement from snowflake information_schema to extract table and column metadata
    # https://docs.snowflake.com/en/sql-reference/account-usage.html#label-account-usage-views
    # This can be modified to use account_usage for performance at the cost of latency if necessary.
    SQL_STATEMENT = """
    SELECT
        lower(c.column_name) AS col_name,
        c.comment AS col_description,
        lower(c.data_type) AS col_type,
        lower(c.ordinal_position) AS col_sort_order,
        lower(c.table_catalog) AS database,
        lower({cluster_source}) AS cluster,
        lower(c.table_schema) AS schema,
        lower(c.table_name) AS name,
        t.comment AS description,
        decode(lower(t.table_type), 'view', 'true', 'false') AS is_view
    FROM
        {database}.{schema}.COLUMNS AS c
    LEFT JOIN
        {database}.{schema}.TABLES t
            ON c.TABLE_NAME = t.TABLE_NAME
            AND c.TABLE_SCHEMA = t.TABLE_SCHEMA
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
    # Snowflake Schema Key, used to determine which Snowflake schema to use.
    SNOWFLAKE_SCHEMA_KEY = 'snowflake_schema'

    # Default values
    DEFAULT_CLUSTER_NAME = 'master'

    DEFAULT_CONFIG = ConfigFactory.from_dict(
        {WHERE_CLAUSE_SUFFIX_KEY: ' ',
         CLUSTER_KEY: DEFAULT_CLUSTER_NAME,
         USE_CATALOG_AS_CLUSTER_NAME: True,
         DATABASE_KEY: 'snowflake',
         SNOWFLAKE_DATABASE_KEY: 'prod',
         SNOWFLAKE_SCHEMA_KEY: 'INFORMATION_SCHEMA'}
    )

    def init(self, conf: ConfigTree) -> None:
        conf = conf.with_fallback(SnowflakeMetadataExtractor.DEFAULT_CONFIG)
        self._cluster = conf.get_string(SnowflakeMetadataExtractor.CLUSTER_KEY)

        if conf.get_bool(SnowflakeMetadataExtractor.USE_CATALOG_AS_CLUSTER_NAME):
            cluster_source = "c.table_catalog"
        else:
            cluster_source = f"'{self._cluster}'"

        self._database = conf.get_string(SnowflakeMetadataExtractor.DATABASE_KEY)
        self._schema = conf.get_string(SnowflakeMetadataExtractor.DATABASE_KEY)
        self._snowflake_database = conf.get_string(SnowflakeMetadataExtractor.SNOWFLAKE_DATABASE_KEY)
        self._snowflake_schema = conf.get_string(SnowflakeMetadataExtractor.SNOWFLAKE_SCHEMA_KEY)

        self.sql_stmt = SnowflakeMetadataExtractor.SQL_STATEMENT.format(
            where_clause_suffix=conf.get_string(SnowflakeMetadataExtractor.WHERE_CLAUSE_SUFFIX_KEY),
            cluster_source=cluster_source,
            database=self._snowflake_database,
            schema=self._snowflake_schema
        )

        LOGGER.info('SQL for snowflake metadata: %s', self.sql_stmt)

        self._alchemy_extractor = sql_alchemy_extractor.from_surrounding_config(conf, self.sql_stmt)
        self._extract_iter: Union[None, Iterator] = None

    def close(self) -> None:
        if getattr(self, '_alchemy_extractor', None) is not None:
            self._alchemy_extractor.close()

    def extract(self) -> Union[TableMetadata, None]:
        if not self._extract_iter:
            self._extract_iter = self._get_extract_iter()
        try:
            return next(self._extract_iter)
        except StopIteration:
            return None

    def get_scope(self) -> str:
        return 'extractor.snowflake'

    def _get_extract_iter(self) -> Iterator[TableMetadata]:
        """
        Using itertools.groupby and raw level iterator, it groups to table and yields TableMetadata
        :return:
        """
        for key, group in groupby(self._get_raw_extract_iter(), self._get_table_key):
            columns = []

            for row in group:
                last_row = row
                columns.append(ColumnMetadata(
                    row['col_name'],
                    unidecode(row['col_description']) if row['col_description'] else None,
                    row['col_type'],
                    row['col_sort_order'])
                )

            yield TableMetadata(self._database, last_row['cluster'],
                                last_row['schema'],
                                last_row['name'],
                                unidecode(last_row['description']) if last_row['description'] else None,
                                columns,
                                last_row['is_view'] == 'true')

    def _get_raw_extract_iter(self) -> Iterator[Dict[str, Any]]:
        """
        Provides iterator of result row from SQLAlchemy extractor
        :return:
        """
        row = self._alchemy_extractor.extract()
        while row:
            yield row
            row = self._alchemy_extractor.extract()

    def _get_table_key(self, row: Dict[str, Any]) -> Union[TableKey, None]:
        """
        Table key consists of schema and table name
        :param row:
        :return:
        """
        if row:
            return TableKey(schema=row['schema'], table_name=row['name'])

        return None
