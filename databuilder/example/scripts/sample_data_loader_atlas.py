# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

"""
This is a example script demonstrating how to load data into Atlas and
Elasticsearch without using an Airflow DAG.

It contains several jobs:
- `run_csv_job`: runs a job that extracts table data from a CSV, loads (writes)
  this into a different local directory as a csv, then publishes this data to
  Atlas.
- `run_table_column_job`: does the same thing as `run_csv_job`, but with a csv
  containing column data.
- `create_last_updated_job`: creates a job that gets the current time, dumps it
  into a predefined model schema, and publishes this to Atlas.
- `create_es_publisher_sample_job`: creates a job that extracts data from Atlas
  and publishes it into Elasticsearch.

For other available extractors, please take a look at
https://github.com/amundsen-io/amundsendatabuilder#list-of-extractors
"""

import logging
import os
import sys
import uuid

from apache_atlas.client.base_client import AtlasClient
from elasticsearch import Elasticsearch
from pyhocon import ConfigFactory
from sqlalchemy.ext.declarative import declarative_base

from databuilder.extractor.atlas_search_data_extractor import AtlasSearchDataExtractor
from databuilder.extractor.csv_extractor import (
    CsvColumnLineageExtractor, CsvExtractor, CsvTableBadgeExtractor, CsvTableColumnExtractor, CsvTableLineageExtractor,
)
from databuilder.job.job import DefaultJob
from databuilder.loader.file_system_atlas_csv_loader import FsAtlasCSVLoader
from databuilder.loader.file_system_elasticsearch_json_loader import FSElasticsearchJSONLoader
from databuilder.publisher.atlas_csv_publisher import AtlasCSVPublisher
from databuilder.publisher.elasticsearch_constants import (
    DASHBOARD_ELASTICSEARCH_INDEX_MAPPING, USER_ELASTICSEARCH_INDEX_MAPPING,
)
from databuilder.publisher.elasticsearch_publisher import ElasticsearchPublisher
from databuilder.task.task import DefaultTask
from databuilder.transformer.base_transformer import ChainedTransformer, NoopTransformer
from databuilder.transformer.dict_to_model import MODEL_CLASS, DictToModel
from databuilder.transformer.generic_transformer import (
    CALLBACK_FUNCTION, FIELD_NAME, GenericTransformer,
)

ATLAS_CREATE_BATCH_SIZE = 5
ATLAS_SEARCH_CHUNK_SIZE = 5
ATLAS_DETAILS_CHUNK_SIZE = 5
ATLAS_PROCESS_POOL_SIZE = 1

es_host = os.getenv('CREDENTIALS_ELASTICSEARCH_PROXY_HOST', 'localhost')
atlas_host = os.getenv('CREDENTIALS_ATLAS_PROXY_HOST', 'localhost')

es_port = os.getenv('CREDENTIALS_ELASTICSEARCH_PROXY_PORT', 9200)
atlas_port = os.getenv('CREDENTIALS_ATLAS_PROXY_PORT', 21000)

if len(sys.argv) > 1:
    es_host = sys.argv[1]
if len(sys.argv) > 2:
    atlas_host = sys.argv[2]

es = Elasticsearch([
    {'host': es_host, 'port': es_port},
])

Base = declarative_base()

atlas_endpoint = f'http://{atlas_host}:{atlas_port}'

atlas_user = 'admin'
atlas_password = 'admin'

LOGGER = logging.getLogger(__name__)


