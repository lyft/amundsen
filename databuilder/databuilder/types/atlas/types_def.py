import pkg_resources


def get_schema(schema: str) -> str:
    return pkg_resources.resource_string(__name__, schema).decode('utf-8')


application_schema = get_schema("schema/07_application_schema.json")
cluster_schema = get_schema("schema/00_cluster_schema.json")
schema_schema = get_schema("schema/01_schema_schema.json")
schema_cluster_relation = get_schema("schema/01_schema_cluster_relation.json")
database_schema = get_schema("schema/01_database_schema.json")
database_cluster_relation = get_schema("schema/01_database_cluster_relation.json")
table_schema = get_schema("schema/01_2_table_schema.json")
table_schema_relation = get_schema("schema/01_table_schema_relation.json")
source_schema = get_schema("schema/01_source_schema.json")
table_source_relation = get_schema("schema/01_table_source_relation.json")
bookmark_schema = get_schema("schema/01_3_bookmark.json")
report_schema = get_schema("schema/01_4_report.json")
column_schema = get_schema("schema/01_column_schema.json")
column_table_relation = get_schema("schema/01_column_table_relation.json")
lineage_schema = get_schema("schema/08_lineage_schema.json")
user_schema = get_schema("schema/02_user.json")
reader_schema = get_schema("schema/01_1_reader.json")
user_reader_relation = get_schema("schema/04_user_reader_relation.json")
reader_referenceable_relation = get_schema("schema/04_reader_referenceable_relation.json")
table_partition_schema = get_schema("schema/05_table_partition_schema.json")
hive_table_partition = get_schema("schema/05_1_hive_table_partition.json")
data_owner_schema = get_schema("schema/06_user_table_owner_relation.json")

# Dashboard definitions ------------------------------------------------------------------------------------------------

dashboard_group_schema = get_schema("schema/dashboard/01_group.json")
dashboard_schema = get_schema("schema/dashboard/02_dashboard.json")
dashboard_query_schema = get_schema("schema/dashboard/03_query.json")
dashboard_chart_schema = get_schema("schema/dashboard/04_chart.json")
dashboard_execution_schema = get_schema("schema/dashboard/05_execution.json")
dashboard_cluster_relation = get_schema("schema/dashboard/06_dashboard_cluster_relation.json")
