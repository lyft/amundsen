# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

"""
This is a example script demonstrating how to load data into Neptune and
Elasticsearch without using an Airflow DAG. This is pretty much a exact copy of the sample_data_loader.py except for
neptune use.

It contains several jobs:
- `run_csv_job`: runs a job that extracts table data from a CSV, loads (writes)
  this into a different local directory as a csv, then publishes this data to
  neptune.
- `run_table_column_job`: does the same thing as `run_csv_job`, but with a csv
  containing column data.
- `create_last_updated_job`: creates a job that gets the current time, dumps it
  into a predefined model schema, and publishes this to neptune.
- `create_es_publisher_sample_job`: creates a job that extracts data from neptune
  and publishes it into elasticsearch.

For other available extractors, please take a look at
https://github.com/amundsen-io/amundsendatabuilder#list-of-extractors
"""

import logging
import os
import uuid

import boto3
from amundsen_common.models.index_map import DASHBOARD_ELASTICSEARCH_INDEX_MAPPING, USER_INDEX_MAP
from elasticsearch import Elasticsearch
from pyhocon import ConfigFactory
from sqlalchemy.ext.declarative import declarative_base

from databuilder.clients.neptune_client import NeptuneSessionClient
from databuilder.extractor.csv_extractor import CsvExtractor, CsvTableColumnExtractor
from databuilder.extractor.es_last_updated_extractor import EsLastUpdatedExtractor
from databuilder.extractor.neptune_search_data_extractor import NeptuneSearchDataExtractor
from databuilder.job.job import DefaultJob
from databuilder.loader.file_system_elasticsearch_json_loader import FSElasticsearchJSONLoader
from databuilder.loader.file_system_neptune_csv_loader import FSNeptuneCSVLoader
from databuilder.publisher.elasticsearch_publisher import ElasticsearchPublisher
from databuilder.publisher.neptune_csv_publisher import NeptuneCSVPublisher
from databuilder.task.task import DefaultTask
from databuilder.transformer.base_transformer import ChainedTransformer, NoopTransformer
from databuilder.transformer.dict_to_model import MODEL_CLASS, DictToModel
from databuilder.transformer.generic_transformer import (
    CALLBACK_FUNCTION, FIELD_NAME, GenericTransformer,
)

es_host = os.getenv('CREDENTIALS_ELASTICSEARCH_PROXY_HOST', 'localhost')
neptune_host = os.getenv('CREDENTIALS_NEPTUNE_HOST', 'localhost')

es_port = os.getenv('CREDENTIALS_ELASTICSEARCH_PROXY_PORT', 9200)
neptune_port = os.getenv('CREDENTIALS_NEPTUNE_PORT', 7687)

neptune_iam_role_name = os.getenv('NEPTUNE_IAM_ROLE')

S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')
assert S3_BUCKET_NAME, "A S3 bucket is needed to load the data from"
S3_DATA_PATH = os.getenv("S3_DATA_PATH", "amundsen_data")
AWS_REGION = os.environ.get("AWS_REGION", 'us-east-1')

es = Elasticsearch(
    '{}:{}'.format(es_host, es_port)
)

Base = declarative_base()

NEPTUNE_ENDPOINT = '{}:{}'.format(neptune_host, neptune_port)

LOGGER = logging.getLogger(__name__)

session = boto3.Session()
aws_creds = session.get_credentials()
aws_access_key = aws_creds.access_key
aws_access_secret = aws_creds.secret_key
aws_token = aws_creds.token


