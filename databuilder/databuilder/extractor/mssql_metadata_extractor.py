# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import logging
from collections import namedtuple
from itertools import groupby
from typing import (
    Any, Dict, Iterator, Union,
)

from pyhocon import ConfigFactory, ConfigTree

from databuilder.extractor import sql_alchemy_extractor
from databuilder.extractor.base_extractor import Extractor
from databuilder.models.table_metadata import ColumnMetadata, TableMetadata

TableKey = namedtuple('TableKey', ['schema_name', 'table_name'])

LOGGER = logging.getLogger(__name__)


class MSSQLMetadataExtractor(Extractor):
    """
    Extracts Microsoft SQL Server table and column metadata from underlying
    meta store database using SQLAlchemyExtractor
    """

    # SELECT statement from MS SQL to extract table and column metadata
    SQL_STATEMENT = """
        SELECT DISTINCT
            {cluster_source} AS cluster,
            TBL.TABLE_SCHEMA AS [schema_name],
            TBL.TABLE_NAME AS [name],
            CAST(PROP.VALUE AS NVARCHAR(MAX)) AS [description],
            COL.COLUMN_NAME AS [col_name],
            COL.DATA_TYPE AS [col_type],
            CAST(PROP_COL.VALUE AS NVARCHAR(MAX)) AS [col_description],
            COL.ORDINAL_POSITION AS col_sort_order
        FROM INFORMATION_SCHEMA.TABLES TBL
        INNER JOIN INFORMATION_SCHEMA.COLUMNS COL
            ON (COL.TABLE_NAME = TBL.TABLE_NAME
                AND COL.TABLE_SCHEMA = TBL.TABLE_SCHEMA )
        LEFT JOIN SYS.EXTENDED_PROPERTIES PROP
            ON (PROP.MAJOR_ID = OBJECT_ID(TBL.TABLE_SCHEMA + '.' + TBL.TABLE_NAME)
                AND PROP.MINOR_ID = 0
                AND PROP.NAME = 'MS_Description')
        LEFT JOIN SYS.EXTENDED_PROPERTIES PROP_COL
            ON (PROP_COL.MAJOR_ID = OBJECT_ID(TBL.TABLE_SCHEMA + '.' + TBL.TABLE_NAME)
                AND PROP_COL.MINOR_ID = COL.ORDINAL_POSITION
                AND PROP_COL.NAME = 'MS_Description')
        WHERE TBL.TABLE_TYPE = 'base table' {where_clause_suffix}
        ORDER BY
            CLUSTER,
            SCHEMA_NAME,
            NAME,
            COL_SORT_ORDER
        ;
    """

    # CONFIG KEYS
    WHERE_CLAUSE_SUFFIX_KEY = 'where_clause_suffix'
    CLUSTER_KEY = 'cluster_key'
    USE_CATALOG_AS_CLUSTER_NAME = 'use_catalog_as_cluster_name'
    DATABASE_KEY = 'database_key'

    # Default values
    DEFAULT_CLUSTER_NAME = 'DB_NAME()'

    DEFAULT_CONFIG = ConfigFactory.from_dict({
        WHERE_CLAUSE_SUFFIX_KEY: '',
        CLUSTER_KEY: DEFAULT_CLUSTER_NAME,
        USE_CATALOG_AS_CLUSTER_NAME: True}
    )

    DEFAULT_WHERE_CLAUSE_VALUE = 'and tbl.table_schema in {schemas}'

    def init(self, conf: ConfigTree) -> None:
        conf = conf.with_fallback(MSSQLMetadataExtractor.DEFAULT_CONFIG)

        self._cluster = conf.get_string(MSSQLMetadataExtractor.CLUSTER_KEY)

        if conf.get_bool(MSSQLMetadataExtractor.USE_CATALOG_AS_CLUSTER_NAME):
            cluster_source = "DB_NAME()"
        else:
            cluster_source = f"'{self._cluster}'"

        self._database = conf.get_string(
            MSSQLMetadataExtractor.DATABASE_KEY,
            default='mssql')

        config_where_clause = conf.get_string(
            MSSQLMetadataExtractor.WHERE_CLAUSE_SUFFIX_KEY)

        LOGGER.info("Crawling for Schemas %s", config_where_clause)

        if config_where_clause:
            where_clause_suffix = MSSQLMetadataExtractor \
                .DEFAULT_WHERE_CLAUSE_VALUE \
                .format(schemas=config_where_clause)
        else:
            where_clause_suffix = ''

        self.sql_stmt = MSSQLMetadataExtractor.SQL_STATEMENT.format(
            where_clause_suffix=where_clause_suffix,
            cluster_source=cluster_source
        )

        LOGGER.info('SQL for MS SQL Metadata: %s', self.sql_stmt)

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
        return 'extractor.mssql_metadata'

    def _get_extract_iter(self) -> Iterator[TableMetadata]:
        """
        Using itertools.groupby and raw level iterator,
        it groups to table and yields TableMetadata
        :return:
        """
        for key, group in groupby(self._get_raw_extract_iter(), self._get_table_key):
            columns = []

            for row in group:
                last_row = row
                columns.append(
                    ColumnMetadata(
                        row['col_name'],
                        row['col_description'],
                        row['col_type'],
                        row['col_sort_order']))

            yield TableMetadata(
                self._database,
                last_row['cluster'],
                last_row['schema_name'],
                last_row['name'],
                last_row['description'],
                columns,
                tags=last_row['schema_name'])

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
            return TableKey(
                schema_name=row['schema_name'],
                table_name=row['name'])

        return None
