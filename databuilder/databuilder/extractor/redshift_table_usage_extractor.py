# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0


from databuilder.extractor.base_postgres_column_usage_extractor import BasePostgresColUsageExtractor


class RedshiftTableUsagextractor(BasePostgresColUsageExtractor):
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
        select
            'redshift' as database,
            {cluster_source} as cluster,
            trim(sti.schema) as schema,
            trim(sti.table) as table_name,
            trim(pu.usename) as user_email,
             count(sq.query) as read_count
            from
            (select
                distinct userid, tbl , query
            from stl_scan) ss
        left join SVV_TABLE_INFO sti on sti.table_id = ss.tbl
        left join pg_user pu on pu.usesysid = ss.userid
        left join stl_query sq on ss.query = sq.query
        where sq.starttime >= '2021-01-01 00:00' and sq.endtime < '2023-11-02 00:00'
        and sti.table is not null
        group by user_email,schema,table_name;
        """.format(
            cluster_source=cluster_source
        )

    def get_scope(self) -> str:
        return 'extractor.redshift_metadata'