def run_csv_job(file_loc, job_name, model):
    tmp_folder = f'/var/tmp/amundsen/{job_name}'
    node_files_folder = f'{tmp_folder}/nodes'
    relationship_files_folder = f'{tmp_folder}/relationships'

    csv_extractor = CsvExtractor()
    csv_loader = FsAtlasCSVLoader()

    task = DefaultTask(extractor=csv_extractor,
                       loader=csv_loader,
                       transformer=NoopTransformer())

    job_config = ConfigFactory.from_dict({
        'extractor.csv.file_location': file_loc,
        'extractor.csv.model_class': model,
        f'loader.filesystem_csv_atlas.{FsAtlasCSVLoader.ENTITY_DIR_PATH}': node_files_folder,
        f'loader.filesystem_csv_atlas.{FsAtlasCSVLoader.RELATIONSHIP_DIR_PATH}': relationship_files_folder,
        f'loader.filesystem_csv_atlas.{FsAtlasCSVLoader.SHOULD_DELETE_CREATED_DIR}': True,
        f'publisher.atlas_csv_publisher.{AtlasCSVPublisher.ATLAS_CLIENT}': AtlasClient(atlas_endpoint,
                                                                                       (atlas_user, atlas_password)),
        f'publisher.atlas_csv_publisher.{AtlasCSVPublisher.ENTITY_DIR_PATH}': node_files_folder,
        f'publisher.atlas_csv_publisher.{AtlasCSVPublisher.RELATIONSHIP_DIR_PATH}': relationship_files_folder,
        f'publisher.atlas_csv_publisher.{AtlasCSVPublisher.ATLAS_ENTITY_CREATE_BATCH_SIZE}': ATLAS_CREATE_BATCH_SIZE,
    })

    DefaultJob(conf=job_config,
               task=task,
               publisher=AtlasCSVPublisher()).launch()


def run_table_badge_job(table_path, badge_path):
    tmp_folder = '/var/tmp/amundsen/table_badge'
    node_files_folder = f'{tmp_folder}/nodes'
    relationship_files_folder = f'{tmp_folder}/relationships'
    extractor = CsvTableBadgeExtractor()
    csv_loader = FsAtlasCSVLoader()
    task = DefaultTask(extractor=extractor,
                       loader=csv_loader,
                       transformer=NoopTransformer())
    job_config = ConfigFactory.from_dict({
        'extractor.csvtablebadge.table_file_location': table_path,
        'extractor.csvtablebadge.badge_file_location': badge_path,
        f'loader.filesystem_csv_atlas.{FsAtlasCSVLoader.ENTITY_DIR_PATH}': node_files_folder,
        f'loader.filesystem_csv_atlas.{FsAtlasCSVLoader.RELATIONSHIP_DIR_PATH}': relationship_files_folder,
        f'loader.filesystem_csv_atlas.{FsAtlasCSVLoader.SHOULD_DELETE_CREATED_DIR}': True,
        f'publisher.atlas_csv_publisher.{AtlasCSVPublisher.ATLAS_CLIENT}': AtlasClient(atlas_endpoint,
                                                                                       (atlas_user, atlas_password)),
        f'publisher.atlas_csv_publisher.{AtlasCSVPublisher.ENTITY_DIR_PATH}': node_files_folder,
        f'publisher.atlas_csv_publisher.{AtlasCSVPublisher.RELATIONSHIP_DIR_PATH}': relationship_files_folder,
        f'publisher.atlas_csv_publisher.{AtlasCSVPublisher.ATLAS_ENTITY_CREATE_BATCH_SIZE}': ATLAS_CREATE_BATCH_SIZE,
    })
    job = DefaultJob(conf=job_config,
                     task=task,
                     publisher=AtlasCSVPublisher())
    job.launch()


