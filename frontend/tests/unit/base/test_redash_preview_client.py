# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import flask
import json
import unittest

from http import HTTPStatus
from typing import Any, Dict, Optional, Tuple

from amundsen_application.base.base_redash_preview_client import BaseRedashPreviewClient


app = flask.Flask(__name__)
app.config.from_object('amundsen_application.config.LocalConfig')

REDASH_VALID_RESP = {
    'query_result': {
        'retrieved_at': '2021-04-16T04:11:42.678Z',
        'query_hash': '8b473ffc45316560515ee71e1c1aff08',
        'query': 'select * from tablelimit 10',
        'runtime': 1.98610711097717,
        'data': {
            'rows': [
                {'field_1': 'value1', 'field_2': None, 'field_3': '92064'},
                {'field_1': 'value2', 'field_2': 'abc', 'field_3': 'some-test-val'},
            ],
            'columns': [
                {'friendly_name': 'field_1', 'type': 'string', 'name': 'field_1'},
                {'friendly_name': 'field_2', 'type': 'string', 'name': 'field_2'},
                {'friendly_name': 'field_3', 'type': 'string', 'name': 'field_4'},
            ]
        },
        'id': 6,
        'data_source_id': 1
    }
}

REDASH_INVALID_RESP = {
    'query_result': {
        'retrieved_at': '2021-04-16T04:11:42.678Z',
        'query_hash': '8b473ffc45316560515ee71e1c1aff08',
        'query': 'select * from tablelimit 10',
        'runtime': 1.98610711097717,
        'data': {
            'rows': [
                {'field_1': 'value1'},
                {'field_1': 'value2'},
            ],
            'columns': [
                {'friendly_name': 'field_1', 'type': 'int', 'name': 'field_1'},
                {'friendly_name': 'field_2', 'type': 'bool', 'name': 'field_2'},
                {'friendly_name': 'field_3', 'type': 'string', 'name': 'field_4'},
            ]
        },
        'id': 6,
        'data_source_id': 1
    }
}

EXPECTED_PROCESSED_RESP = {
    'columns': [
        {'column_name': 'field_1', 'column_type': 'string'},
        {'column_name': 'field_2', 'column_type': 'string'},
        {'column_name': 'field_4', 'column_type': 'string'}
    ],
    'data': [
        {'field_1': 'value1', 'field_2': None, 'field_3': '92064'},
        {'field_1': 'value2', 'field_2': 'abc', 'field_3': 'some-test-val'}
    ],
    'error_text': ''
}

REDASH_QUERY_JOB_RESP = {
    'job': {
        'status': 2,
        'error': '',
        'id': '206e4d7f-7c68-4607-b744-5fabd2e09a4b',
        'query_result_id': None,
        'updated_at': 0
    }
}


class MockRedashClient(BaseRedashPreviewClient):
    def __init__(self) -> None:
        super().__init__(redash_host='', user_api_key='n/a')

    def get_redash_query_id(self, params: Dict) -> Optional[int]:
        return 1


class MockRedashNoQueryIdClient(BaseRedashPreviewClient):
    def __init__(self) -> None:
        super().__init__(redash_host='', user_api_key='n/a')

    def get_redash_query_id(self, params: Dict) -> Optional[int]:
        return None


class MockRedashNoApiKeyClient(BaseRedashPreviewClient):
    def __init__(self) -> None:
        super().__init__(redash_host='')

    def get_redash_query_id(self, params: Dict) -> Optional[int]:
        return None


class MockMulitpleApiKeyClient(BaseRedashPreviewClient):
    def __init__(self) -> None:
        super().__init__(redash_host='', user_api_key='base-key')

    def get_redash_query_id(self, params: Dict) -> Optional[int]:
        return None

    def _get_query_api_key(self, params: Dict) -> Optional[str]:
        return 'override-key'


class MockRedashCachedResultClient(BaseRedashPreviewClient):
    def __init__(self) -> None:
        super().__init__(redash_host='', user_api_key='n/a')

    def get_redash_query_id(self, params: Dict) -> Optional[int]:
        return 1

    def _start_redash_query(self, query_id: int, query_params: Dict) -> Tuple[Any, bool]:
        return REDASH_VALID_RESP, True


class MockRedashNewQueryJobClient(BaseRedashPreviewClient):
    def __init__(self) -> None:
        super().__init__(redash_host='', user_api_key='n/a')

    def get_redash_query_id(self, params: Dict) -> Optional[int]:
        return 1

    def _start_redash_query(self, query_id: int, query_params: Dict) -> Tuple[Any, bool]:
        return REDASH_QUERY_JOB_RESP, False

    def _wait_for_query_finish(self, job_id: str, max_wait: int = 60) -> str:
        return 'results-ID'

    def _get_query_results(self, query_result_id: str) -> Dict:
        return REDASH_VALID_RESP


class MockRedashBadDataResultClient(BaseRedashPreviewClient):
    def __init__(self) -> None:
        super().__init__(redash_host='', user_api_key='n/a')

    def get_redash_query_id(self, params: Dict) -> Optional[int]:
        return 1

    def _start_redash_query(self, query_id: int, query_params: Dict) -> Tuple[Any, bool]:
        return REDASH_INVALID_RESP, True


class RedashPreviewClientTest(unittest.TestCase):

    def test_no_query_id_raises_error(self) -> None:
        """
        Tests that returning no query_id returns an error.
        :return:
        """
        with app.test_request_context():
            response = MockRedashNoQueryIdClient().get_preview_data(params={})
            self.assertEqual(response.status_code, HTTPStatus.INTERNAL_SERVER_ERROR)

    def test_no_api_key_raises_error(self) -> None:
        """
        Tests that returning no api key returns an error.
        :return:
        """
        with app.test_request_context():
            response = MockRedashNoApiKeyClient().get_preview_data(params={})
            self.assertEqual(response.status_code, HTTPStatus.INTERNAL_SERVER_ERROR)

    def test_query_api_key_overrides_default_api_key(self) -> None:
        """
        Tests that returning no api key returns an error.
        :return:
        """
        with app.test_request_context():
            mocK_client = MockMulitpleApiKeyClient()
            mocK_client._build_headers(params={})
            self.assertEqual(mocK_client.headers, {'Authorization': 'Key override-key'})

    def test_build_redash_query_params(self) -> None:
        sample_params = {'schema': 'test_schema', 'tableName': 'test_table'}
        test_redash_client = MockRedashClient()
        resp = test_redash_client.build_redash_query_params(sample_params)
        expected_resp = {
            'parameters': {
                'SELECT_FIELDS': '*',
                'SCHEMA_NAME': 'test_schema',
                'TABLE_NAME': 'test_table',
                'WHERE_CLAUSE': '',
                'RCD_LIMIT': '50'
            },
            'max_age': test_redash_client.max_redash_cache_age
        }
        self.assertEquals(resp, expected_resp)

    def test_redash_api_returns_cached_result(self) -> None:
        """
        Test the response from Redash is a previously cached object
        :return:
        """
        with app.test_request_context():
            response = MockRedashCachedResultClient().get_preview_data(params={})
            self.assertEqual(json.loads(response.data).get('preview_data'), EXPECTED_PROCESSED_RESP)
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_redash_api_returns_query_job(self) -> None:
        """
        Test the response from Redash is a previously cached object
        :return:
        """
        with app.test_request_context():
            response = MockRedashNewQueryJobClient().get_preview_data(params={})
            self.assertEqual(json.loads(response.data).get('preview_data'), EXPECTED_PROCESSED_RESP)
            self.assertEqual(response.status_code, HTTPStatus.OK)
