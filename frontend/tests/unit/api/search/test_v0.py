# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import json
from typing import Dict
import responses
import unittest

from http import HTTPStatus
from unittest.mock import Mock, patch

from amundsen_application import create_app
from amundsen_application.api.search.v0 import SEARCH_DASHBOARD_ENDPOINT, SEARCH_DASHBOARD_FILTER_ENDPOINT, \
    SEARCH_TABLE_ENDPOINT, SEARCH_TABLE_FILTER_ENDPOINT, SEARCH_USER_ENDPOINT

local_app = create_app('amundsen_application.config.TestConfig', 'tests/templates')

MOCK_TABLE_RESULTS = {
    'total_results': 1,
    'results': [
        {
            'cluster': 'test_cluster',
            'column_names': [
                'column_1',
                'column_2',
                'column_3'
            ],
            'database': 'test_db',
            'description': 'This is a test',
            'key': 'test_key',
            'last_updated_timestamp': 1527283287,
            'name': 'test_table',
            'schema': 'test_schema',
            'schema_description': 'test_schema_description',
            'tags': [],
            'badges': []
        }
    ]
}

MOCK_PARSED_TABLE_RESULTS = [
    {
        'type': 'table',
        'cluster': 'test_cluster',
        'database': 'test_db',
        'description': 'This is a test',
        'key': 'test_key',
        'last_updated_timestamp': 1527283287,
        'name': 'test_table',
        'schema': 'test_schema',
        'schema_description': 'test_schema_description',
        'badges': []
    }
]


