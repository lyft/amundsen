# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import unittest
from http import HTTPStatus

from mock import (
    MagicMock, Mock, patch,
)

from search_service import create_app
from search_service.api.document import DocumentUsersAPI


class TestDocumentUsersAPI(unittest.TestCase):
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
        RequestParser().parse_args.return_value = dict(data={}, index='fake_index')

        response = DocumentUsersAPI().post()
        self.assertEqual(list(response)[1], HTTPStatus.OK)
        mock_proxy.create_document.assert_called_with(data=[], index='fake_index')

    @patch('search_service.api.document.reqparse.RequestParser')
    @patch('search_service.api.document.get_proxy_client')
    def test_put(self, get_proxy: MagicMock, RequestParser: MagicMock) -> None:
        mock_proxy = get_proxy.return_value = Mock()
        RequestParser().parse_args.return_value = dict(data=[], index='fake_index')

        response = DocumentUsersAPI().put()
        self.assertEqual(list(response)[1], HTTPStatus.OK)
        mock_proxy.update_document.assert_called_with(data=[], index='fake_index')

    def test_should_not_reach_create_with_id(self) -> None:
        response = self.app.test_client().post('/document_user/1')

        self.assertEqual(response.status_code, 405)

    def test_should_not_reach_update_with_id(self) -> None:
        response = self.app.test_client().put('/document_user/1')

        self.assertEqual(response.status_code, 405)
