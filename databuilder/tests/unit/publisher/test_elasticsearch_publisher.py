# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import json
import unittest

from mock import (
    MagicMock, mock_open, patch,
)
from pyhocon import ConfigFactory

from databuilder import Scoped
from databuilder.publisher.elasticsearch_publisher import ElasticsearchPublisher


class TestElasticsearchPublisher(unittest.TestCase):

    def setUp(self) -> None:
        self.test_file_path = 'test_publisher_file.json'
        self.test_file_mode = 'r'

        self.mock_es_client = MagicMock()
        self.test_es_new_index = 'test_new_index'
        self.test_es_alias = 'test_index_alias'
        self.test_doc_type = 'test_doc_type'

        config_dict = {'publisher.elasticsearch.file_path': self.test_file_path,
                       'publisher.elasticsearch.mode': self.test_file_mode,
                       'publisher.elasticsearch.client': self.mock_es_client,
                       'publisher.elasticsearch.new_index': self.test_es_new_index,
                       'publisher.elasticsearch.alias': self.test_es_alias,
                       'publisher.elasticsearch.doc_type': self.test_doc_type}

        self.conf = ConfigFactory.from_dict(config_dict)

    def test_publish_with_no_data(self) -> None:
        """
        Test Publish functionality with no data
        """
        with patch('builtins.open', mock_open(read_data='')) as mock_file:
            publisher = ElasticsearchPublisher()
            publisher.init(conf=Scoped.get_scoped_conf(conf=self.conf,
                                                       scope=publisher.get_scope()))

            # assert mock was called with test_file_path and test_file_mode
            mock_file.assert_called_with(self.test_file_path, self.test_file_mode)

            publisher.publish()
            # no calls should be made through elasticseach_client when there is no data
            self.assertTrue(self.mock_es_client.call_count == 0)

    def test_publish_with_data_and_no_old_index(self) -> None:
        """
        Test Publish functionality with data but no index in place
        """
        mock_data = json.dumps({'KEY_DOESNOT_MATTER': 'NO_VALUE',
                                'KEY_DOESNOT_MATTER2': 'NO_VALUE2'})
        self.mock_es_client.indices.get_alias.return_value = {}

        with patch('builtins.open', mock_open(read_data=mock_data)) as mock_file:
            publisher = ElasticsearchPublisher()
            publisher.init(conf=Scoped.get_scoped_conf(conf=self.conf,
                                                       scope=publisher.get_scope()))

            # assert mock was called with test_file_path and test_file_mode
            mock_file.assert_called_once_with(self.test_file_path, self.test_file_mode)

            publisher.publish()
            # ensure indices create endpoint was called
            default_mapping = ElasticsearchPublisher.DEFAULT_ELASTICSEARCH_INDEX_MAPPING
            self.mock_es_client.indices.create.assert_called_once_with(index=self.test_es_new_index,
                                                                       body=default_mapping)

            # bulk endpoint called once
            self.mock_es_client.bulk.assert_called_once_with(
                [{'index': {'_type': self.test_doc_type, '_index': self.test_es_new_index}},
                 {'KEY_DOESNOT_MATTER': 'NO_VALUE', 'KEY_DOESNOT_MATTER2': 'NO_VALUE2'}]
            )

            # update alias endpoint called once
            self.mock_es_client.indices.update_aliases.assert_called_once_with(
                {'actions': [{"add": {"index": self.test_es_new_index, "alias": self.test_es_alias}}]}
            )

    def test_publish_with_data_and_old_index(self) -> None:
        """
        Test Publish functionality with data and with old_index in place
        """
        mock_data = json.dumps({'KEY_DOESNOT_MATTER': 'NO_VALUE',
                                'KEY_DOESNOT_MATTER2': 'NO_VALUE2'})
        self.mock_es_client.indices.get_alias.return_value = {'test_old_index': 'DOES_NOT_MATTER'}

        with patch('builtins.open', mock_open(read_data=mock_data)) as mock_file:
            publisher = ElasticsearchPublisher()
            publisher.init(conf=Scoped.get_scoped_conf(conf=self.conf,
                                                       scope=publisher.get_scope()))

            # assert mock was called with test_file_path and test_file_mode
            mock_file.assert_called_once_with(self.test_file_path, self.test_file_mode)

            publisher.publish()
            # ensure indices create endpoint was called
            default_mapping = ElasticsearchPublisher.DEFAULT_ELASTICSEARCH_INDEX_MAPPING
            self.mock_es_client.indices.create.assert_called_once_with(index=self.test_es_new_index,
                                                                       body=default_mapping)

            # bulk endpoint called once
            self.mock_es_client.bulk.assert_called_once_with(
                [{'index': {'_type': self.test_doc_type, '_index': self.test_es_new_index}},
                 {'KEY_DOESNOT_MATTER': 'NO_VALUE', 'KEY_DOESNOT_MATTER2': 'NO_VALUE2'}]
            )

            # update alias endpoint called once
            self.mock_es_client.indices.update_aliases.assert_called_once_with(
                {'actions': [{"add": {"index": self.test_es_new_index, "alias": self.test_es_alias}},
                             {"remove_index": {"index": 'test_old_index'}}]}
            )
