# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import json
import unittest
from http import HTTPStatus

from marshmallow.exceptions import ValidationError
from mock import (
    MagicMock, Mock, patch,
)

from search_service import create_app
from search_service.api.document import DocumentFeaturesAPI
from search_service.models.feature import Feature
from search_service.models.tag import Tag


class TestDocumentFeaturesAPI(unittest.TestCase):
    def setUp(self) -> None:
        self.app = create_app(config_module_class='search_service.config.Config')
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tear_down(self) -> None:
        self.app_context.pop()

    @patch('search_service.api.document.reqparse.RequestParser')
    @patch('search_service.api.document.get_proxy_client')
    def test_post(self, get_proxy: MagicMock, RequestParser: MagicMock) -> None:
        mock_proxy = get_proxy.return_value = Mock()
        RequestParser().parse_args.return_value = dict(data=[], index='fake_index')

        response = DocumentFeaturesAPI().post()
        self.assertEqual(list(response)[1], HTTPStatus.OK)
        mock_proxy.create_document.assert_called_with(data=[], index='fake_index')

    @patch('search_service.api.document.reqparse.RequestParser')
    @patch('search_service.api.document.get_proxy_client')
    def test_put(self, get_proxy: MagicMock, RequestParser: MagicMock) -> None:
        mock_proxy = get_proxy.return_value = Mock()
        RequestParser().parse_args.return_value = dict(data=[], index='fake_index')

        response = DocumentFeaturesAPI().put()
        self.assertEqual(list(response)[1], HTTPStatus.OK)
        mock_proxy.update_document.assert_called_with(data=[], index='fake_index')

    @patch('search_service.api.document.reqparse.RequestParser')
    @patch('search_service.api.document.get_proxy_client')
    def test_put_multiple_features(self, get_proxy: MagicMock, RequestParser: MagicMock) -> None:
        mock_proxy = get_proxy.return_value = Mock()
        input_data = [
            json.dumps({
                'id': '123aaabbb',
                'feature_group': 'group1',
                'feature_name': 'name1',
                'version': '7',
                'key': 'group1/name1/7',
                'total_usage': 12,
                'description': 'friendly description of a feature',
                'last_updated_timestamp': 12345678,
                'tags': [{'tag_name': 'tag1'}, {'tag_name': 'tag2'}]
            }),
            json.dumps({
                'id': '456bbbccc',
                'feature_group': 'group1',
                'feature_name': 'name2',
                'version': 'v1.0.0',
                'key': 'group1/name2/v1.0.0',
                'total_usage': 0,
                'availability': ['postgres'],
                'last_updated_timestamp': 12345678,
                'badges': [{'tag_name': 'badge1'}, {'tag_name': 'badge2'}]
            })
        ]
        RequestParser().parse_args.return_value = dict(data=input_data, index='fake_index')

        expected_data = [Feature(id='123aaabbb', feature_group='group1', feature_name='name1', version='7',
                                 key='group1/name1/7', total_usage=12, description='friendly description of a feature',
                                 last_updated_timestamp=12345678, tags=[Tag(tag_name='tag1'), Tag(tag_name='tag2')]),
                         Feature(id='456bbbccc', feature_group='group1', feature_name='name2', version='v1.0.0',
                                 key='group1/name2/v1.0.0', total_usage=0, availability=['postgres'],
                                 last_updated_timestamp=12345678,
                                 badges=[Tag(tag_name='badge1'), Tag(tag_name='badge2')])]

        response = DocumentFeaturesAPI().put()
        self.assertEqual(list(response)[1], HTTPStatus.OK)
        mock_proxy.update_document.assert_called_with(data=expected_data, index='fake_index')

    @patch('search_service.api.document.reqparse.RequestParser')
    @patch('search_service.api.document.get_proxy_client')
    def test_put_multiple_features_fails(self, get_proxy: MagicMock, RequestParser: MagicMock) -> None:
        input_data = [
            json.dumps({
                'anykey1': 'anyval1'
            }),
            json.dumps({
                'anykey2': 'anyval2'
            })
        ]
        RequestParser().parse_args.return_value = dict(data=input_data, index='fake_index')

        with self.assertRaises(ValidationError):
            DocumentFeaturesAPI().put()

    def test_should_not_reach_create_with_id(self) -> None:
        response = self.app.test_client().post('/document_feature/1')
        self.assertEqual(response.status_code, 405)

    def test_should_not_reach_update_with_id(self) -> None:
        response = self.app.test_client().put('/document_feature/1')
        self.assertEqual(response.status_code, 405)
