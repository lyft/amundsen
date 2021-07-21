# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

"""
TODO: it needs db init(in dev) first in metadata service
This is a example script demonstrating how to load data into MySQL and
Elasticsearch without using an Airflow DAG.

It contains several jobs:
- `run_csv_job`: runs a job that extracts table data from a CSV, loads (writes)
  this into a different local directory as a csv, then publishes this data to
  mysql.
- `run_table_column_job`: does the same thing as `run_csv_job`, but with a csv
  containing column data.
- `create_last_updated_job`: creates a job that gets the current time, dumps it
  into a predefined model schema, and publishes this to mysql.
- `create_es_publisher_sample_job`: creates a job that extracts data from mysql
  and publishes it into elasticsearch.

For other available extractors, please take a look at
https://github.com/amundsen-io/amundsendatabuilder#list-of-extractors
"""

import logging
import os
import sys
import uuid

from amundsen_common.models.index_map import DASHBOARD_ELASTICSEARCH_INDEX_MAPPING, USER_INDEX_MAP
from elasticsearch import Elasticsearch
from pyhocon import ConfigFactory

from databuilder.extractor.csv_extractor import CsvExtractor, CsvTableColumnExtractor
from databuilder.extractor.es_last_updated_extractor import EsLastUpdatedExtractor
from databuilder.extractor.mysql_search_data_extractor import MySQLSearchDataExtractor
from databuilder.job.job import DefaultJob
from databuilder.loader.file_system_elasticsearch_json_loader import FSElasticsearchJSONLoader
from databuilder.loader.file_system_mysql_csv_loader import FSMySQLCSVLoader
from databuilder.publisher.elasticsearch_publisher import ElasticsearchPublisher
from databuilder.publisher.mysql_csv_publisher import MySQLCSVPublisher
from databuilder.task.task import DefaultTask
from databuilder.transformer.base_transformer import ChainedTransformer, NoopTransformer
from databuilder.transformer.dict_to_model import DictToModel
from databuilder.transformer.generic_transformer import GenericTransformer

es_host = os.getenv('CREDENTIALS_ELASTICSEARCH_PROXY_HOST', 'localhost')
es_port = os.getenv('CREDENTIALS_ELASTICSEARCH_PROXY_PORT', 9200)

mysql_host = os.getenv('CREDENTIALS_MYSQL_PROXY_HOST', 'localhost')
mysql_port = os.getenv('CREDENTIALS_MYSQL_PROXY_PORT', 3306)
mysql_db = os.getenv('CREDENTIALS_MYSQL_PROXY_DATABASE', 'test')

if len(sys.argv) > 1:
    es_host = sys.argv[1]
if len(sys.argv) > 2:
    mysql_host = sys.argv[2]

es = Elasticsearch([
    {'host': es_host, 'port': es_port},
])

mysql_user = 'root'
mysql_password = 'password'

mysql_conn_string = f'mysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_db}'


LOGGER = logging.getLogger(__name__)


def run_csv_job(file_loc, job_name, model):
    tmp_folder = f'/var/tmp/amundsen/{job_name}'
    record_files_folder = f'{tmp_folder}/records'

    csv_extractor = CsvExtractor()
    csv_loader = FSMySQLCSVLoader()

    task = DefaultTask(extractor=csv_extractor,
                       loader=csv_loader,
                       transformer=NoopTransformer())

    job_config = ConfigFactory.from_dict({
        'extractor.csv.file_location': file_loc,
        'extractor.csv.model_class': model,
        'loader.mysql_filesystem_csv.record_dir_path': record_files_folder,
        'loader.mysql_filesystem_csv.delete_created_directories': True,
        'publisher.mysql.record_files_directory': record_files_folder,
        'publisher.mysql.conn_string': mysql_conn_string,
        'publisher.mysql.job_publish_tag': 'unique_tag',
    })

    DefaultJob(conf=job_config,
               task=task,
               publisher=MySQLCSVPublisher()).launch()


def run_table_column_job(table_path, column_path):
    tmp_folder = '/var/tmp/amundsen/table_column'
    record_files_folder = f'{tmp_folder}/records'

    extractor = CsvTableColumnExtractor()
    csv_loader = FSMySQLCSVLoader()
    task = DefaultTask(extractor,
                       loader=csv_loader,
                       transformer=NoopTransformer())
    job_config = ConfigFactory.from_dict({
        'extractor.csvtablecolumn.table_file_location': table_path,
        'extractor.csvtablecolumn.column_file_location': column_path,
        'loader.mysql_filesystem_csv.record_dir_path': record_files_folder,
        'loader.mysql_filesystem_csv.delete_created_directories': True,
        'publisher.mysql.record_files_directory': record_files_folder,
        'publisher.mysql.conn_string': mysql_conn_string,
        'publisher.mysql.job_publish_tag': 'unique_tag'
    })
    job = DefaultJob(conf=job_config,
                     task=task,
                     publisher=MySQLCSVPublisher())
    job.launch()


