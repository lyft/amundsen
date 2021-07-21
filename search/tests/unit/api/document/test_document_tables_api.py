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
from search_service.api.document import DocumentTablesAPI
from search_service.models.table import Table
from search_service.models.tag import Tag


class TestDocumentTablesAPI(unittest.TestCase):
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

        response = DocumentTablesAPI().post()
        self.assertEqual(list(response)[1], HTTPStatus.OK)
        mock_proxy.create_document.assert_called_with(data=[], index='fake_index')

    @patch('search_service.api.document.reqparse.RequestParser')
    @patch('search_service.api.document.get_proxy_client')
    def test_put(self, get_proxy: MagicMock, RequestParser: MagicMock) -> None:
        mock_proxy = get_proxy.return_value = Mock()
        RequestParser().parse_args.return_value = dict(data=[], index='fake_index')

        response = DocumentTablesAPI().put()
        self.assertEqual(list(response)[1], HTTPStatus.OK)
        mock_proxy.update_document.assert_called_with(data=[], index='fake_index')

    @patch('search_service.api.document.reqparse.RequestParser')
    @patch('search_service.api.document.get_proxy_client')
    def test_put_multiple_tables(self, get_proxy: MagicMock, RequestParser: MagicMock) -> None:
        mock_proxy = get_proxy.return_value = Mock()
        input_data = [
            json.dumps({
                'id': 'table1',
                'key': 'table1',
                'cluster': 'cluster1',
                'database': 'database1',
                'name': 'name1',
                'schema': 'schema1',
                'last_updated_timestamp': 12345678,
                'tags': [{'tag_name': 'tag1'}, {'tag_name': 'tag2'}]
            }),
            json.dumps({
                'id': 'table2',
                'key': 'table2',
                'cluster': 'cluster2',
                'database': 'database2',
                'name': 'name2',
                'schema': 'schema2',
                'last_updated_timestamp': 12345678,
                'tags': [{'tag_name': 'tag3'}, {'tag_name': 'tag4'}]
            })
        ]
        RequestParser().parse_args.return_value = dict(data=input_data, index='fake_index')

        expected_data = [Table(id='table1', database='database1', cluster='cluster1', schema='schema1', name='name1',
                               key='table1', tags=[Tag(tag_name='tag1'), Tag(tag_name='tag2')],
                               last_updated_timestamp=12345678),
                         Table(id='table2', database='database2', cluster='cluster2', schema='schema2', name='name2',
                               key='table2', tags=[Tag(tag_name='tag3'), Tag(tag_name='tag4')],
                               last_updated_timestamp=12345678)]

        response = DocumentTablesAPI().put()
        self.assertEqual(list(response)[1], HTTPStatus.OK)
        mock_proxy.update_document.assert_called_with(data=expected_data, index='fake_index')

    @patch('search_service.api.document.reqparse.RequestParser')
    @patch('search_service.api.document.get_proxy_client')
    def test_put_multiple_tables_fails(self, get_proxy: MagicMock, RequestParser: MagicMock) -> None:
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
            DocumentTablesAPI().put()

    def test_should_not_reach_create_with_id(self) -> None:
        response = self.app.test_client().post('/document_table/1')

        self.assertEqual(response.status_code, 405)

    def test_should_not_reach_update_with_id(self) -> None:
        response = self.app.test_client().put('/document_table/1')

        self.assertEqual(response.status_code, 405)
