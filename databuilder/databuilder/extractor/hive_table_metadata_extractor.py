# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import logging
from collections import namedtuple
from itertools import groupby
from typing import (
    Any, Dict, Iterator, Union,
)

from pyhocon import ConfigFactory, ConfigTree
from sqlalchemy.engine.url import make_url

from databuilder import Scoped
from databuilder.extractor.base_extractor import Extractor
from databuilder.extractor.sql_alchemy_extractor import SQLAlchemyExtractor
from databuilder.extractor.table_metadata_constants import PARTITION_BADGE
from databuilder.models.table_metadata import ColumnMetadata, TableMetadata

TableKey = namedtuple('TableKey', ['schema', 'table_name'])

LOGGER = logging.getLogger(__name__)


class HiveTableMetadataExtractor(Extractor):
    """
    Extracts Hive table and column metadata from underlying meta store database using SQLAlchemyExtractor
    """
    EXTRACT_SQL = 'extract_sql'
    # SELECT statement from hive metastore database to extract table and column metadata
    # Below SELECT statement uses UNION to combining two queries together.
    # 1st query is retrieving partition columns
    # 2nd query is retrieving columns
    # Using UNION to combine above two statements and order by table & partition identifier.
    DEFAULT_SQL_STATEMENT = """
    SELECT source.* FROM
    (SELECT t.TBL_ID, d.NAME as `schema`, t.TBL_NAME name, t.TBL_TYPE, tp.PARAM_VALUE as description,
           p.PKEY_NAME as col_name, p.INTEGER_IDX as col_sort_order,
           p.PKEY_TYPE as col_type, p.PKEY_COMMENT as col_description, 1 as "is_partition_col",
           IF(t.TBL_TYPE = 'VIRTUAL_VIEW', 1, 0) "is_view"
    FROM TBLS t
    JOIN DBS d ON t.DB_ID = d.DB_ID
    JOIN PARTITION_KEYS p ON t.TBL_ID = p.TBL_ID
    LEFT JOIN TABLE_PARAMS tp ON (t.TBL_ID = tp.TBL_ID AND tp.PARAM_KEY='comment')
    {where_clause_suffix}
    UNION
    SELECT t.TBL_ID, d.NAME as `schema`, t.TBL_NAME name, t.TBL_TYPE, tp.PARAM_VALUE as description,
           c.COLUMN_NAME as col_name, c.INTEGER_IDX as col_sort_order,
           c.TYPE_NAME as col_type, c.COMMENT as col_description, 0 as "is_partition_col",
           IF(t.TBL_TYPE = 'VIRTUAL_VIEW', 1, 0) "is_view"
    FROM TBLS t
    JOIN DBS d ON t.DB_ID = d.DB_ID
    JOIN SDS s ON t.SD_ID = s.SD_ID
    JOIN COLUMNS_V2 c ON s.CD_ID = c.CD_ID
    LEFT JOIN TABLE_PARAMS tp ON (t.TBL_ID = tp.TBL_ID AND tp.PARAM_KEY='comment')
    {where_clause_suffix}
    ) source
    ORDER by tbl_id, is_partition_col desc;
    """

    DEFAULT_POSTGRES_SQL_STATEMENT = """
    SELECT source.* FROM
    (SELECT t."TBL_ID" as tbl_id, d."NAME" as "schema", t."TBL_NAME" as name, t."TBL_TYPE",
           tp."PARAM_VALUE" as description, p."PKEY_NAME" as col_name, p."INTEGER_IDX" as col_sort_order,
           p."PKEY_TYPE" as col_type, p."PKEY_COMMENT" as col_description, 1 as "is_partition_col",
           CASE WHEN t."TBL_TYPE" = 'VIRTUAL_VIEW' THEN 1
                ELSE 0 END as "is_view"
    FROM "TBLS" t
    JOIN "DBS" d ON t."DB_ID" = d."DB_ID"
    JOIN "PARTITION_KEYS" p ON t."TBL_ID" = p."TBL_ID"
    LEFT JOIN "TABLE_PARAMS" tp ON (t."TBL_ID" = tp."TBL_ID" AND tp."PARAM_KEY"='comment')
    {where_clause_suffix}
    UNION
    SELECT t."TBL_ID" as tbl_id, d."NAME" as "schema", t."TBL_NAME" as name, t."TBL_TYPE",
           tp."PARAM_VALUE" as description, c."COLUMN_NAME" as col_name, c."INTEGER_IDX" as col_sort_order,
           c."TYPE_NAME" as col_type, c."COMMENT" as col_description, 0 as "is_partition_col",
           CASE WHEN t."TBL_TYPE" = 'VIRTUAL_VIEW' THEN 1
                ELSE 0 END as "is_view"
    FROM "TBLS" t
    JOIN "DBS" d ON t."DB_ID" = d."DB_ID"
    JOIN "SDS" s ON t."SD_ID" = s."SD_ID"
    JOIN "COLUMNS_V2" c ON s."CD_ID" = c."CD_ID"
    LEFT JOIN "TABLE_PARAMS" tp ON (t."TBL_ID" = tp."TBL_ID" AND tp."PARAM_KEY"='comment')
    {where_clause_suffix}
    ) source
    ORDER by tbl_id, is_partition_col desc;
    """

    # CONFIG KEYS
    WHERE_CLAUSE_SUFFIX_KEY = 'where_clause_suffix'
    CLUSTER_KEY = 'cluster'

    DEFAULT_CONFIG = ConfigFactory.from_dict({WHERE_CLAUSE_SUFFIX_KEY: ' ',
                                              CLUSTER_KEY: 'gold'})

    def init(self, conf: ConfigTree) -> None:
        conf = conf.with_fallback(HiveTableMetadataExtractor.DEFAULT_CONFIG)
        self._cluster = conf.get_string(HiveTableMetadataExtractor.CLUSTER_KEY)

        self._alchemy_extractor = SQLAlchemyExtractor()

        sql_alch_conf = Scoped.get_scoped_conf(conf, self._alchemy_extractor.get_scope())
        default_sql = self._choose_default_sql_stm(sql_alch_conf).format(
            where_clause_suffix=conf.get_string(HiveTableMetadataExtractor.WHERE_CLAUSE_SUFFIX_KEY))

        self.sql_stmt = conf.get_string(HiveTableMetadataExtractor.EXTRACT_SQL, default=default_sql)

        LOGGER.info('SQL for hive metastore: %s', self.sql_stmt)

        sql_alch_conf = sql_alch_conf.with_fallback(ConfigFactory.from_dict(
            {SQLAlchemyExtractor.EXTRACT_SQL: self.sql_stmt}))
        self._alchemy_extractor.init(sql_alch_conf)
        self._extract_iter: Union[None, Iterator] = None

    def _choose_default_sql_stm(self, conf: ConfigTree) -> str:
        url = make_url(conf.get_string(SQLAlchemyExtractor.CONN_STRING))
        if url.drivername.lower() in ['postgresql', 'postgres']:
            return HiveTableMetadataExtractor.DEFAULT_POSTGRES_SQL_STATEMENT
        else:
            return HiveTableMetadataExtractor.DEFAULT_SQL_STATEMENT

    def extract(self) -> Union[TableMetadata, None]:
        if not self._extract_iter:
            self._extract_iter = self._get_extract_iter()
        try:
            return next(self._extract_iter)
        except StopIteration:
            return None

    def get_scope(self) -> str:
        return 'extractor.hive_table_metadata'

    def _get_extract_iter(self) -> Iterator[TableMetadata]:
        """
        Using itertools.groupby and raw level iterator, it groups to table and yields TableMetadata
        :return:
        """
        for key, group in groupby(self._get_raw_extract_iter(), self._get_table_key):
            columns = []

            for row in group:
                last_row = row
                column = None
                if row['is_partition_col'] == 1:
                    # create add a badge to indicate partition column
                    column = ColumnMetadata(row['col_name'], row['col_description'],
                                            row['col_type'], row['col_sort_order'], [PARTITION_BADGE])
                else:
                    column = ColumnMetadata(row['col_name'], row['col_description'],
                                            row['col_type'], row['col_sort_order'])
                columns.append(column)
            is_view = last_row['is_view'] == 1
            yield TableMetadata('hive', self._cluster,
                                last_row['schema'],
                                last_row['name'],
                                last_row['description'],
                                columns,
                                is_view=is_view)

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
