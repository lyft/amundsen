# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import logging
from collections import namedtuple
from itertools import groupby
from typing import (
    Any, Dict, Iterator, Union,
)

from pyhocon import ConfigFactory, ConfigTree

from databuilder import Scoped
from databuilder.extractor.base_extractor import Extractor
from databuilder.extractor.sql_alchemy_extractor import SQLAlchemyExtractor
from databuilder.models.table_metadata import ColumnMetadata, TableMetadata

TableKey = namedtuple('TableKey', ['schema', 'table_name'])

LOGGER = logging.getLogger(__name__)


class Db2MetadataExtractor(Extractor):
    """
    Extracts Db2 table and column metadata from underlying meta store database using SQLAlchemyExtractor
    """
    # SELECT statement from Db2 SYSIBM to extract table and column metadata
    SQL_STATEMENT = """
    SELECT
      {cluster_source} as cluster, c.TABSCHEMA as schema, c.TABNAME as name, t.REMARKS as description,
      c.COLNAME as col_name,
      CASE WHEN c.TYPENAME='VARCHAR' OR c.TYPENAME='CHARACTER' THEN
      TRIM (TRAILING FROM c.TYPENAME) concat '(' concat c.LENGTH concat ')'
      WHEN c.TYPENAME='DECIMAL' THEN
      TRIM (TRAILING FROM c.TYPENAME) concat '(' concat c.LENGTH concat ',' concat c.SCALE concat ')'
      ELSE TRIM (TRAILING FROM c.TYPENAME) END as col_type,
      c.REMARKS as col_description, c.COLNO as col_sort_order
    FROM SYSCAT.COLUMNS c
    INNER JOIN
      SYSCAT.TABLES as t on c.TABSCHEMA=t.TABSCHEMA and c.TABNAME=t.TABNAME
    {where_clause_suffix}
    ORDER by cluster, schema, name, col_sort_order ;
    """

    # CONFIG KEYS
    WHERE_CLAUSE_SUFFIX_KEY = 'where_clause_suffix'
    CLUSTER_KEY = 'cluster_key'
    DATABASE_KEY = 'database_key'

    # Default values
    DEFAULT_CLUSTER_NAME = 'master'

    DEFAULT_CONFIG = ConfigFactory.from_dict(
        {WHERE_CLAUSE_SUFFIX_KEY: ' ', CLUSTER_KEY: DEFAULT_CLUSTER_NAME}
    )

    def init(self, conf: ConfigTree) -> None:
        conf = conf.with_fallback(Db2MetadataExtractor.DEFAULT_CONFIG)
        self._cluster = conf.get_string(Db2MetadataExtractor.CLUSTER_KEY)

        cluster_source = f"'{self._cluster}'"

        self._database = conf.get_string(Db2MetadataExtractor.DATABASE_KEY, default='db2')

        self.sql_stmt = Db2MetadataExtractor.SQL_STATEMENT.format(
            where_clause_suffix=conf.get_string(Db2MetadataExtractor.WHERE_CLAUSE_SUFFIX_KEY),
            cluster_source=cluster_source
        )

        self._alchemy_extractor = SQLAlchemyExtractor()
        sql_alch_conf = Scoped.get_scoped_conf(conf, self._alchemy_extractor.get_scope())\
            .with_fallback(ConfigFactory.from_dict({SQLAlchemyExtractor.EXTRACT_SQL: self.sql_stmt}))

        self.sql_stmt = sql_alch_conf.get_string(SQLAlchemyExtractor.EXTRACT_SQL)

        LOGGER.info('SQL for Db2 metadata: %s', self.sql_stmt)

        self._alchemy_extractor.init(sql_alch_conf)
        self._extract_iter: Union[None, Iterator] = None

    def extract(self) -> Union[TableMetadata, None]:
        if not self._extract_iter:
            self._extract_iter = self._get_extract_iter()
        try:
            return next(self._extract_iter)
        except StopIteration:
            return None

    def get_scope(self) -> str:
        return 'extractor.db2_metadata'

    def _get_extract_iter(self) -> Iterator[TableMetadata]:
        """
        Using itertools.groupby and raw level iterator, it groups to table and yields TableMetadata
        :return:
        """
        for key, group in groupby(self._get_raw_extract_iter(), self._get_table_key):
            columns = []

            for row in group:
                last_row = row
                columns.append(ColumnMetadata(row['col_name'], row['col_description'],
                                              row['col_type'], row['col_sort_order']))

            yield TableMetadata(self._database, last_row['cluster'],
                                last_row['schema'],
                                last_row['name'],
                                last_row['description'],
                                columns)

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
