# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from typing import (  # noqa: F401
    Any, Dict, Iterator, Union,
)

from pyhocon import ConfigFactory, ConfigTree  # noqa: F401

from databuilder.extractor.base_postgres_metadata_extractor import BasePostgresMetadataExtractor


class RedshiftMetadataExtractor(BasePostgresMetadataExtractor):
    """
    Extracts Redshift table and column metadata from underlying meta store database using SQLAlchemyExtractor

    This differs from the PostgresMetadataExtractor because in order to support Redshift's late binding views,
    we need to join the INFORMATION_SCHEMA data against the function PG_GET_LATE_BINDING_VIEW_COLS().
    """

    def get_sql_statement(self, use_catalog_as_cluster_name: bool, where_clause_suffix: str) -> str:
        if use_catalog_as_cluster_name:
            cluster_source = "CURRENT_DATABASE()"
        else:
            cluster_source = f"'{self._cluster}'"

        return """
        SELECT
            *
        FROM (
            SELECT
              {cluster_source} as cluster,
              c.table_schema as schema,
              c.table_name as name,
              pgtd.description as description,
              c.column_name as col_name,
              c.data_type as col_type,
              pgcd.description as col_description,
              ordinal_position as col_sort_order
            FROM INFORMATION_SCHEMA.COLUMNS c
            INNER JOIN
              pg_catalog.pg_statio_all_tables as st on c.table_schema=st.schemaname and c.table_name=st.relname
            LEFT JOIN
              pg_catalog.pg_description pgcd on pgcd.objoid=st.relid and pgcd.objsubid=c.ordinal_position
            LEFT JOIN
              pg_catalog.pg_description pgtd on pgtd.objoid=st.relid and pgtd.objsubid=0

            UNION

            SELECT
              {cluster_source} as cluster,
              view_schema as schema,
              view_name as name,
              NULL as description,
              column_name as col_name,
              data_type as col_type,
              NULL as col_description,
              ordinal_position as col_sort_order
            FROM
                PG_GET_LATE_BINDING_VIEW_COLS()
                    COLS(view_schema NAME, view_name NAME, column_name NAME, data_type VARCHAR, ordinal_position INT)

            UNION

            SELECT
              {cluster_source} AS cluster,
              schemaname AS schema,
              tablename AS name,
              NULL AS description,
              columnname AS col_name,
              external_type AS col_type,
              NULL AS col_description,
              columnnum AS col_sort_order
            FROM svv_external_columns
        )

        {where_clause_suffix}
        ORDER by cluster, schema, name, col_sort_order ;
        """.format(
            cluster_source=cluster_source,
            where_clause_suffix=where_clause_suffix,
        )

    def get_scope(self) -> str:
        return 'extractor.redshift_metadata'