def run_table_column_job(table_path, column_path):
    tmp_folder = '/var/tmp/amundsen/table_column'
    node_files_folder = f'{tmp_folder}/nodes'
    relationship_files_folder = f'{tmp_folder}/relationships'
    extractor = CsvTableColumnExtractor()
    csv_loader = FsAtlasCSVLoader()
    task = DefaultTask(extractor,
                       loader=csv_loader,
                       transformer=NoopTransformer())
    job_config = ConfigFactory.from_dict({
        'extractor.csvtablecolumn.table_file_location': table_path,
        'extractor.csvtablecolumn.column_file_location': column_path,
        f'loader.filesystem_csv_atlas.{FsAtlasCSVLoader.ENTITY_DIR_PATH}': node_files_folder,
        f'loader.filesystem_csv_atlas.{FsAtlasCSVLoader.RELATIONSHIP_DIR_PATH}': relationship_files_folder,
        f'loader.filesystem_csv_atlas.{FsAtlasCSVLoader.SHOULD_DELETE_CREATED_DIR}': True,
        f'publisher.atlas_csv_publisher.{AtlasCSVPublisher.ATLAS_CLIENT}': AtlasClient(atlas_endpoint,
                                                                                       (atlas_user, atlas_password)),
        f'publisher.atlas_csv_publisher.{AtlasCSVPublisher.ENTITY_DIR_PATH}': node_files_folder,
        f'publisher.atlas_csv_publisher.{AtlasCSVPublisher.RELATIONSHIP_DIR_PATH}': relationship_files_folder,
        f'publisher.atlas_csv_publisher.{AtlasCSVPublisher.ATLAS_ENTITY_CREATE_BATCH_SIZE}': ATLAS_CREATE_BATCH_SIZE,
    })
    job = DefaultJob(conf=job_config,
                     task=task,
                     publisher=AtlasCSVPublisher())
    job.launch()


def run_table_lineage_job(table_lineage_path):
    tmp_folder = '/var/tmp/amundsen/table_column'
    node_files_folder = f'{tmp_folder}/nodes'
    relationship_files_folder = f'{tmp_folder}/relationships'
    extractor = CsvTableLineageExtractor()
    csv_loader = FsAtlasCSVLoader()
    task = DefaultTask(extractor,
                       loader=csv_loader,
                       transformer=NoopTransformer())
    job_config = ConfigFactory.from_dict({
        'extractor.csvtablelineage.table_lineage_file_location': table_lineage_path,
        f'loader.filesystem_csv_atlas.{FsAtlasCSVLoader.ENTITY_DIR_PATH}': node_files_folder,
        f'loader.filesystem_csv_atlas.{FsAtlasCSVLoader.RELATIONSHIP_DIR_PATH}': relationship_files_folder,
        f'loader.filesystem_csv_atlas.{FsAtlasCSVLoader.SHOULD_DELETE_CREATED_DIR}': True,
        f'publisher.atlas_csv_publisher.{AtlasCSVPublisher.ATLAS_CLIENT}': AtlasClient(atlas_endpoint,
                                                                                       (atlas_user, atlas_password)),
        f'publisher.atlas_csv_publisher.{AtlasCSVPublisher.ENTITY_DIR_PATH}': node_files_folder,
        f'publisher.atlas_csv_publisher.{AtlasCSVPublisher.RELATIONSHIP_DIR_PATH}': relationship_files_folder,
        f'publisher.atlas_csv_publisher.{AtlasCSVPublisher.ATLAS_ENTITY_CREATE_BATCH_SIZE}': ATLAS_CREATE_BATCH_SIZE,
    })
    job = DefaultJob(conf=job_config,
                     task=task,
                     publisher=AtlasCSVPublisher())
    job.launch()