def run_csv_job(file_loc, job_name, model):
    tmp_folder = '/var/tmp/amundsen/{job_name}'.format(job_name=job_name)
    node_files_folder = '{tmp_folder}/nodes'.format(tmp_folder=tmp_folder)
    relationship_files_folder = '{tmp_folder}/relationships'.format(tmp_folder=tmp_folder)

    csv_extractor = CsvExtractor()
    loader = FSNeptuneCSVLoader()
    publisher = NeptuneCSVPublisher()

    task = DefaultTask(
        extractor=csv_extractor,
        loader=loader,
        transformer=NoopTransformer()
    )

    job_config = ConfigFactory.from_dict({
        'extractor.csv.file_location': file_loc,
        'extractor.csv.model_class': model,
        loader.get_scope(): {
            FSNeptuneCSVLoader.NODE_DIR_PATH: node_files_folder,
            FSNeptuneCSVLoader.RELATION_DIR_PATH: relationship_files_folder,
            FSNeptuneCSVLoader.SHOULD_DELETE_CREATED_DIR: True,
            FSNeptuneCSVLoader.JOB_PUBLISHER_TAG: 'unique_tag'
        },
        publisher.get_scope(): {
            NeptuneCSVPublisher.NODE_FILES_DIR: node_files_folder,
            NeptuneCSVPublisher.RELATION_FILES_DIR: relationship_files_folder,
            NeptuneCSVPublisher.AWS_S3_BUCKET_NAME: S3_BUCKET_NAME,
            NeptuneCSVPublisher.AWS_BASE_S3_DATA_PATH: S3_DATA_PATH,
            NeptuneCSVPublisher.NEPTUNE_HOST: NEPTUNE_ENDPOINT,
            NeptuneCSVPublisher.AWS_IAM_ROLE_NAME: neptune_iam_role_name,
            NeptuneCSVPublisher.AWS_REGION: AWS_REGION,
            NeptuneCSVPublisher.AWS_ACCESS_KEY: aws_access_key,
            NeptuneCSVPublisher.AWS_SECRET_ACCESS_KEY: aws_access_secret,
            NeptuneCSVPublisher.AWS_SESSION_TOKEN: aws_token
        },
    })

    DefaultJob(
        conf=job_config,
        task=task,
        publisher=publisher
    ).launch()


def run_table_column_job(table_path, column_path):
    tmp_folder = '/var/tmp/amundsen/table_column'
    node_files_folder = '{tmp_folder}/nodes'.format(tmp_folder=tmp_folder)
    relationship_files_folder = '{tmp_folder}/relationships'.format(tmp_folder=tmp_folder)
    extractor = CsvTableColumnExtractor()
    csv_loader = FSNeptuneCSVLoader()
    publisher = NeptuneCSVPublisher()
    task = DefaultTask(
        extractor,
        loader=csv_loader,
        transformer=NoopTransformer()
    )
    job_config = ConfigFactory.from_dict({
        'extractor.csvtablecolumn.table_file_location': table_path,
        'extractor.csvtablecolumn.column_file_location': column_path,
        csv_loader.get_scope(): {
            FSNeptuneCSVLoader.NODE_DIR_PATH: node_files_folder,
            FSNeptuneCSVLoader.RELATION_DIR_PATH: relationship_files_folder,
            FSNeptuneCSVLoader.SHOULD_DELETE_CREATED_DIR: True,
            FSNeptuneCSVLoader.JOB_PUBLISHER_TAG: 'unique_tag'
        },
        publisher.get_scope(): {
            NeptuneCSVPublisher.NODE_FILES_DIR: node_files_folder,
            NeptuneCSVPublisher.RELATION_FILES_DIR: relationship_files_folder,
            NeptuneCSVPublisher.AWS_S3_BUCKET_NAME: S3_BUCKET_NAME,
            NeptuneCSVPublisher.AWS_BASE_S3_DATA_PATH: S3_DATA_PATH,
            NeptuneCSVPublisher.NEPTUNE_HOST: NEPTUNE_ENDPOINT,
            NeptuneCSVPublisher.AWS_IAM_ROLE_NAME: neptune_iam_role_name,
            NeptuneCSVPublisher.AWS_REGION: AWS_REGION,
            NeptuneCSVPublisher.AWS_ACCESS_KEY: aws_access_key,
            NeptuneCSVPublisher.AWS_SECRET_ACCESS_KEY: aws_access_secret,
            NeptuneCSVPublisher.AWS_SESSION_TOKEN: aws_token
        }
    })
    job = DefaultJob(
        conf=job_config,
        task=task,
        publisher=publisher
    )
    job.launch()


