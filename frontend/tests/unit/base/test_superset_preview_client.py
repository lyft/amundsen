# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import flask
import json
import unittest

from http import HTTPStatus
from requests import Response
from typing import Dict
from unittest.mock import Mock

from amundsen_application.base.base_superset_preview_client import BaseSupersetPreviewClient

app = flask.Flask(__name__)
app.config.from_object('amundsen_application.config.LocalConfig')

good_json_data = {
    "columns": [
        {
            "agg": "count_distinct",
            "is_date": False,
            "type": "INT",
            "name": "id",
            "is_dim": False,
        },
        {
            "is_date": False,
            "type": "STRING",
            "name": "name",
            "is_dim": True,
        }
    ],
    "data": [
        {"id": 1, "name": "Admin"},
        {"id": 2, "name": "Public"},
        {"id": 3, "name": "Alpha"},
    ]
}
expected_results = {
    "columns": [
        {
            "column_type": "INT",
            "column_name": "id",
        },
        {
            "column_type": "STRING",
            "column_name": "name",
        }
    ],
    "data": [
        {"id": 1, "name": "Admin"},
        {"id": 2, "name": "Public"},
        {"id": 3, "name": "Alpha"},
    ],
    "error_text": ""
}

bad_json_data = {
    "columns": [
        {
            "agg": "count_distinct",
            "is_date": False,
            "type": "INT",
            "name": "id",
            "is_dim": False,
        },
        {
            "is_date": False,
            "type": "STRING",
            "name": "name",
            "is_dim": True,
        }
    ],
    "data": "Wrong type",
}


class MockClient(BaseSupersetPreviewClient):
    def __init__(self) -> None:
        super().__init__()

    def post_to_sql_json(self, *, params: Dict, headers: Dict) -> Response:
        mockresponse = Mock()
        mockresponse.json.return_value = good_json_data
        mockresponse.status_code = HTTPStatus.OK
        return mockresponse


class MockBadDataClient(BaseSupersetPreviewClient):
    def __init__(self) -> None:
        self.headers = {}

    def post_to_sql_json(self, *, params: Dict, headers: Dict) -> Response:
        mockresponse = Mock()
        mockresponse.json.return_value = bad_json_data
        mockresponse.status_code = HTTPStatus.OK
        return mockresponse


class MockExceptionClient(BaseSupersetPreviewClient):
    def __init__(self) -> None:
        super().__init__()

    def post_to_sql_json(self, *, params: Dict, headers: Dict) -> Response:
        mockresponse = Mock()
        mockresponse.json.return_value = None
        mockresponse.status_code = HTTPStatus.OK
        return mockresponse


class SupersetPreviewClientTest(unittest.TestCase):
    def test_get_preview_data_raise_exception(self) -> None:
        """
        Test catching any exception raised in get_preview_data(), which should result in
        a response with 500 error and empty preview_data payload
        :return:
        """
        with app.test_request_context():
            response = MockExceptionClient().get_preview_data(params={})
            self.assertEqual(json.loads(response.data).get('preview_data'), {})
            self.assertEqual(response.status_code, HTTPStatus.INTERNAL_SERVER_ERROR)

    def test_post_sql_json_incorrect_data_shape(self) -> None:
        """
        Test catching errors in the data shape returned by post_sql_json(), which should result in
        a response with 500 error and empty preview_data payload
        :return:
        """
        with app.test_request_context():
            response = MockBadDataClient().get_preview_data(params={})
            self.assertEqual(json.loads(response.data).get('preview_data'), {})
            self.assertEqual(response.status_code, HTTPStatus.INTERNAL_SERVER_ERROR)

    def test_post_sql_json_correct_data_shape(self) -> None:
        """
        Test post_sql_json(), which should result in
        a response with 200 status and correct preview_data payload
        :return:
        """
        with app.test_request_context():
            response = MockClient().get_preview_data(params={}, optionalHeaders={'testKey': 'testValue'})
            self.assertEqual(json.loads(response.data).get('preview_data'), expected_results)
            self.assertEqual(response.status_code, HTTPStatus.OK)