def run_column_lineage_job(column_lineage_path):
    tmp_folder = '/var/tmp/amundsen/table_column'
    node_files_folder = f'{tmp_folder}/nodes'
    relationship_files_folder = f'{tmp_folder}/relationships'
    extractor = CsvColumnLineageExtractor()
    csv_loader = FsAtlasCSVLoader()
    task = DefaultTask(extractor,
                       loader=csv_loader,
                       transformer=NoopTransformer())
    job_config = ConfigFactory.from_dict({
        'extractor.csvcolumnlineage.column_lineage_file_location': column_lineage_path,
        f'loader.filesystem_csv_atlas.{FsAtlasCSVLoader.ENTITY_DIR_PATH}': node_files_folder,
        f'loader.filesystem_csv_atlas.{FsAtlasCSVLoader.RELATIONSHIP_DIR_PATH}': relationship_files_folder,
        f'loader.filesystem_csv_atlas.{FsAtlasCSVLoader.SHOULD_DELETE_CREATED_DIR}': True,
        f'publisher.atlas_csv_publisher.{AtlasCSVPublisher.ATLAS_CLIENT}': AtlasClient(atlas_endpoint,
                                                                                       (atlas_user, atlas_password)),
        f'publisher.atlas_csv_publisher.{AtlasCSVPublisher.ENTITY_DIR_PATH}': node_files_folder,
        f'publisher.atlas_csv_publisher.{AtlasCSVPublisher.RELATIONSHIP_DIR_PATH}': relationship_files_folder,
        f'publisher.atlas_csv_publisher.{AtlasCSVPublisher.ATLAS_ENTITY_CREATE_BATCH_SIZE}': ATLAS_CREATE_BATCH_SIZE,
    })
    job = DefaultJob(conf=job_config,
                     task=task,
                     publisher=AtlasCSVPublisher())
    job.launch()


def _str_to_list(str_val):
    return str_val.split(',')


def create_dashboard_tables_job():
    # loader saves data to these folders and publisher reads it from here
    tmp_folder = '/var/tmp/amundsen/dashboard_table'
    node_files_folder = f'{tmp_folder}/nodes'
    relationship_files_folder = f'{tmp_folder}/relationships'

    csv_extractor = CsvExtractor()
    csv_loader = FsAtlasCSVLoader()

    generic_transformer = GenericTransformer()
    dict_to_model_transformer = DictToModel()
    transformer = ChainedTransformer(transformers=[generic_transformer, dict_to_model_transformer],
                                     is_init_transformers=True)

    task = DefaultTask(extractor=csv_extractor,
                       loader=csv_loader,
                       transformer=transformer)
    publisher = AtlasCSVPublisher()

    job_config = ConfigFactory.from_dict({
        f'{csv_extractor.get_scope()}.file_location': 'example/sample_data/sample_dashboard_table.csv',
        f'{transformer.get_scope()}.{generic_transformer.get_scope()}.{FIELD_NAME}': 'table_ids',
        f'{transformer.get_scope()}.{generic_transformer.get_scope()}.{CALLBACK_FUNCTION}': _str_to_list,
        f'{transformer.get_scope()}.{dict_to_model_transformer.get_scope()}.{MODEL_CLASS}':
            'databuilder.models.dashboard.dashboard_table.DashboardTable',
        f'loader.filesystem_csv_atlas.{FsAtlasCSVLoader.ENTITY_DIR_PATH}': node_files_folder,
        f'loader.filesystem_csv_atlas.{FsAtlasCSVLoader.RELATIONSHIP_DIR_PATH}': relationship_files_folder,
        f'loader.filesystem_csv_atlas.{FsAtlasCSVLoader.SHOULD_DELETE_CREATED_DIR}': True,
        f'publisher.atlas_csv_publisher.{AtlasCSVPublisher.ATLAS_CLIENT}': AtlasClient(atlas_endpoint,
                                                                                       (atlas_user, atlas_password)),
        f'publisher.atlas_csv_publisher.{AtlasCSVPublisher.ENTITY_DIR_PATH}': node_files_folder,
        f'publisher.atlas_csv_publisher.{AtlasCSVPublisher.RELATIONSHIP_DIR_PATH}': relationship_files_folder,
        f'publisher.atlas_csv_publisher.{AtlasCSVPublisher.ATLAS_ENTITY_CREATE_BATCH_SIZE}': ATLAS_CREATE_BATCH_SIZE,
    })

    return DefaultJob(conf=job_config,
                      task=task,
                      publisher=publisher)


