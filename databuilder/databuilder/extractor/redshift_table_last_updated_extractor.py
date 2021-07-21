# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0


from databuilder.extractor.base_postgres_last_updated_extractor import BaseRedshiftLastUpdatedExtractor


class RedshiftTableLastUpdatedExtractor(BaseRedshiftLastUpdatedExtractor):
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
           {cluster_source} as cluster,
           'redshift' as db,
           sti.schema as schema,
           sti.table as table_name,
           cast(date_part(epoch,  sq.endtime) as integer) as last_updated_time_epoch
            FROM
                (SELECT MAX(query) as query, tbl, MAX(i.endtime) as last_insert
                FROM stl_insert i
                GROUP BY tbl
                ORDER BY tbl) inserts
            JOIN stl_query sq ON sq.query = inserts.query
            JOIN svv_table_info sti ON sti.table_id = inserts.tbl
            ;
        """.format(
            cluster_source=cluster_source
        )

    def get_scope(self) -> str:
        return 'extractor.redshift_metadata'