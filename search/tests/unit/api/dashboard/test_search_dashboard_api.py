# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from http import HTTPStatus
from unittest import TestCase

from mock import Mock, patch

from search_service import create_app
from search_service.models.search_result import SearchResult
from tests.unit.api.dashboard.fixtures import mock_json_response, mock_proxy_results


class TestSearchDashboardAPI(TestCase):
    def setUp(self) -> None:
        self.app = create_app(config_module_class='search_service.config.Config')
        self.app_context = self.app.app_context()
        self.app_context.push()

        self.mock_client = patch('search_service.api.dashboard.get_proxy_client')
        self.mock_proxy = self.mock_client.start().return_value = Mock()

    def tear_down(self) -> None:
        self.app_context.pop()
        self.mock_client.stop()

    def test_should_get_result_for_search(self) -> None:
        result = mock_proxy_results()
        self.mock_proxy.fetch_dashboard_search_results.return_value = SearchResult(total_results=1, results=[result])

        response = self.app.test_client().get('/search_dashboard?query_term=searchterm')
        expected_response = {
            "total_results": 1,
            "results": [mock_json_response()]
        }

        self.assertEqual(response.json, expected_response)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.mock_proxy.fetch_dashboard_search_results.assert_called_with(query_term='searchterm', page_index=0,
                                                                          index='dashboard_search_index')

    def test_should_give_empty_result_when_there_are_no_results_from_proxy(self) -> None:
        self.mock_proxy.fetch_dashboard_search_results.return_value = \
            SearchResult(total_results=0, results=[])

        response = self.app.test_client().get('/search_dashboard?query_term=searchterm')

        expected_response = {
            "total_results": 0,
            "results": []
        }
        self.assertEqual(response.json, expected_response)

    def test_should_fail_without_query_term(self) -> None:
        response = self.app.test_client().get('/search_dashboard')

        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)

    def test_should_fail_when_proxy_fails(self) -> None:
        self.mock_proxy.fetch_dashboard_search_results.side_effect = RuntimeError('search failed')

        response = self.app.test_client().get('/search_dashboard?query_term=searchterm')

        self.assertEqual(response.status_code, HTTPStatus.INTERNAL_SERVER_ERROR)