def create_last_updated_job():
    # loader saves data to these folders and publisher reads it from here
    tmp_folder = '/var/tmp/amundsen/last_updated_data'
    node_files_folder = '{tmp_folder}/nodes'.format(tmp_folder=tmp_folder)
    relationship_files_folder = '{tmp_folder}/relationships'.format(tmp_folder=tmp_folder)

    loader = FSNeptuneCSVLoader()
    task = DefaultTask(
        extractor=EsLastUpdatedExtractor(),
        loader=loader
    )

    publisher = NeptuneCSVPublisher()

    job_config = ConfigFactory.from_dict({
        'extractor.es_last_updated.model_class': 'databuilder.models.es_last_updated.ESLastUpdated',
        loader.get_scope(): {
            FSNeptuneCSVLoader.NODE_DIR_PATH: node_files_folder,
            FSNeptuneCSVLoader.RELATION_DIR_PATH: relationship_files_folder,
            FSNeptuneCSVLoader.SHOULD_DELETE_CREATED_DIR: True,
            FSNeptuneCSVLoader.JOB_PUBLISHER_TAG: 'unique_tag'
        },
        publisher.get_scope(): {
            NeptuneCSVPublisher.NODE_FILES_DIR: node_files_folder,
            NeptuneCSVPublisher.RELATION_FILES_DIR: relationship_files_folder,
            NeptuneCSVPublisher.AWS_S3_BUCKET_NAME: S3_BUCKET_NAME,
            NeptuneCSVPublisher.AWS_BASE_S3_DATA_PATH: S3_DATA_PATH,
            NeptuneCSVPublisher.NEPTUNE_HOST: NEPTUNE_ENDPOINT,
            NeptuneCSVPublisher.AWS_IAM_ROLE_NAME: neptune_iam_role_name,
            NeptuneCSVPublisher.AWS_REGION: AWS_REGION,
            NeptuneCSVPublisher.AWS_ACCESS_KEY: aws_access_key,
            NeptuneCSVPublisher.AWS_SECRET_ACCESS_KEY: aws_access_secret,
            NeptuneCSVPublisher.AWS_SESSION_TOKEN: aws_token,
            'job_publish_tag': 'unique_lastupdated_tag'
        }
    })

    return DefaultJob(
        conf=job_config,
        task=task,
        publisher=publisher
    )


def _str_to_list(str_val):
    return str_val.split(',')


def create_dashboard_tables_job():
    # loader saves data to these folders and publisher reads it from here
    tmp_folder = '/var/tmp/amundsen/dashboard_table'
    node_files_folder = '{tmp_folder}/nodes'.format(tmp_folder=tmp_folder)
    relationship_files_folder = '{tmp_folder}/relationships'.format(tmp_folder=tmp_folder)

    csv_extractor = CsvExtractor()
    loader = FSNeptuneCSVLoader()
    publisher = NeptuneCSVPublisher()

    generic_transformer = GenericTransformer()
    dict_to_model_transformer = DictToModel()
    transformer = ChainedTransformer(
        transformers=[generic_transformer, dict_to_model_transformer],
        is_init_transformers=True
    )

    task = DefaultTask(
        extractor=csv_extractor,
        loader=loader,
        transformer=transformer
    )

    job_config = ConfigFactory.from_dict({
        csv_extractor.get_scope(): {
            CsvExtractor.FILE_LOCATION: 'example/sample_data/sample_dashboard_table.csv'
        },
        transformer.get_scope(): {
            generic_transformer.get_scope(): {
                FIELD_NAME: 'table_ids',
                CALLBACK_FUNCTION: _str_to_list
            },
            dict_to_model_transformer.get_scope(): {
                MODEL_CLASS: 'databuilder.models.dashboard.dashboard_table.DashboardTable',
            }
        },
        loader.get_scope(): {
            FSNeptuneCSVLoader.NODE_DIR_PATH: node_files_folder,
            FSNeptuneCSVLoader.RELATION_DIR_PATH: relationship_files_folder,
            FSNeptuneCSVLoader.SHOULD_DELETE_CREATED_DIR: True,
            FSNeptuneCSVLoader.JOB_PUBLISHER_TAG: 'unique_tag'
        },
        publisher.get_scope(): {
            NeptuneCSVPublisher.NODE_FILES_DIR: node_files_folder,
            NeptuneCSVPublisher.RELATION_FILES_DIR: relationship_files_folder,
            NeptuneCSVPublisher.AWS_S3_BUCKET_NAME: S3_BUCKET_NAME,
            NeptuneCSVPublisher.AWS_BASE_S3_DATA_PATH: S3_DATA_PATH,
            NeptuneCSVPublisher.NEPTUNE_HOST: NEPTUNE_ENDPOINT,
            NeptuneCSVPublisher.AWS_IAM_ROLE_NAME: neptune_iam_role_name,
            NeptuneCSVPublisher.AWS_REGION: AWS_REGION,
            NeptuneCSVPublisher.AWS_ACCESS_KEY: aws_access_key,
            NeptuneCSVPublisher.AWS_SECRET_ACCESS_KEY: aws_access_secret,
            NeptuneCSVPublisher.AWS_SESSION_TOKEN: aws_token
        }
    })

    return DefaultJob(
        conf=job_config,
        task=task,
        publisher=publisher
    )


