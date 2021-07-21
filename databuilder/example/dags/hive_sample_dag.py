# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import logging
import textwrap
from datetime import datetime, timedelta

from airflow import DAG  # noqa
from airflow import macros  # noqa
from airflow.operators.python_operator import PythonOperator  # noqa
from pyhocon import ConfigFactory

from databuilder.extractor.hive_table_metadata_extractor import HiveTableMetadataExtractor
from databuilder.extractor.sql_alchemy_extractor import SQLAlchemyExtractor
from databuilder.job.job import DefaultJob
from databuilder.loader.file_system_neo4j_csv_loader import FsNeo4jCSVLoader
from databuilder.models.table_metadata import DESCRIPTION_NODE_LABEL
from databuilder.publisher import neo4j_csv_publisher
from databuilder.publisher.neo4j_csv_publisher import Neo4jCsvPublisher
from databuilder.task.task import DefaultTask
from databuilder.transformer.base_transformer import NoopTransformer

dag_args = {
    'concurrency': 10,
    # One dagrun at a time
    'max_active_runs': 1,
    # 4AM, 4PM PST
    'schedule_interval': '0 11 * * *',
    'catchup': False
}

default_args = {
    'owner': 'amundsen',
    'start_date': datetime(2018, 6, 18),
    'depends_on_past': False,
    'email': [''],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 3,
    'priority_weight': 10,
    'retry_delay': timedelta(minutes=5),
    'execution_timeout': timedelta(minutes=120)
}

# NEO4J cluster endpoints
NEO4J_ENDPOINT = 'bolt://localhost:7687'

neo4j_endpoint = NEO4J_ENDPOINT

neo4j_user = 'neo4j'
neo4j_password = 'test'

# Todo: user provides a list of schema for indexing
SUPPORTED_HIVE_SCHEMAS = ['hive']
# Global used in all Hive metastore queries.
# String format - ('schema1', schema2', .... 'schemaN')
SUPPORTED_HIVE_SCHEMA_SQL_IN_CLAUSE = "('{schemas}')".format(schemas="', '".join(SUPPORTED_HIVE_SCHEMAS))

LOGGER = logging.getLogger(__name__)


# Todo: user needs to modify and provide a hivemetastore connection string
def connection_string():
    return 'hivemetastore.connection'


def create_table_wm_job(**kwargs):
    sql = textwrap.dedent("""
        SELECT From_unixtime(A0.create_time) as create_time,
               'hive'                        as `database`,
               C0.NAME                       as `schema`,
               B0.tbl_name as table_name,
               {func}(A0.part_name) as part_name,
               {watermark} as part_type
        FROM   PARTITIONS A0
               LEFT OUTER JOIN TBLS B0
                            ON A0.tbl_id = B0.tbl_id
               LEFT OUTER JOIN DBS C0
                            ON B0.db_id = C0.db_id
        WHERE  C0.NAME IN {schemas}
               AND B0.tbl_type IN ( 'EXTERNAL_TABLE', 'MANAGED_TABLE' )
               AND A0.PART_NAME NOT LIKE '%%__HIVE_DEFAULT_PARTITION__%%'
        GROUP  BY C0.NAME, B0.tbl_name
        ORDER by create_time desc
    """).format(func=kwargs['templates_dict'].get('agg_func'),
                watermark=kwargs['templates_dict'].get('watermark_type'),
                schemas=SUPPORTED_HIVE_SCHEMA_SQL_IN_CLAUSE)

    LOGGER.info('SQL query: %s', sql)
    tmp_folder = '/var/tmp/amundsen/table_{hwm}'.format(hwm=kwargs['templates_dict'].get('watermark_type').strip("\""))
    node_files_folder = f'{tmp_folder}/nodes'
    relationship_files_folder = f'{tmp_folder}/relationships'

    hwm_extractor = SQLAlchemyExtractor()
    csv_loader = FsNeo4jCSVLoader()

    task = DefaultTask(extractor=hwm_extractor,
                       loader=csv_loader,
                       transformer=NoopTransformer())

    job_config = ConfigFactory.from_dict({
        f'extractor.sqlalchemy.{SQLAlchemyExtractor.CONN_STRING}': connection_string(),
        f'extractor.sqlalchemy.{SQLAlchemyExtractor.EXTRACT_SQL}': sql,
        'extractor.sqlalchemy.model_class': 'databuilder.models.watermark.Watermark',
        f'loader.filesystem_csv_neo4j.{FsNeo4jCSVLoader.NODE_DIR_PATH}': node_files_folder,
        f'loader.filesystem_csv_neo4j.{FsNeo4jCSVLoader.RELATION_DIR_PATH}': relationship_files_folder,
        f'publisher.neo4j.{neo4j_csv_publisher.NODE_FILES_DIR}': node_files_folder,
        f'publisher.neo4j.{neo4j_csv_publisher.RELATION_FILES_DIR}': relationship_files_folder,
        f'publisher.neo4j.{neo4j_csv_publisher.NEO4J_END_POINT_KEY}': neo4j_endpoint,
        f'publisher.neo4j.{neo4j_csv_publisher.NEO4J_USER}': neo4j_user,
        f'publisher.neo4j.{neo4j_csv_publisher.NEO4J_PASSWORD}': neo4j_password,
    })
    job = DefaultJob(conf=job_config,
                     task=task,
                     publisher=Neo4jCsvPublisher())
    job.launch()