def create_es_publisher_sample_job(elasticsearch_index_alias='table_search_index',
                                   entity_type='table',
                                   elasticsearch_mapping=None):
    """
    :param elasticsearch_index_alias:  alias for Elasticsearch used in
                                       amundsensearchlibrary/search_service/config.py as an index
    :param elasticsearch_doc_type_key: name the ElasticSearch index is prepended with. Defaults to `table` resulting in
                                       `table_{uuid}`
    :param model_name:                 the Databuilder model class used in transporting between Extractor and Loader
    :param entity_type:                Entity type handed to the `Neo4jSearchDataExtractor` class, used to determine
                                       Cypher query to extract data from Neo4j. Defaults to `table`.
    :param elasticsearch_mapping:      Elasticsearch field mapping "DDL" handed to the `ElasticsearchPublisher` class,
                                       if None is given (default) it uses the `Table` query baked into the Publisher
    """
    # loader saves data to this location and publisher reads it from here
    extracted_search_data_path = '/var/tmp/amundsen/search_data.json'

    task = DefaultTask(loader=FSElasticsearchJSONLoader(),
                       extractor=AtlasSearchDataExtractor(),
                       transformer=NoopTransformer())

    # elastic search client instance
    elasticsearch_client = es
    # unique name of new index in Elasticsearch
    elasticsearch_new_index_key = f'{entity_type}_{uuid.uuid4()}'

    job_config = ConfigFactory.from_dict({
        'extractor.atlas_search_data.{}'.format(AtlasSearchDataExtractor.ATLAS_URL_CONFIG_KEY):
            atlas_host,
        'extractor.atlas_search_data.{}'.format(AtlasSearchDataExtractor.ATLAS_PORT_CONFIG_KEY):
            atlas_port,
        'extractor.atlas_search_data.{}'.format(AtlasSearchDataExtractor.ATLAS_PROTOCOL_CONFIG_KEY):
            'http',
        'extractor.atlas_search_data.{}'.format(AtlasSearchDataExtractor.ATLAS_VALIDATE_SSL_CONFIG_KEY):
            False,
        'extractor.atlas_search_data.{}'.format(AtlasSearchDataExtractor.ATLAS_USERNAME_CONFIG_KEY):
            atlas_user,
        'extractor.atlas_search_data.{}'.format(AtlasSearchDataExtractor.ATLAS_PASSWORD_CONFIG_KEY):
            atlas_password,
        'extractor.atlas_search_data.{}'.format(AtlasSearchDataExtractor.ATLAS_SEARCH_CHUNK_SIZE_KEY):
            ATLAS_SEARCH_CHUNK_SIZE,
        'extractor.atlas_search_data.{}'.format(AtlasSearchDataExtractor.ATLAS_DETAILS_CHUNK_SIZE_KEY):
            ATLAS_DETAILS_CHUNK_SIZE,
        'extractor.atlas_search_data.{}'.format(AtlasSearchDataExtractor.PROCESS_POOL_SIZE_KEY):
            ATLAS_PROCESS_POOL_SIZE,
        'extractor.atlas_search_data.{}'.format(AtlasSearchDataExtractor.ENTITY_TYPE_KEY):
            entity_type.title(),
        'loader.filesystem.elasticsearch.file_path': extracted_search_data_path,
        'loader.filesystem.elasticsearch.mode': 'w',
        'publisher.elasticsearch.file_path': extracted_search_data_path,
        'publisher.elasticsearch.mode': 'r',
        'publisher.elasticsearch.client': elasticsearch_client,
        'publisher.elasticsearch.new_index': elasticsearch_new_index_key,
        'publisher.elasticsearch.doc_type': '_doc',
        'publisher.elasticsearch.alias': elasticsearch_index_alias,
    })

    # only optionally add these keys, so need to dynamically `put` them
    if elasticsearch_mapping:
        job_config.put(f'publisher.elasticsearch.{ElasticsearchPublisher.ELASTICSEARCH_MAPPING_CONFIG_KEY}',
                       elasticsearch_mapping)

    job = DefaultJob(conf=job_config,
                     task=task,
                     publisher=ElasticsearchPublisher())
    return job


