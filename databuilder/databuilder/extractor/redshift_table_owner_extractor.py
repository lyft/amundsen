# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0


from databuilder.extractor.base_postgres_owner_extractor import BasePostgresOwnerExtractor


class RedshiftTableOwnerextractor(BasePostgresOwnerExtractor):
    """
    Extracts Redshift table usage stats from underlying meta store database using SQLAlchemyExtractor
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
        'redshift' as database
         ,n.nspname AS schema
         , c.relname AS table_name
         , pg_get_userbyid(c.relowner) AS owner
         ,{cluster_source} as cluster
         , CASE WHEN c.relkind = 'v' THEN 'view' ELSE 'table' END AS table_type
         , d.description AS table_description
         FROM pg_class As c
         LEFT JOIN pg_namespace n ON n.oid = c.relnamespace
         LEFT JOIN pg_tablespace t ON t.oid = c.reltablespace
         LEFT JOIN pg_description As d
              ON (d.objoid = c.oid AND d.objsubid = 0)
         WHERE c.relkind IN('r', 'v')
         and schema = 'public'
        ORDER BY n.nspname, c.relname ;
        """.format(
            cluster_source=cluster_source
        )

    def get_scope(self) -> str:
        return 'extractor.redshift_metadata'