class SearchTable(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_table_results = MOCK_TABLE_RESULTS
        self.expected_parsed_table_results = MOCK_PARSED_TABLE_RESULTS
        self.search_service_url = local_app.config['SEARCHSERVICE_BASE'] + SEARCH_TABLE_ENDPOINT
        self.search_service_filter_url = local_app.config['SEARCHSERVICE_BASE'] + SEARCH_TABLE_FILTER_ENDPOINT
        self.fe_flask_endpoint = '/api/search/v0/table'

    def test_fail_if_term_is_none(self) -> None:
        """
        Test request failure if 'term' is not provided in the request json
        :return:
        """
        with local_app.test_client() as test:
            response = test.post(self.fe_flask_endpoint, json={'pageIndex': 0})
            self.assertEqual(response.status_code, HTTPStatus.INTERNAL_SERVER_ERROR)

    def test_fail_if_page_index_is_none(self) -> None:
        """
        Test request failure if 'pageIndex' is not provided in the request json
        :return:
        """
        with local_app.test_client() as test:
            response = test.post(self.fe_flask_endpoint, json={'term': ''})
            self.assertEqual(response.status_code, HTTPStatus.INTERNAL_SERVER_ERROR)

    @responses.activate
    @patch('amundsen_application.api.search.v0.transform_filters')
    def test_calls_transform_filters(self, transform_filter_mock: Mock) -> None:
        """
        Test transform_filters is called with the filters from the request json
        from the request_json
        :return:
        """
        test_filters = {'schema': 'test_schema'}
        responses.add(responses.POST,
                      self.search_service_filter_url,
                      json=self.mock_table_results,
                      status=HTTPStatus.OK)

        with local_app.test_client() as test:
            test.post(self.fe_flask_endpoint,
                      json={
                          'term': 'hello',
                          'pageIndex': 1,
                          'filters': test_filters,
                          'searchType': 'test'})
            transform_filter_mock.assert_called_with(filters=test_filters, resource='table')

    @responses.activate
    @patch('amundsen_application.api.search.v0.transform_filters')
    @patch('amundsen_application.api.search.v0._search_table')
    def test_calls_search_table_log_helper(self, search_table_mock: Mock, transform_filter_mock: Mock) -> None:
        """
        Test _search_table helper method is called with correct arguments for logging
        from the request_json
        :return:
        """
        test_term = 'hello'
        test_index = 1
        test_search_type = 'test'
        mock_filters = {'schema': ['test_schema']}
        transform_filter_mock.return_value = mock_filters
        responses.add(responses.POST,
                      self.search_service_filter_url,
                      json=self.mock_table_results,
                      status=HTTPStatus.OK)

        with local_app.test_client() as test:
            test.post(self.fe_flask_endpoint,
                      json={
                          'term': test_term,
                          'pageIndex': test_index,
                          'filters': {},
                          'searchType': test_search_type})
            search_table_mock.assert_called_with(filters=mock_filters,
                                                 page_index=test_index,
                                                 search_term=test_term,
                                                 search_type=test_search_type)

    @responses.activate
    @patch('amundsen_application.api.search.v0.transform_filters')
    @patch('amundsen_application.api.search.v0.has_filters')
    @patch('amundsen_application.api.search.v0.generate_query_json')
    def test_calls_generate_query_json(self,
                                       mock_generate_query_json: Mock,
                                       has_filters_mock: Mock,
                                       transform_filter_mock: Mock
                                       ) -> None:
        """
        Test generate_query_json helper method is called with correct arguments
        from the request_json if filters exist
        :return:
        """
        test_term = 'hello'
        test_index = 1
        responses.add(responses.POST,
                      self.search_service_filter_url,
                      json=self.mock_table_results,
                      status=HTTPStatus.OK)
        has_filters_mock.return_value = True
        mock_filters = {'schema': ['test_schema']}
        transform_filter_mock.return_value = mock_filters

        with local_app.test_client() as test:
            test.post(self.fe_flask_endpoint,
                      json={'term': test_term, 'pageIndex': test_index, 'filters': {}})
            mock_generate_query_json.assert_called_with(filters=mock_filters,
                                                        page_index=test_index,
                                                        search_term=test_term)

    @responses.activate
    @patch('amundsen_application.api.search.v0.has_filters')
    @patch('amundsen_application.api.search.v0.generate_query_json')
    def test_does_not_calls_generate_query_json(self, mock_generate_query_json: Mock, has_filters_mock: Mock) -> None:
        """
        Test generate_query_json helper method is not called if filters do not exist
        :return:
        """
        test_term = 'hello'
        test_index = 1
        responses.add(responses.GET, self.search_service_url, json=self.mock_table_results, status=HTTPStatus.OK)
        has_filters_mock.return_value = False

        with local_app.test_client() as test:
            test.post(self.fe_flask_endpoint, json={'term': test_term, 'pageIndex': test_index, 'filters': {}})
            mock_generate_query_json.assert_not_called()

    @responses.activate
    def test_request_success(self) -> None:
        """
        Test that the response contains the expected data and status code on success
        :return:
        """
        test_filters = {'schema': 'test_schema'}
        test_term = 'hello'
        test_index = 1
        responses.add(responses.POST,
                      self.search_service_filter_url,
                      json=self.mock_table_results,
                      status=HTTPStatus.OK)

        with local_app.test_client() as test:
            response = test.post(self.fe_flask_endpoint,
                                 json={'term': test_term, 'pageIndex': test_index, 'filters': test_filters})
            data = json.loads(response.data)
            self.assertEqual(response.status_code, HTTPStatus.OK)

            results = data.get('tables')
            self.assertEqual(results.get('total_results'), self.mock_table_results.get('total_results'))
            self.assertEqual(results.get('results'), self.expected_parsed_table_results)

    @responses.activate
    def test_request_fail(self) -> None:
        """
        Test that the response containes the failure status code from the search service on failure
        :return:
        """
        test_filters = {'schema': 'test_schema'}
        test_term = 'hello'
        test_index = 1
        responses.add(responses.POST, self.search_service_filter_url, json={}, status=HTTPStatus.BAD_REQUEST)

        with local_app.test_client() as test:
            response = test.post(self.fe_flask_endpoint,
                                 json={'term': test_term, 'pageIndex': test_index, 'filters': test_filters})
            data = json.loads(response.data)
            self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)
            self.assertEqual(data.get('msg'), 'Encountered error: Search request failed')


