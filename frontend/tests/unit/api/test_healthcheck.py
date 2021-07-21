# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0
from http import HTTPStatus
import json
import unittest
from unittest.mock import MagicMock, patch

from amundsen_application import create_app

local_app = create_app('amundsen_application.config.TestConfig', 'tests/templates')


class HealthCheckTest(unittest.TestCase):
    def setUp(self) -> None:
        self.healthcheck_endpoint = '/healthcheck'
        self.search_service_url = local_app.config['SEARCHSERVICE_BASE'] + '/healthcheck'
        self.metadata_service_url = local_app.config['METADATASERVICE_BASE'] + '/healthcheck'

    @patch('amundsen_application.api.healthcheck.request_search', autospec=True)
    @patch('amundsen_application.api.healthcheck.request_metadata', autospec=True)
    def test_healthcheck_pass(
        self,
        mock_metadata_health: MagicMock,
        mock_search_health: MagicMock
    ) -> None:
        """
        Test request failure if 'term' is not provided in the request json
        :return:
        """
        mock_search = MagicMock()
        mock_search.status_code = HTTPStatus.OK
        mock_search.json.return_value = {"status": "ok", 'checks': {'search': {'test': 'check'}}}

        mock_metadata = MagicMock()
        mock_metadata.status_code = HTTPStatus.OK
        mock_metadata.json.return_value = {"status": "ok", 'checks': {'metadata': {'test': 'check'}}}

        mock_search_health.return_value = mock_search
        mock_metadata_health.return_value = mock_metadata

        with local_app.test_client() as test:
            expected = {
                "status": "ok",
                "checks": {
                    "search_service": {'search': {'test': 'check'}},
                    'metadata_service': {'metadata': {'test': 'check'}}
                }
            }
            actual = test.get(self.healthcheck_endpoint)

            # actual = run_healthcheck()
            json_resp = json.loads(actual.get_data())
            self.assertDictEqual(json_resp, expected)

    @patch('amundsen_application.api.healthcheck.request_search', autospec=True)
    @patch('amundsen_application.api.healthcheck.request_metadata', autospec=True)
    def test_healthcheck_search_unreachable(
        self,
        mock_metadata_health: MagicMock,
        mock_search_health: MagicMock
    ) -> None:
        """
        Test request failure if 'term' is not provided in the request json
        :return:
        """
        mock_search = MagicMock()
        mock_search.status_code = HTTPStatus.SERVICE_UNAVAILABLE

        mock_metadata = MagicMock()
        mock_metadata.status_code = HTTPStatus.OK
        mock_metadata.json.return_value = {"status": "ok", 'checks': {'metadata': {'test': 'check'}}}

        mock_search_health.return_value = mock_search
        mock_metadata_health.return_value = mock_metadata

        with local_app.test_client() as test:
            expected = {
                "status": "fail",
                "checks": {
                    'search_service': {'status': 'Unable to connect.'},
                    'metadata_service': {'metadata': {'test': 'check'}}
                }
            }
            actual = test.get(self.healthcheck_endpoint)

            # actual = run_healthcheck()
            json_resp = json.loads(actual.get_data())
            self.maxDiff = None
            self.assertDictEqual(json_resp, expected)

    @patch('amundsen_application.api.healthcheck.request_search', autospec=True)
    @patch('amundsen_application.api.healthcheck.request_metadata', autospec=True)
    def test_healthcheck_search_fail(
        self,
        mock_metadata_health: MagicMock,
        mock_search_health: MagicMock
    ) -> None:
        """
        Test request failure if 'term' is not provided in the request json
        :return:
        """
        mock_search = MagicMock()
        mock_search.status_code = HTTPStatus.OK
        mock_search.json.return_value = {"status": "fail", 'checks': {'search': {'some': 'failure'}}}

        mock_metadata = MagicMock()
        mock_metadata.status_code = HTTPStatus.OK
        mock_metadata.json.return_value = {"status": "ok", 'checks': {'metadata': {'test': 'check'}}}

        mock_search_health.return_value = mock_search
        mock_metadata_health.return_value = mock_metadata

        with local_app.test_client() as test:
            expected = {
                "status": "fail",
                "checks": {
                    'search_service': {'search': {'some': 'failure'}},
                    'metadata_service': {'metadata': {'test': 'check'}}
                }
            }
            actual = test.get(self.healthcheck_endpoint)

            json_resp = json.loads(actual.get_data())
            self.maxDiff = None
            self.assertDictEqual(json_resp, expected)

    @patch('amundsen_application.api.healthcheck.request_search', autospec=True)
    @patch('amundsen_application.api.healthcheck.request_metadata', autospec=True)
    def test_healthcheck_metadata_unreachable(
        self,
        mock_metadata_health: MagicMock,
        mock_search_health: MagicMock
    ) -> None:
        """
        Test request failure if 'term' is not provided in the request json
        :return:
        """
        mock_search = MagicMock()
        mock_search.status_code = HTTPStatus.OK
        mock_search.json.return_value = {"status": "ok", 'checks': {'search': {'test': 'check'}}}

        mock_metadata = MagicMock()
        mock_metadata.status_code = HTTPStatus.SERVICE_UNAVAILABLE

        mock_search_health.return_value = mock_search
        mock_metadata_health.return_value = mock_metadata

        with local_app.test_client() as test:
            expected = {
                "status": "fail",
                "checks": {
                    'search_service': {'search': {'test': 'check'}},
                    'metadata_service': {'status': 'Unable to connect.'}
                }
            }
            actual = test.get(self.healthcheck_endpoint)
            json_resp = json.loads(actual.get_data())
            self.maxDiff = None
            self.assertDictEqual(json_resp, expected)

    @patch('amundsen_application.api.healthcheck.request_search', autospec=True)
    @patch('amundsen_application.api.healthcheck.request_metadata', autospec=True)
    def test_healthcheck_metadata_fail(
        self,
        mock_metadata_health: MagicMock,
        mock_search_health: MagicMock
    ) -> None:
        """
        Test request failure if 'term' is not provided in the request json
        :return:
        """
        mock_search = MagicMock()
        mock_search.status_code = HTTPStatus.OK
        mock_search.json.return_value = {"status": "ok", 'checks': {'search': {'test': 'check'}}}

        mock_metadata = MagicMock()
        mock_metadata.status_code = HTTPStatus.OK
        mock_metadata.json.return_value = {"status": "fail", 'checks': {'metadata': {'some': 'failure'}}}

        mock_search_health.return_value = mock_search
        mock_metadata_health.return_value = mock_metadata

        with local_app.test_client() as test:
            expected = {
                "status": "fail",
                "checks": {
                    'search_service': {'search': {'test': 'check'}},
                    'metadata_service': {'metadata': {'some': 'failure'}}
                }
            }
            actual = test.get(self.healthcheck_endpoint)
            json_resp = json.loads(actual.get_data())
            self.maxDiff = None
            self.assertDictEqual(json_resp, expected)
