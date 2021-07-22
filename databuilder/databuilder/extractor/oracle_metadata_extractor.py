# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from typing import (  # noqa: F401
    Any, Dict, Iterator, Union,
)

from pyhocon import ConfigFactory, ConfigTree  # noqa: F401

from databuilder.extractor.base_oracle_metadata_extractor import BaseOracleMetadataExtractor


class OracleMetadataExtractor(BaseOracleMetadataExtractor):
    """
    Extracts Oracle table and column metadata from underlying meta store database using SQLAlchemyExtractor
    """

    def get_sql_statement(self, where_clause_suffix: str) -> str:
        cluster_source = f"'{self._cluster}'"

        return """
        SELECT 
            {cluster_source} as "cluster",
            lower(c.owner) as "schema",
            lower(c.table_name) as "name",
            tc.comments as "description",
            lower(c.column_name) as "col_name",
            lower(c.data_type) as "col_type",
            cc.comments as "col_description",
            lower(c.column_id) as "col_sort_order"
        FROM
            all_tab_columns c
        LEFT JOIN
            all_tab_comments tc ON c.owner=tc.owner AND c.table_name=tc.table_name
        LEFT JOIN
            all_col_comments cc ON c.owner=cc.owner AND c.table_name=cc.table_name AND c.column_name=cc.column_name
        {where_clause_suffix}
        ORDER BY "cluster", "schema", "name", "col_sort_order" ;
        """.format(
            cluster_source=cluster_source,
            where_clause_suffix=where_clause_suffix,
        )

    def get_scope(self) -> str:
        return 'extractor.oracle_metadata'