class SearchUser(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_search_user_results = {
            'total_results': 1,
            'results': [
                {
                    'name': 'First Last',
                    'first_name': 'First',
                    'last_name': 'Last',
                    'team_name': 'Team Name',
                    'email': 'email@email.com',
                    'manager_email': 'manager@email.com',
                    'github_username': '',
                    'is_active': True,
                    'employee_type': 'teamMember',
                    'role_name': 'SWE',
                }
            ]
        }
        self.expected_parsed_search_user_results = [
            {
                'display_name': 'First Last',
                'email': 'email@email.com',
                'employee_type': 'teamMember',
                'first_name': 'First',
                'full_name': 'First Last',
                'github_username': '',
                'is_active': True,
                'last_name': 'Last',
                'manager_email': 'manager@email.com',
                'manager_id': None,
                'manager_fullname': None,
                'profile_url': '',
                'role_name': 'SWE',
                'slack_id': None,
                'team_name': 'Team Name',
                'type': 'user',
                'user_id': 'email@email.com'
            }
        ]
        self.bad_search_results = {
            'total_results': 1,
            'results': 'Bad results to trigger exception'
        }
        self.fe_flask_endpoint = '/api/search/v0/user'

    def test_search_user_fail_if_no_query(self) -> None:
        """
        Test request failure if 'query' is not provided in the query string
        to the search endpoint
        :return:
        """
        with local_app.test_client() as test:
            response = test.get(self.fe_flask_endpoint, query_string=dict(page_index='0'))
            self.assertEqual(response.status_code, HTTPStatus.INTERNAL_SERVER_ERROR)

    def test_search_user_fail_if_no_page_index(self) -> None:
        """
        Test request failure if 'page_index' is not provided in the query string
        to the search endpoint
        :return:
        """
        with local_app.test_client() as test:
            response = test.get(self.fe_flask_endpoint, query_string=dict(query='test'))
            self.assertEqual(response.status_code, HTTPStatus.INTERNAL_SERVER_ERROR)

    @responses.activate
    def test_search_user_success_if_no_response_from_search(self) -> None:
        """
        Test request success
        :return:
        """
        responses.add(responses.GET, local_app.config['SEARCHSERVICE_BASE'] + SEARCH_USER_ENDPOINT,
                      json={}, status=HTTPStatus.OK)

        with local_app.test_client() as test:
            response = test.get(self.fe_flask_endpoint, query_string=dict(query='test', page_index='0'))
            data = json.loads(response.data)
            self.assertEqual(response.status_code, HTTPStatus.OK)

            users = data.get('users')
            self.assertEqual(len(users.get('results')), 0)
            self.assertEqual(users.get('total_results'), 0)

    @responses.activate
    def test_search_user_success(self) -> None:
        """
        Test request success
        :return:
        """
        responses.add(responses.GET, local_app.config['SEARCHSERVICE_BASE'] + SEARCH_USER_ENDPOINT,
                      json=self.mock_search_user_results, status=HTTPStatus.OK)

        with local_app.test_client() as test:
            response = test.get(self.fe_flask_endpoint, query_string=dict(query='test', page_index='0'))
            data = json.loads(response.data)
            self.assertEqual(response.status_code, HTTPStatus.OK)

            users = data.get('users')
            self.assertEqual(users.get('total_results'), self.mock_search_user_results.get('total_results'))

    @responses.activate
    def test_search_user_fail_on_non_200_response(self) -> None:
        """
        Test request failure if search endpoint returns non-200 http code
        :return:
        """
        responses.add(responses.GET, local_app.config['SEARCHSERVICE_BASE'] + SEARCH_USER_ENDPOINT,
                      json=self.mock_search_user_results, status=HTTPStatus.INTERNAL_SERVER_ERROR)

        with local_app.test_client() as test:
            response = test.get(self.fe_flask_endpoint, query_string=dict(query='test', page_index='0'))
            self.assertEqual(response.status_code, HTTPStatus.INTERNAL_SERVER_ERROR)


class SearchDashboard(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_results = {
            'total_results': 2,
            'results': [
                {
                    'group_name': 'Amundsen Team',
                    'group_url': 'product_dashboard://cluster.group',
                    'name': 'Amundsen Metrics Dashboard',
                    'product': 'mode',
                    'description': 'I am a dashboard',
                    'uri': 'product_dashboard://cluster.group/name',
                    'url': 'product/name',
                    'cluster': 'cluster',
                    'last_successful_run_timestamp': 1585062593,
                    'total_usage': 1
                },
                {
                    'group_name': 'Amundsen Team',
                    'group_url': 'product_dashboard://cluster.group',
                    'name': 'Amundsen Metrics Dashboard1',
                    'product': 'mode',
                    'description': 'I am a second dashboard',
                    'uri': 'product_dashboard://cluster.group/name2',
                    'url': 'product/name',
                    'cluster': 'cluster',
                    'last_successful_run_timestamp': 1585062593,
                    'total_usage': 1
                },
            ]
        }
        self.expected_parsed_results = [
            {
                'chart_names': [],
                'cluster': 'cluster',
                'description': 'I am a dashboard',
                'group_name': 'Amundsen Team',
                'group_url': 'product_dashboard://cluster.group',
                'last_successful_run_timestamp': 1585062593,
                'name': 'Amundsen Metrics Dashboard',
                'product': 'mode',
                'type': 'dashboard',
                'uri': 'product_dashboard://cluster.group/name',
                'key': 'product_dashboard://cluster.group/name',
                'url': 'product/name'
            },
            {
                'chart_names': [],
                'cluster': 'cluster',
                'description': 'I am a second dashboard',
                'group_name': 'Amundsen Team',
                'group_url': 'product_dashboard://cluster.group',
                'last_successful_run_timestamp': 1585062593,
                'name': 'Amundsen Metrics Dashboard1',
                'product': 'mode',
                'type': 'dashboard',
                'uri': 'product_dashboard://cluster.group/name2',
                'key': 'product_dashboard://cluster.group/name2',
                'url': 'product/name'
            },
        ]
        self.search_service_url = local_app.config['SEARCHSERVICE_BASE'] + SEARCH_DASHBOARD_ENDPOINT
        self.search_service_filter_url = local_app.config['SEARCHSERVICE_BASE'] + SEARCH_DASHBOARD_FILTER_ENDPOINT
        self.fe_flask_endpoint = '/api/search/v0/dashboard'

    def test_fail_if_term_is_none(self) -> None:
        """
        Test request failure if 'query' is not provided in the query string
        :return:
        """
        with local_app.test_client() as test:
            response = test.post(self.fe_flask_endpoint, json={'pageIndex': '0'})
            self.assertEqual(response.status_code, HTTPStatus.INTERNAL_SERVER_ERROR)

    def test_fail_if_page_index_is_none(self) -> None:
        """
        Test request failure if 'page_index' is not provided in the query string
        :return:
        """
        with local_app.test_client() as test:
            response = test.post(self.fe_flask_endpoint, json={'term': 'test'})
            self.assertEqual(response.status_code, HTTPStatus.INTERNAL_SERVER_ERROR)

    @responses.activate
    @patch('amundsen_application.api.search.v0.transform_filters')
    def test_calls_transform_filters(self, transform_filter_mock: Mock) -> None:
        """
        Test transform_filters is called with the filters from the request json
        from the request_json
        :return:
        """
        test_filters: Dict = {}
        responses.add(responses.POST,
                      self.search_service_url,
                      json=self.mock_results,
                      status=HTTPStatus.OK)

        with local_app.test_client() as test:
            test.post(self.fe_flask_endpoint,
                      json={
                          'term': 'hello',
                          'pageIndex': 1,
                          'filters': test_filters,
                          'searchType': 'test'})
            transform_filter_mock.assert_called_with(filters=test_filters, resource='dashboard')

    @responses.activate
    @patch('amundsen_application.api.search.v0._search_dashboard')
    def test_calls_search_dashboard_log_helper(self, search_dashboard_mock: Mock) -> None:
        """
        Test _search_dashboard helper method is called wwith correct arguments for logging
        from the request_json
        :return:
        """
        test_term = 'hello'
        test_index = 1
        test_search_type = 'test'
        mock_filters: Dict = {}
        responses.add(responses.GET,
                      self.search_service_url,
                      body=self.mock_results,
                      status=HTTPStatus.OK)

        with local_app.test_client() as test:
            test.post(self.fe_flask_endpoint,
                      json={
                          'term': test_term,
                          'pageIndex': test_index,
                          'filters': mock_filters,
                          'searchType': test_search_type})
            search_dashboard_mock.assert_called_with(filters=mock_filters,
                                                     page_index=test_index,
                                                     search_term=test_term,
                                                     search_type=test_search_type)

    @responses.activate
    @patch('amundsen_application.api.search.v0.transform_filters')
    @patch('amundsen_application.api.search.v0.has_filters')
    @patch('amundsen_application.api.search.v0.generate_query_json')
    def test_calls_generate_query_json(self,
                                       mock_generate_query_json: Mock,
                                       has_filters_mock: Mock,
                                       transform_filter_mock: Mock
                                       ) -> None:
        """
        Test generate_query_json helper method is called with correct arguments
        from the request_json if filters exist
        :return:
        """
        test_term = 'hello'
        test_index = 1
        responses.add(responses.POST,
                      self.search_service_filter_url,
                      json=self.mock_results,
                      status=HTTPStatus.OK)
        has_filters_mock.return_value = True
        mock_filters = {'group_name': 'test'}
        transform_filter_mock.return_value = mock_filters

        with local_app.test_client() as test:
            test.post(self.fe_flask_endpoint,
                      json={'term': test_term, 'pageIndex': test_index, 'filters': {}})
            mock_generate_query_json.assert_called_with(filters=mock_filters,
                                                        page_index=test_index,
                                                        search_term=test_term)

    @responses.activate
    @patch('amundsen_application.api.search.v0.has_filters')
    @patch('amundsen_application.api.search.v0.generate_query_json')
    def test_does_not_calls_generate_query_json(self, mock_generate_query_json: Mock, has_filters_mock: Mock) -> None:
        """
        Test generate_query_json helper method is not called if filters do not exist
        :return:
        """
        test_term = 'hello'
        test_index = 1
        responses.add(responses.GET, self.search_service_url, json=self.mock_results, status=HTTPStatus.OK)
        has_filters_mock.return_value = False

        with local_app.test_client() as test:
            test.post(self.fe_flask_endpoint, json={'term': test_term, 'pageIndex': test_index, 'filters': {}})
            mock_generate_query_json.assert_not_called()

    @responses.activate
    def test_request_success(self) -> None:
        """
        Test that the response contains the expected data and status code on success
        :return:
        """
        responses.add(responses.GET,
                      self.search_service_url,
                      json=self.mock_results,
                      status=HTTPStatus.OK)

        with local_app.test_client() as test:
            response = test.post(self.fe_flask_endpoint,
                                 json={'term': 'hello', 'pageIndex': '0'})
            data = json.loads(response.data)
            self.assertEqual(response.status_code, HTTPStatus.OK)

            results = data.get('dashboards')
            print(results.get('results'))
            self.assertEqual(results.get('total_results'), self.mock_results.get('total_results'))
            self.assertEqual(results.get('results'), self.expected_parsed_results)

    @responses.activate
    def test_request_fail(self) -> None:
        """
        Test that the response containes the failure status code from the search service on failure
        :return:
        """
        responses.add(responses.GET,
                      self.search_service_url,
                      json=self.mock_results,
                      status=HTTPStatus.BAD_REQUEST)

        with local_app.test_client() as test:
            response = test.post(self.fe_flask_endpoint,
                                 json={'term': 'hello', 'pageIndex': '1'})
            data = json.loads(response.data)
            self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)
            self.assertEqual(data.get('msg'), 'Encountered error: Search request failed')
