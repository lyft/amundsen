# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import json
import logging
from typing import List

from amundsen_common.models.index_map import TABLE_INDEX_MAP
from elasticsearch.exceptions import NotFoundError
from pyhocon import ConfigTree

from databuilder.publisher.base_publisher import Publisher

LOGGER = logging.getLogger(__name__)


class ElasticsearchPublisher(Publisher):
    """
    Elasticsearch Publisher uses Bulk API to load data from JSON file.
    A new index is created and data is uploaded into it. After the upload
    is complete, index alias is swapped to point to new index from old index
    and traffic is routed to new index.

    Old index is deleted after the alias swap is complete
    """
    FILE_PATH_CONFIG_KEY = 'file_path'
    FILE_MODE_CONFIG_KEY = 'mode'

    ELASTICSEARCH_CLIENT_CONFIG_KEY = 'client'
    ELASTICSEARCH_DOC_TYPE_CONFIG_KEY = 'doc_type'
    ELASTICSEARCH_NEW_INDEX_CONFIG_KEY = 'new_index'
    ELASTICSEARCH_ALIAS_CONFIG_KEY = 'alias'
    ELASTICSEARCH_MAPPING_CONFIG_KEY = 'mapping'

    # config to control how many max documents to publish at a time
    ELASTICSEARCH_PUBLISHER_BATCH_SIZE = 'batch_size'

    DEFAULT_ELASTICSEARCH_INDEX_MAPPING = TABLE_INDEX_MAP

    def __init__(self) -> None:
        super(ElasticsearchPublisher, self).__init__()

    def init(self, conf: ConfigTree) -> None:
        self.conf = conf

        self.file_path = self.conf.get_string(ElasticsearchPublisher.FILE_PATH_CONFIG_KEY)
        self.file_mode = self.conf.get_string(ElasticsearchPublisher.FILE_MODE_CONFIG_KEY, 'w')

        self.elasticsearch_type = self.conf.get_string(ElasticsearchPublisher.ELASTICSEARCH_DOC_TYPE_CONFIG_KEY)
        self.elasticsearch_client = self.conf.get(ElasticsearchPublisher.ELASTICSEARCH_CLIENT_CONFIG_KEY)
        self.elasticsearch_new_index = self.conf.get(ElasticsearchPublisher.ELASTICSEARCH_NEW_INDEX_CONFIG_KEY)
        self.elasticsearch_alias = self.conf.get(ElasticsearchPublisher.ELASTICSEARCH_ALIAS_CONFIG_KEY)

        self.elasticsearch_mapping = self.conf.get(ElasticsearchPublisher.ELASTICSEARCH_MAPPING_CONFIG_KEY,
                                                   ElasticsearchPublisher.DEFAULT_ELASTICSEARCH_INDEX_MAPPING)
        self.elasticsearch_batch_size = self.conf.get(ElasticsearchPublisher.ELASTICSEARCH_PUBLISHER_BATCH_SIZE,
                                                      10000)
        self.file_handler = open(self.file_path, self.file_mode)

    def _fetch_old_index(self) -> List[str]:
        """
        Retrieve all indices that currently have {elasticsearch_alias} alias
        :return: list of elasticsearch indices
        """
        try:
            indices = self.elasticsearch_client.indices.get_alias(self.elasticsearch_alias).keys()
            return indices
        except NotFoundError:
            LOGGER.warn("Received index not found error from Elasticsearch. " +
                        "The index doesn't exist for a newly created ES. It's OK on first run.")
            # return empty list on exception
            return []

    def publish_impl(self) -> None:
        """
        Use Elasticsearch Bulk API to load data from file to a {new_index}.
        After upload, swap alias from {old_index} to {new_index} in a atomic operation
        to route traffic to {new_index}
        """
        actions = [json.loads(line) for line in self.file_handler.readlines()]
        # ensure new data exists
        if not actions:
            LOGGER.warning("received no data to upload to Elasticsearch!")
            return

        # Convert object to json for elasticsearch bulk upload
        # Bulk load JSON format is defined here:
        # https://www.elastic.co/guide/en/elasticsearch/reference/6.2/docs-bulk.html
        bulk_actions = []
        cnt = 0

        # create new index with mapping
        self.elasticsearch_client.indices.create(index=self.elasticsearch_new_index, body=self.elasticsearch_mapping)
        for action in actions:
            index_row = dict(index=dict(_index=self.elasticsearch_new_index,
                                        _type=self.elasticsearch_type))
            bulk_actions.append(index_row)
            bulk_actions.append(action)
            cnt += 1
            if cnt == self.elasticsearch_batch_size:
                self.elasticsearch_client.bulk(bulk_actions)
                LOGGER.info('Publish %i of records to ES', cnt)
                cnt = 0
                bulk_actions = []

        # Do the final bulk actions
        if bulk_actions:
            self.elasticsearch_client.bulk(bulk_actions)

        # fetch indices that have {elasticsearch_alias} as alias
        elasticsearch_old_indices = self._fetch_old_index()

        # update alias to point to the new index
        actions = [{"add": {"index": self.elasticsearch_new_index, "alias": self.elasticsearch_alias}}]

        # delete old indices
        delete_actions = [{"remove_index": {"index": index}} for index in elasticsearch_old_indices]
        actions.extend(delete_actions)

        update_action = {"actions": actions}

        # perform alias update and index delete in single atomic operation
        self.elasticsearch_client.indices.update_aliases(update_action)

    def get_scope(self) -> str:
        return 'publisher.elasticsearch'