def create_es_publisher_sample_job(elasticsearch_index_alias='table_search_index',
                                   elasticsearch_doc_type_key='table',
                                   model_name='databuilder.models.table_elasticsearch_document.TableESDocument',
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
    loader = FSElasticsearchJSONLoader()
    extractor = NeptuneSearchDataExtractor()

    task = DefaultTask(
        loader=loader,
        extractor=extractor,
        transformer=NoopTransformer()
    )

    # elastic search client instance
    elasticsearch_client = es
    # unique name of new index in Elasticsearch
    elasticsearch_new_index_key = '{}_'.format(elasticsearch_doc_type_key) + str(uuid.uuid4())
    publisher = ElasticsearchPublisher()

    job_config = ConfigFactory.from_dict({
        extractor.get_scope(): {
            NeptuneSearchDataExtractor.ENTITY_TYPE_CONFIG_KEY: entity_type,
            NeptuneSearchDataExtractor.MODEL_CLASS_CONFIG_KEY: model_name,
            'neptune.client': {
                NeptuneSessionClient.NEPTUNE_HOST_NAME: NEPTUNE_ENDPOINT,
                NeptuneSessionClient.AWS_REGION: AWS_REGION,
                NeptuneSessionClient.AWS_ACCESS_KEY: aws_access_key,
                NeptuneSessionClient.AWS_SECRET_ACCESS_KEY: aws_access_secret,
                NeptuneSessionClient.AWS_SESSION_TOKEN: aws_token
            }
        },
        'loader.filesystem.elasticsearch.file_path': extracted_search_data_path,
        'loader.filesystem.elasticsearch.mode': 'w',
        publisher.get_scope(): {
            'file_path': extracted_search_data_path,
            'mode': 'r',
            'client': elasticsearch_client,
            'new_index': elasticsearch_new_index_key,
            'doc_type': elasticsearch_doc_type_key,
            'alias': elasticsearch_index_alias
        }
    })

    # only optionally add these keys, so need to dynamically `put` them
    if elasticsearch_mapping:
        job_config.put('publisher.elasticsearch.{}'.format(ElasticsearchPublisher.ELASTICSEARCH_MAPPING_CONFIG_KEY),
                       elasticsearch_mapping)

    job = DefaultJob(
        conf=job_config,
        task=task,
        publisher=ElasticsearchPublisher()
    )
    return job


if __name__ == "__main__":
    # Uncomment next line to get INFO level logging
    logging.basicConfig(level=logging.INFO)

    run_table_column_job('example/sample_data/sample_table.csv', 'example/sample_data/sample_col.csv')
    run_csv_job('example/sample_data/sample_table_column_stats.csv', 'test_table_column_stats',
                'databuilder.models.table_stats.TableColumnStats')
    run_csv_job('example/sample_data/sample_table_programmatic_source.csv', 'test_programmatic_source',
                'databuilder.models.table_metadata.TableMetadata')
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
    run_csv_job('example/sample_data/sample_table_last_updated.csv', 'test_table_last_updated_metadata',
                'databuilder.models.table_last_updated.TableLastUpdated')
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

    create_last_updated_job().launch()

    job_es_table = create_es_publisher_sample_job(
        elasticsearch_index_alias='table_search_index',
        elasticsearch_doc_type_key='table',
        entity_type='table',
        model_name='databuilder.models.table_elasticsearch_document.TableESDocument')
    job_es_table.launch()

    job_es_user = create_es_publisher_sample_job(
        elasticsearch_index_alias='user_search_index',
        elasticsearch_doc_type_key='user',
        model_name='databuilder.models.user_elasticsearch_document.UserESDocument',
        entity_type='user',
        elasticsearch_mapping=USER_INDEX_MAP
    )
    job_es_user.launch()

    job_es_dashboard = create_es_publisher_sample_job(
        elasticsearch_index_alias='dashboard_search_index',
        elasticsearch_doc_type_key='dashboard',
        model_name='databuilder.models.dashboard_elasticsearch_document.DashboardESDocument',
        entity_type='dashboard',
        elasticsearch_mapping=DASHBOARD_ELASTICSEARCH_INDEX_MAPPING
    )
    job_es_dashboard.launch()