def create_table_metadata_databuilder_job():
    """
    Launches data builder job that extracts table and column metadata from MySQL Hive metastore database,
    and publishes to Neo4j.
    @param kwargs:
    @return:
    """

    # Adding to where clause to scope schema, filter out temp tables which start with numbers and views
    where_clause_suffix = textwrap.dedent("""
        WHERE d.NAME IN {schemas}
        AND t.TBL_NAME NOT REGEXP '^[0-9]+'
        AND t.TBL_TYPE IN ( 'EXTERNAL_TABLE', 'MANAGED_TABLE' )
    """).format(schemas=SUPPORTED_HIVE_SCHEMA_SQL_IN_CLAUSE)

    tmp_folder = '/var/tmp/amundsen/table_metadata'
    node_files_folder = f'{tmp_folder}/nodes/'
    relationship_files_folder = f'{tmp_folder}/relationships/'

    job_config = ConfigFactory.from_dict({
        f'extractor.hive_table_metadata.{HiveTableMetadataExtractor.WHERE_CLAUSE_SUFFIX_KEY}': where_clause_suffix,
        f'extractor.hive_table_metadata.extractor.sqlalchemy.{SQLAlchemyExtractor.CONN_STRING}': connection_string(),
        f'loader.filesystem_csv_neo4j.{FsNeo4jCSVLoader.NODE_DIR_PATH}': node_files_folder,
        f'loader.filesystem_csv_neo4j.{FsNeo4jCSVLoader.RELATION_DIR_PATH}': relationship_files_folder,
        f'publisher.neo4j.{neo4j_csv_publisher.NODE_FILES_DIR}': node_files_folder,
        f'publisher.neo4j.{neo4j_csv_publisher.RELATION_FILES_DIR}': relationship_files_folder,
        f'publisher.neo4j.{neo4j_csv_publisher.NEO4J_END_POINT_KEY}': neo4j_endpoint,
        f'publisher.neo4j.{neo4j_csv_publisher.NEO4J_USER}': neo4j_user,
        f'publisher.neo4j.{neo4j_csv_publisher.NEO4J_PASSWORD}': neo4j_password,
        f'publisher.neo4j.{neo4j_csv_publisher.NEO4J_CREATE_ONLY_NODES}': [DESCRIPTION_NODE_LABEL],
        'publisher.neo4j.job_publish_tag': 'some_unique_tag'  # TO-DO unique tag must be added
    })

    job = DefaultJob(conf=job_config,
                     task=DefaultTask(extractor=HiveTableMetadataExtractor(), loader=FsNeo4jCSVLoader()),
                     publisher=Neo4jCsvPublisher())
    job.launch()


with DAG('amundsen_databuilder', default_args=default_args, **dag_args) as dag:
    amundsen_databuilder_table_metadata_job = PythonOperator(
        task_id='amundsen_databuilder_table_metadata_job',
        python_callable=create_table_metadata_databuilder_job
    )

    # calculate hive high watermark
    amundsen_hwm_job = PythonOperator(
        task_id='amundsen_hwm_job',
        python_callable=create_table_wm_job,
        provide_context=True,
        templates_dict={'agg_func': 'max',
                        'watermark_type': '"high_watermark"',
                        'part_regex': '{{ ds }}'}
    )

    # calculate hive low watermark
    amundsen_lwm_job = PythonOperator(
        task_id='amundsen_lwm_job',
        python_callable=create_table_wm_job,
        provide_context=True,
        templates_dict={'agg_func': 'min',
                        'watermark_type': '"low_watermark"',
                        'part_regex': '{{ ds }}'}
    )

    # Schedule high and low watermark task after metadata task
    amundsen_databuilder_table_metadata_job >> amundsen_hwm_job
    amundsen_databuilder_table_metadata_job >> amundsen_lwm_job