if __name__ == "__main__":
    # Uncomment next line to get INFO level logging
    # logging.basicConfig(level=logging.INFO)

    run_table_column_job('example/sample_data/sample_table.csv', 'example/sample_data/sample_col.csv')
    run_table_badge_job('example/sample_data/sample_table.csv', 'example/sample_data/sample_badges.csv')
    run_table_lineage_job('example/sample_data/sample_table_lineage.csv')
    run_column_lineage_job('example/sample_data/sample_column_lineage.csv')
    # run_csv_job('example/sample_data/sample_table_column_stats.csv', 'test_table_column_stats',
    #             'databuilder.models.table_stats.TableColumnStats')
    # run_csv_job('example/sample_data/sample_table_programmatic_source.csv', 'test_programmatic_source',
    #             'databuilder.models.table_metadata.TableMetadata')
    run_csv_job('example/sample_data/sample_watermark.csv', 'test_watermark_metadata',
                'databuilder.models.watermark.Watermark')
    run_csv_job('example/sample_data/sample_table_owner.csv', 'test_table_owner_metadata',
                'databuilder.models.table_owner.TableOwner')
    run_csv_job('example/sample_data/sample_column_usage.csv', 'test_usage_metadata',
                'databuilder.models.table_column_usage.ColumnReader')
    run_csv_job('example/sample_data/sample_user.csv', 'test_user_metadata',
                'databuilder.models.user.User')
    run_csv_job('example/sample_data/sample_application.csv', 'test_application_metadata',
                'databuilder.models.application.Application')
    run_csv_job('example/sample_data/sample_source.csv', 'test_source_metadata',
                'databuilder.models.table_source.TableSource')
    run_csv_job('example/sample_data/sample_tags.csv', 'test_tag_metadata',
                'databuilder.models.table_metadata.TagMetadata')
    run_csv_job('example/sample_data/sample_schema_description.csv', 'test_schema_description',
                'databuilder.models.schema.schema.SchemaModel')
    run_csv_job('example/sample_data/sample_dashboard_base.csv', 'test_dashboard_base',
                'databuilder.models.dashboard.dashboard_metadata.DashboardMetadata')
    run_csv_job('example/sample_data/sample_dashboard_usage.csv', 'test_dashboard_usage',
                'databuilder.models.dashboard.dashboard_usage.DashboardUsage')
    run_csv_job('example/sample_data/sample_dashboard_owner.csv', 'test_dashboard_owner',
                'databuilder.models.dashboard.dashboard_owner.DashboardOwner')
    run_csv_job('example/sample_data/sample_dashboard_query.csv', 'test_dashboard_query',
                'databuilder.models.dashboard.dashboard_query.DashboardQuery')
    run_csv_job('example/sample_data/sample_dashboard_last_execution.csv', 'test_dashboard_last_execution',
                'databuilder.models.dashboard.dashboard_execution.DashboardExecution')
    run_csv_job('example/sample_data/sample_dashboard_last_modified.csv', 'test_dashboard_last_modified',
                'databuilder.models.dashboard.dashboard_last_modified.DashboardLastModifiedTimestamp')

    create_dashboard_tables_job().launch()

    job_es_table = create_es_publisher_sample_job(
        elasticsearch_index_alias='table_search_index',
        entity_type='table')
    job_es_table.launch()

    job_es_user = create_es_publisher_sample_job(
        elasticsearch_index_alias='user_search_index',
        entity_type='user',
        elasticsearch_mapping=USER_ELASTICSEARCH_INDEX_MAPPING)
    job_es_user.launch()

    job_es_dashboard = create_es_publisher_sample_job(
        elasticsearch_index_alias='dashboard_search_index',
        entity_type='dashboard',
        elasticsearch_mapping=DASHBOARD_ELASTICSEARCH_INDEX_MAPPING)
    job_es_dashboard.launch()
