# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

"""
This is a example script for extracting Delta Lake Metadata Results
"""

from pyhocon import ConfigFactory
from pyspark.sql import SparkSession

from databuilder.extractor.delta_lake_metadata_extractor import DeltaLakeMetadataExtractor
from databuilder.job.job import DefaultJob
from databuilder.loader.file_system_neo4j_csv_loader import FsNeo4jCSVLoader
from databuilder.models.table_metadata import DESCRIPTION_NODE_LABEL
from databuilder.publisher import neo4j_csv_publisher
from databuilder.publisher.neo4j_csv_publisher import Neo4jCsvPublisher
from databuilder.task.task import DefaultTask

# NEO4J cluster endpoints
NEO4J_ENDPOINT = 'bolt://localhost:7687/'

neo4j_endpoint = NEO4J_ENDPOINT

neo4j_user = 'neo4j'
neo4j_password = 'test'
cluster_key = 'my_delta_environment'
database = 'delta'
# Or set to empty to do all
schema_list = ['schema1', 'schema2']
# Or set to empty list if you don't have any schemas that you don't want to process
exclude_list = ['bad_schema']


def create_delta_lake_job_config():
    tmp_folder = '/var/tmp/amundsen/table_metadata'
    node_files_folder = f'{tmp_folder}/nodes/'
    relationship_files_folder = f'{tmp_folder}/relationships/'

    job_config = ConfigFactory.from_dict({
        f'extractor.delta_lake_table_metadata.{DeltaLakeMetadataExtractor.CLUSTER_KEY}': cluster_key,
        f'extractor.delta_lake_table_metadata.{DeltaLakeMetadataExtractor.DATABASE_KEY}': database,
        f'extractor.delta_lake_table_metadata.{DeltaLakeMetadataExtractor.SCHEMA_LIST_KEY}': schema_list,
        f'extractor.delta_lake_table_metadata.{DeltaLakeMetadataExtractor.EXCLUDE_LIST_SCHEMAS_KEY}': exclude_list,
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
    return job_config


if __name__ == "__main__":
    # This assumes you are running on a spark cluster (for example databricks cluster)
    # that is configured with a hive metastore that
    # has pointers to all of your delta tables
    # Because of this, this code CANNOT run as a normal python operator on airflow.
    spark = SparkSession.builder.appName("Amundsen Delta Lake Metadata Extraction").getOrCreate()
    job_config = create_delta_lake_job_config()
    dExtractor = DeltaLakeMetadataExtractor()
    dExtractor.set_spark(spark)
    job = DefaultJob(conf=job_config,
                     task=DefaultTask(extractor=dExtractor, loader=FsNeo4jCSVLoader()),
                     publisher=Neo4jCsvPublisher())
    job.launch()
