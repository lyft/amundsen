# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

"""
This is a example script for extracting Feast feature tables

Usage:
    python3 sample_feast_loader.py [feast_core] [neo4j_endpoint] [es_url]

For example:
    python sample_feast_loader.py feast-feast-core:6565 bolt://neo4j http://elasticsearch:9200
"""

import sys
import uuid

from elasticsearch.client import Elasticsearch
from pyhocon import ConfigFactory

from databuilder.extractor.feast_extractor import FeastExtractor
from databuilder.extractor.neo4j_extractor import Neo4jExtractor
from databuilder.extractor.neo4j_search_data_extractor import Neo4jSearchDataExtractor
from databuilder.job.job import DefaultJob
from databuilder.loader.file_system_elasticsearch_json_loader import FSElasticsearchJSONLoader
from databuilder.loader.file_system_neo4j_csv_loader import FsNeo4jCSVLoader
from databuilder.publisher import neo4j_csv_publisher
from databuilder.publisher.elasticsearch_publisher import ElasticsearchPublisher
from databuilder.task.task import DefaultTask

feast_endpoint = sys.argv[1]
feast_serving_endpoint = sys.argv[2]
neo4j_endpoint = sys.argv[3]
es_url = sys.argv[4]
es = Elasticsearch([es_url])

neo4j_user = "neo4j"
neo4j_password = "test"


def create_feast_job_config():
    tmp_folder = "/var/tmp/amundsen/table_metadata"
    node_files_folder = f"{tmp_folder}/nodes/"
    relationship_files_folder = f"{tmp_folder}/relationships/"

    job_config = ConfigFactory.from_dict(
        {
            f"extractor.feast.{FeastExtractor.FEAST_ENDPOINT_CONFIG_KEY}": feast_endpoint,
            f'extractor.feast.{FeastExtractor.FEAST_SERVING_ENDPOINT_CONFIG_KEY}': feast_serving_endpoint,
            f"loader.filesystem_csv_neo4j.{FsNeo4jCSVLoader.NODE_DIR_PATH}": node_files_folder,
            f"loader.filesystem_csv_neo4j.{FsNeo4jCSVLoader.RELATION_DIR_PATH}": relationship_files_folder,
            f"publisher.neo4j.{neo4j_csv_publisher.NODE_FILES_DIR}": node_files_folder,
            f"publisher.neo4j.{neo4j_csv_publisher.RELATION_FILES_DIR}": relationship_files_folder,
            f"publisher.neo4j.{neo4j_csv_publisher.NEO4J_END_POINT_KEY}": neo4j_endpoint,
            f"publisher.neo4j.{neo4j_csv_publisher.NEO4J_USER}": neo4j_user,
            f"publisher.neo4j.{neo4j_csv_publisher.NEO4J_PASSWORD}": neo4j_password,
            "publisher.neo4j.job_publish_tag": "some_unique_tag",  # TO-DO unique tag must be added
        }
    )
    return job_config


def create_es_publish_job_config(
        elasticsearch_index_alias="table_search_index",
        elasticsearch_doc_type_key="table",
        model_name="databuilder.models.table_elasticsearch_document.TableESDocument",
        cypher_query=None,
        elasticsearch_mapping=None,
):
    """
    :param elasticsearch_index_alias:  alias for Elasticsearch used in
                                       amundsensearchlibrary/search_service/config.py as an index
    :param elasticsearch_doc_type_key: name the ElasticSearch index is prepended with. Defaults to `table` resulting in
                                       `table_search_index`
    :param model_name:                 the Databuilder model class used in transporting between Extractor and Loader
    :param cypher_query:               Query handed to the `Neo4jSearchDataExtractor` class, if None is given (default)
                                       it uses the `Table` query baked into the Extractor
    :param elasticsearch_mapping:      Elasticsearch field mapping "DDL" handed to the `ElasticsearchPublisher` class,
                                       if None is given (default) it uses the `Table` query baked into the Publisher
    """
    # loader saves data to this location and publisher reads it from here
    extracted_search_data_path = "/var/tmp/amundsen/search_data.json"

    # elastic search client instance
    elasticsearch_client = es
    # unique name of new index in Elasticsearch
    elasticsearch_new_index_key = "tables" + str(uuid.uuid4())

    job_config = ConfigFactory.from_dict(
        {
            f"extractor.search_data.extractor.neo4j.{Neo4jExtractor.GRAPH_URL_CONFIG_KEY}": neo4j_endpoint,
            f"extractor.search_data.extractor.neo4j.{Neo4jExtractor.MODEL_CLASS_CONFIG_KEY}": model_name,
            f"extractor.search_data.extractor.neo4j.{Neo4jExtractor.NEO4J_AUTH_USER}": neo4j_user,
            f"extractor.search_data.extractor.neo4j.{Neo4jExtractor.NEO4J_AUTH_PW}": neo4j_password,
            f"loader.filesystem.elasticsearch.{FSElasticsearchJSONLoader.FILE_PATH_CONFIG_KEY}":
                extracted_search_data_path,
            f"loader.filesystem.elasticsearch.{FSElasticsearchJSONLoader.FILE_MODE_CONFIG_KEY}": "w",
            f"publisher.elasticsearch.{ElasticsearchPublisher.FILE_PATH_CONFIG_KEY}": extracted_search_data_path,
            f"publisher.elasticsearch.{ElasticsearchPublisher.FILE_MODE_CONFIG_KEY}": "r",
            f"publisher.elasticsearch.{ElasticsearchPublisher.ELASTICSEARCH_CLIENT_CONFIG_KEY}":
                elasticsearch_client,
            f"publisher.elasticsearch.{ElasticsearchPublisher.ELASTICSEARCH_NEW_INDEX_CONFIG_KEY}":
                elasticsearch_new_index_key,
            f"publisher.elasticsearch.{ElasticsearchPublisher.ELASTICSEARCH_DOC_TYPE_CONFIG_KEY}":
                elasticsearch_doc_type_key,
            f"publisher.elasticsearch.{ElasticsearchPublisher.ELASTICSEARCH_ALIAS_CONFIG_KEY}":
                elasticsearch_index_alias,
        }
    )

    # only optionally add these keys, so need to dynamically `put` them
    if cypher_query:
        job_config.put(
            f"extractor.search_data.{Neo4jSearchDataExtractor.CYPHER_QUERY_CONFIG_KEY}",
            cypher_query,
        )
    if elasticsearch_mapping:
        job_config.put(
            f"publisher.elasticsearch.{ElasticsearchPublisher.ELASTICSEARCH_MAPPING_CONFIG_KEY}",
            elasticsearch_mapping,
        )

    return job_config


if __name__ == "__main__":
    feast_job = DefaultJob(
        conf=create_feast_job_config(),
        task=DefaultTask(extractor=FeastExtractor(), loader=FsNeo4jCSVLoader()),
        publisher=neo4j_csv_publisher.Neo4jCsvPublisher(),
    )
    feast_job.launch()

    es_publish_job = DefaultJob(
        conf=create_es_publish_job_config(),
        task=DefaultTask(
            loader=FSElasticsearchJSONLoader(), extractor=Neo4jSearchDataExtractor()
        ),
        publisher=ElasticsearchPublisher(),
    )
    es_publish_job.launch()
