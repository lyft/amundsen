# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import uuid

from elasticsearch import Elasticsearch
from pyhocon import ConfigFactory

from databuilder.extractor.atlas_search_data_extractor import AtlasSearchDataExtractor
from databuilder.job.job import DefaultJob
from databuilder.loader.file_system_elasticsearch_json_loader import FSElasticsearchJSONLoader
from databuilder.publisher.elasticsearch_publisher import ElasticsearchPublisher
from databuilder.task.task import DefaultTask
from databuilder.transformer.base_transformer import NoopTransformer

entity_type = 'Table'
extracted_search_data_path = f'/tmp/{entity_type.lower()}_search_data.json'
process_pool_size = 5

# atlas config
atlas_url = 'localhost'
atlas_port = 21000
atlas_protocol = 'http'
atlas_verify_ssl = False
atlas_username = 'admin'
atlas_password = 'admin'
atlas_search_chunk_size = 200
atlas_details_chunk_size = 10

# elastic config
es = Elasticsearch([
    {'host': 'localhost'},
])

elasticsearch_client = es
elasticsearch_new_index_key = f'{entity_type.lower()}-' + str(uuid.uuid4())
elasticsearch_new_index_key_type = '_doc'
elasticsearch_index_alias = f'{entity_type.lower()}_search_index'

job_config = ConfigFactory.from_dict({
    'extractor.atlas_search_data.{}'.format(AtlasSearchDataExtractor.ATLAS_URL_CONFIG_KEY):
        atlas_url,
    'extractor.atlas_search_data.{}'.format(AtlasSearchDataExtractor.ATLAS_PORT_CONFIG_KEY):
        atlas_port,
    'extractor.atlas_search_data.{}'.format(AtlasSearchDataExtractor.ATLAS_PROTOCOL_CONFIG_KEY):
        atlas_protocol,
    'extractor.atlas_search_data.{}'.format(AtlasSearchDataExtractor.ATLAS_VALIDATE_SSL_CONFIG_KEY):
        atlas_verify_ssl,
    'extractor.atlas_search_data.{}'.format(AtlasSearchDataExtractor.ATLAS_USERNAME_CONFIG_KEY):
        atlas_username,
    'extractor.atlas_search_data.{}'.format(AtlasSearchDataExtractor.ATLAS_PASSWORD_CONFIG_KEY):
        atlas_password,
    'extractor.atlas_search_data.{}'.format(AtlasSearchDataExtractor.ATLAS_SEARCH_CHUNK_SIZE_KEY):
        atlas_search_chunk_size,
    'extractor.atlas_search_data.{}'.format(AtlasSearchDataExtractor.ATLAS_DETAILS_CHUNK_SIZE_KEY):
        atlas_details_chunk_size,
    'extractor.atlas_search_data.{}'.format(AtlasSearchDataExtractor.PROCESS_POOL_SIZE_KEY):
        process_pool_size,
    'extractor.atlas_search_data.{}'.format(AtlasSearchDataExtractor.ENTITY_TYPE_KEY):
        entity_type,
    'loader.filesystem.elasticsearch.{}'.format(FSElasticsearchJSONLoader.FILE_PATH_CONFIG_KEY):
        extracted_search_data_path,
    'loader.filesystem.elasticsearch.{}'.format(FSElasticsearchJSONLoader.FILE_MODE_CONFIG_KEY):
        'w',
    'publisher.elasticsearch.{}'.format(ElasticsearchPublisher.FILE_PATH_CONFIG_KEY):
        extracted_search_data_path,
    'publisher.elasticsearch.{}'.format(ElasticsearchPublisher.FILE_MODE_CONFIG_KEY):
        'r',
    'publisher.elasticsearch.{}'.format(ElasticsearchPublisher.ELASTICSEARCH_CLIENT_CONFIG_KEY):
        elasticsearch_client,
    'publisher.elasticsearch.{}'.format(ElasticsearchPublisher.ELASTICSEARCH_NEW_INDEX_CONFIG_KEY):
        elasticsearch_new_index_key,
    'publisher.elasticsearch.{}'.format(ElasticsearchPublisher.ELASTICSEARCH_DOC_TYPE_CONFIG_KEY):
        elasticsearch_new_index_key_type,
    'publisher.elasticsearch.{}'.format(ElasticsearchPublisher.ELASTICSEARCH_ALIAS_CONFIG_KEY):
        elasticsearch_index_alias
})

if __name__ == "__main__":
    task = DefaultTask(extractor=AtlasSearchDataExtractor(),
                       transformer=NoopTransformer(),
                       loader=FSElasticsearchJSONLoader())

    job = DefaultJob(conf=job_config,
                     task=task,
                     publisher=ElasticsearchPublisher())

    job.launch()