def create_last_updated_job():
    # loader saves data to these folders and publisher reads it from here
    tmp_folder = '/var/tmp/amundsen/last_updated_data'
    record_files_folder = f'{tmp_folder}/records'

    task = DefaultTask(extractor=EsLastUpdatedExtractor(),
                       loader=FSMySQLCSVLoader())

    job_config = ConfigFactory.from_dict({
        'extractor.es_last_updated.model_class': 'databuilder.models.es_last_updated.ESLastUpdated',
        'loader.mysql_filesystem_csv.record_dir_path': record_files_folder,
        'loader.mysql_filesystem_csv.delete_created_directories': True,
        'publisher.mysql.record_files_directory': record_files_folder,
        'publisher.mysql.conn_string': mysql_conn_string,
        'publisher.mysql.job_publish_tag': 'unique_tag'
    })

    return DefaultJob(conf=job_config,
                      task=task,
                      publisher=MySQLCSVPublisher())


def _str_to_list(str_val):
    return str_val.split(',')


def create_dashboard_tables_job():
    # loader saves data to these folders and publisher reads it from here
    tmp_folder = '/var/tmp/amundsen/dashboard_table'
    record_files_folder = f'{tmp_folder}/records'
    model_class = 'databuilder.models.dashboard.dashboard_table.DashboardTable'

    csv_extractor = CsvExtractor()
    csv_loader = FSMySQLCSVLoader()

    generic_transformer = GenericTransformer()
    dict_to_model_transformer = DictToModel()
    transformer = ChainedTransformer(transformers=[generic_transformer, dict_to_model_transformer],
                                     is_init_transformers=True)

    task = DefaultTask(extractor=csv_extractor,
                       loader=csv_loader,
                       transformer=transformer)
    publisher = MySQLCSVPublisher()

    job_config = ConfigFactory.from_dict({
        'extractor.csv.file_location': 'example/sample_data/sample_dashboard_table.csv',
        'transformer.chained.transformer.generic.field_name': 'table_ids',
        'transformer.chained.transformer.generic.callback_function': _str_to_list,
        'transformer.chained.transformer.dict_to_model.model_class': model_class,
        'loader.mysql_filesystem_csv.record_dir_path': record_files_folder,
        'loader.mysql_filesystem_csv.delete_created_directories': True,
        'publisher.mysql.record_files_directory': record_files_folder,
        'publisher.mysql.conn_string': mysql_conn_string,
        'publisher.mysql.job_publish_tag': 'unique_tag',
    })

    return DefaultJob(conf=job_config,
                      task=task,
                      publisher=publisher)


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
    :param entity_type:                Entity type handed to the `MySQLSearchDataExtractor` class, used to determine
                                       search function to extract data from MySQL. Defaults to `table`.
    :param elasticsearch_mapping:      Elasticsearch field mapping "DDL" handed to the `ElasticsearchPublisher` class,
                                       if None is given (default) it uses the `Table` query baked into the Publisher
    """
    # loader saves data to this location and publisher reads it from here
    extracted_search_data_path = '/var/tmp/amundsen/search_data.json'

    task = DefaultTask(loader=FSElasticsearchJSONLoader(),
                       extractor=MySQLSearchDataExtractor(),
                       transformer=NoopTransformer())

    # elastic search client instance
    elasticsearch_client = es
    # unique name of new index in Elasticsearch
    elasticsearch_new_index_key = f'{elasticsearch_doc_type_key}_{uuid.uuid4()}'

    job_config = ConfigFactory.from_dict({
        'extractor.mysql_search_data.conn_string': mysql_conn_string,
        'extractor.mysql_search_data.entity_type': entity_type,
        'extractor.mysql_search_data.model_class': model_name,
        'loader.filesystem.elasticsearch.file_path': extracted_search_data_path,
        'loader.filesystem.elasticsearch.mode': 'w',
        'publisher.elasticsearch.file_path': extracted_search_data_path,
        'publisher.elasticsearch.mode': 'r',
        'publisher.elasticsearch.client': elasticsearch_client,
        'publisher.elasticsearch.new_index': elasticsearch_new_index_key,
        'publisher.elasticsearch.doc_type': elasticsearch_doc_type_key,
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
    run_csv_job('example/sample_data/sample_table_column_stats.csv', 'test_table_column_stats',
                'databuilder.models.table_stats.TableColumnStats')
    run_csv_job('example/sample_data/sample_table_programmatic_source.csv', 'test_programmatic_source',
                'databuilder.models.table_metadata.TableMetadata')
    run_csv_job('example/sample_data/sample_watermark.csv', 'test_watermark_metadata',
                'databuilder.models.watermark.Watermark')
    run_csv_job('example/sample_data/sample_user.csv', 'test_user_metadata',
                'databuilder.models.user.User')
    run_csv_job('example/sample_data/sample_table_owner.csv', 'test_table_owner_metadata',
                'databuilder.models.table_owner.TableOwner')
    run_csv_job('example/sample_data/sample_column_usage.csv', 'test_usage_metadata',
                'databuilder.models.table_column_usage.ColumnReader')
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
        elasticsearch_mapping=USER_INDEX_MAP)
    job_es_user.launch()

    job_es_dashboard = create_es_publisher_sample_job(
        elasticsearch_index_alias='dashboard_search_index',
        elasticsearch_doc_type_key='dashboard',
        model_name='databuilder.models.dashboard_elasticsearch_document.DashboardESDocument',
        entity_type='dashboard',
        elasticsearch_mapping=DASHBOARD_ELASTICSEARCH_INDEX_MAPPING)
    job_es_dashboard.launch()
