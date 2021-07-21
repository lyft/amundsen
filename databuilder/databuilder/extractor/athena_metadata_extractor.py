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

TableKey = namedtuple('TableKey', ['schema', 'table_name'])

LOGGER = logging.getLogger(__name__)


class AthenaMetadataExtractor(Extractor):
    """
    Extracts Athena table and column metadata from underlying meta store database using SQLAlchemyExtractor
    """

    SQL_STATEMENT = """
    SELECT
        {catalog_source} as cluster, table_schema as schema, table_name as name, column_name as col_name,
        data_type as col_type,ordinal_position as col_sort_order,
        comment as col_description, extra_info as extras from information_schema.columns
        {where_clause_suffix}
        ORDER by cluster, schema, name, col_sort_order ;
    """

    # CONFIG KEYS
    WHERE_CLAUSE_SUFFIX_KEY = 'where_clause_suffix'
    CATALOG_KEY = 'catalog_source'

    # Default values
    DEFAULT_CLUSTER_NAME = 'master'

    DEFAULT_CONFIG = ConfigFactory.from_dict(
        {WHERE_CLAUSE_SUFFIX_KEY: ' ', CATALOG_KEY: DEFAULT_CLUSTER_NAME}
    )

    def init(self, conf: ConfigTree) -> None:
        conf = conf.with_fallback(AthenaMetadataExtractor.DEFAULT_CONFIG)
        self._cluster = conf.get_string(AthenaMetadataExtractor.CATALOG_KEY)

        self.sql_stmt = AthenaMetadataExtractor.SQL_STATEMENT.format(
            where_clause_suffix=conf.get_string(AthenaMetadataExtractor.WHERE_CLAUSE_SUFFIX_KEY),
            catalog_source=self._cluster
        )

        LOGGER.info('SQL for Athena metadata: %s', self.sql_stmt)

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
        return 'extractor.athena_metadata'

    def _get_extract_iter(self) -> Iterator[TableMetadata]:
        """
        Using itertools.groupby and raw level iterator, it groups to table and yields TableMetadata
        :return:
        """

        for key, group in groupby(self._get_raw_extract_iter(), self._get_table_key):
            columns = []

            for row in group:
                last_row = row
                columns.append(ColumnMetadata(row['col_name'],
                                              row['extras'] if row['extras'] is not None else row['col_description'],
                                              row['col_type'], row['col_sort_order']))

            yield TableMetadata('athena', last_row['cluster'],
                                last_row['schema'],
                                last_row['name'],
                                '',
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
