# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import logging
import textwrap
from collections import namedtuple
from itertools import groupby
from typing import (
    Any, Dict, Iterator, Union,
)

from pyhocon import ConfigFactory, ConfigTree

from databuilder.extractor import sql_alchemy_extractor
from databuilder.extractor.base_extractor import Extractor
from databuilder.models.table_metadata import ColumnMetadata, TableMetadata

TableKey = namedtuple('TableKey', ['schema', 'table_name'])

LOGGER = logging.getLogger(__name__)


class DruidMetadataExtractor(Extractor):
    """
    Extracts Druid table and column metadata from druid using dbapi extractor
    """
    SQL_STATEMENT = textwrap.dedent("""
        SELECT
        TABLE_SCHEMA as schema,
        TABLE_NAME as name,
        COLUMN_NAME as col_name,
        DATA_TYPE as col_type,
        ORDINAL_POSITION as col_sort_order
        FROM INFORMATION_SCHEMA.COLUMNS
        {where_clause_suffix}
        order by TABLE_SCHEMA, TABLE_NAME, CAST(ORDINAL_POSITION AS int)
    """)

    # CONFIG KEYS
    WHERE_CLAUSE_SUFFIX_KEY = 'where_clause_suffix'
    CLUSTER_KEY = 'cluster'

    DEFAULT_CONFIG = ConfigFactory.from_dict({WHERE_CLAUSE_SUFFIX_KEY: ' ',
                                              CLUSTER_KEY: 'gold'})

    def init(self, conf: ConfigTree) -> None:
        conf = conf.with_fallback(DruidMetadataExtractor.DEFAULT_CONFIG)
        self._cluster = conf.get_string(DruidMetadataExtractor.CLUSTER_KEY)

        self.sql_stmt = DruidMetadataExtractor.SQL_STATEMENT.format(
            where_clause_suffix=conf.get_string(DruidMetadataExtractor.WHERE_CLAUSE_SUFFIX_KEY,
                                                default=''))

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
        return 'extractor.druid_metadata'

    def _get_extract_iter(self) -> Iterator[TableMetadata]:
        """
        Using itertools.groupby and raw level iterator, it groups to table and yields TableMetadata
        :return:
        """
        for key, group in groupby(self._get_raw_extract_iter(), self._get_table_key):
            columns = []
            # no table description and column description
            for row in group:
                last_row = row
                columns.append(ColumnMetadata(name=row['col_name'],
                                              description='',
                                              col_type=row['col_type'],
                                              sort_order=row['col_sort_order']))
            yield TableMetadata(database='druid',
                                cluster=self._cluster,
                                schema=last_row['schema'],
                                name=last_row['name'],
                                description='',
                                columns=columns)

    def _get_raw_extract_iter(self) -> Iterator[Dict[str, Any]]:
        """
        Provides iterator of result row from dbapi extractor
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
