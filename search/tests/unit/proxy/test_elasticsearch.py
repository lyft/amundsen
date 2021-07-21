# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import unittest
from typing import (  # noqa: F401
    Any, Iterable, List,
)
from unittest.mock import MagicMock, patch

from elasticsearch_dsl import Search

from search_service import create_app
from search_service.api.feature import FEATURE_INDEX
from search_service.api.table import TABLE_INDEX
from search_service.api.user import USER_INDEX
from search_service.models.dashboard import Dashboard
from search_service.models.feature import Feature, SearchFeatureResult
from search_service.models.search_result import SearchResult
from search_service.models.table import Table
from search_service.models.tag import Tag
from search_service.models.user import User
from search_service.proxy import get_proxy_client
from search_service.proxy.elasticsearch import ElasticsearchProxy


class MockSearchResult:
    def __init__(self, *,
                 name: str,
                 key: str,
                 description: str,
                 cluster: str,
                 database: str,
                 schema: str,
                 column_names: Iterable[str],
                 tags: Iterable[Tag],
                 badges: Iterable[Tag],
                 last_updated_timestamp: int,
                 programmatic_descriptions: List[str] = None) -> None:
        self.name = name
        self.key = key
        self.description = description
        self.cluster = cluster
        self.database = database
        self.schema = schema
        self.column_names = column_names
        self.tags = tags
        self.badges = badges
        self.last_updated_timestamp = last_updated_timestamp
        self.programmatic_descriptions = programmatic_descriptions


class MockUserSearchResult:
    def __init__(self, *,
                 first_name: str,
                 last_name: str,
                 full_name: str,
                 team_name: str,
                 email: str,
                 manager_email: str,
                 github_username: str,
                 is_active: bool,
                 employee_type: str,
                 role_name: str,
                 new_attr: str) -> None:
        self.full_name = full_name
        self.first_name = first_name
        self.last_name = last_name
        self.team_name = team_name
        self.email = email
        self.manager_email = manager_email
        self.github_username = github_username
        self.is_active = is_active
        self.employee_type = employee_type
        self.new_attr = new_attr
        self.role_name = role_name


class Response:
    def __init__(self,
                 result: Any):
        self._d_ = result


class TableResponse:
    def __init__(self,
                 result: Any):
        self._d_ = result
        self.meta = {'id': result['key']}


class UserResponse:
    def __init__(self,
                 result: Any):
        self._d_ = result
        self.meta = {'id': result['email']}


class TestElasticsearchProxy(unittest.TestCase):

    def setUp(self) -> None:
        self.app = create_app(config_module_class='search_service.config.LocalConfig')
        self.app_context = self.app.app_context()
        self.app_context.push()

        mock_elasticsearch_client = MagicMock()
        self.es_proxy = ElasticsearchProxy(client=mock_elasticsearch_client)
        self.mock_badge = Tag(tag_name='name')
        self.mock_tag = Tag(tag_name='match')
        self.mock_empty_badge = []  # type: List[Tag]
        self.mock_empty_tag = []  # type: List[Tag]
        self.mock_result1 = MockSearchResult(name='test_table',
                                             key='test_key',
                                             description='test_description',
                                             cluster='gold',
                                             database='test_db',
                                             schema='test_schema',
                                             column_names=['test_col1', 'test_col2'],
                                             tags=self.mock_empty_tag,
                                             badges=self.mock_empty_badge,
                                             last_updated_timestamp=1527283287,
                                             programmatic_descriptions=[])

        self.mock_result2 = MockSearchResult(name='test_table2',
                                             key='test_key2',
                                             description='test_description2',
                                             cluster='gold',
                                             database='test_db2',
                                             schema='test_schema2',
                                             column_names=['test_col1', 'test_col2'],
                                             tags=self.mock_empty_tag,
                                             badges=self.mock_empty_badge,
                                             last_updated_timestamp=1527283287)

        self.mock_result3 = Table(id='test_key3',
                                  name='test_table3',
                                  key='test_key3',
                                  description='test_description3',
                                  cluster='gold',
                                  database='test_db3',
                                  schema='test_schema3',
                                  column_names=['test_col1', 'test_col2'],
                                  tags=[self.mock_tag],
                                  badges=[self.mock_badge],
                                  last_updated_timestamp=1527283287)

        self.mock_result4 = MockUserSearchResult(full_name='First Last',
                                                 first_name='First',
                                                 last_name='Last',
                                                 team_name='Test team',
                                                 email='test@email.com',
                                                 github_username='ghub',
                                                 manager_email='manager@email.com',
                                                 is_active=True,
                                                 employee_type='FTE',
                                                 role_name='swe',
                                                 new_attr='aaa')

    def test_setup_client(self) -> None:
        self.es_proxy = ElasticsearchProxy(
            host="http://0.0.0.0:9200",
            user="elastic",
            password="elastic"
        )
        a = self.es_proxy.elasticsearch
        for client in [a, a.cat, a.cluster, a.indices, a.ingest, a.nodes, a.snapshot, a.tasks]:
            self.assertEqual(client.transport.hosts[0]['host'], "0.0.0.0")
            self.assertEqual(client.transport.hosts[0]['port'], 9200)

    @patch('search_service.proxy.elasticsearch.Elasticsearch', autospec=True)
    def test_setup_client_with_username_and_password(self, elasticsearch_mock: MagicMock) -> None:
        self.es_proxy = ElasticsearchProxy(
            host='http://unit-test-host',
            user='unit-test-user',
            password='unit-test-pass'
        )

        elasticsearch_mock.assert_called_once()
        elasticsearch_mock.assert_called_once_with(
            'http://unit-test-host',
            http_auth=('unit-test-user', 'unit-test-pass')
        )

    @patch('search_service.proxy.elasticsearch.Elasticsearch', autospec=True)
    def test_setup_client_without_username(self, elasticsearch_mock: MagicMock) -> None:
        self.es_proxy = ElasticsearchProxy(
            host='http://unit-test-host',
            user=''
        )

        elasticsearch_mock.assert_called_once()
        elasticsearch_mock.assert_called_once_with('http://unit-test-host', http_auth=None)

    @patch('search_service.proxy._proxy_client', None)
    def test_setup_config(self) -> None:
        es: Any = get_proxy_client()
        a = es.elasticsearch
        for client in [a, a.cat, a.cluster, a.indices, a.ingest, a.nodes, a.snapshot, a.tasks]:
            self.assertEqual(client.transport.hosts[0]['host'], "0.0.0.0")
            self.assertEqual(client.transport.hosts[0]['port'], 9200)

    @patch('elasticsearch_dsl.Search.execute')
    def test_search_with_empty_query_string(self, mock_search: MagicMock) -> None:

        expected = SearchResult(total_results=0, results=[])
        result = self.es_proxy.fetch_table_search_results(query_term='')

        # check the output was empty list
        self.assertDictEqual(vars(result), vars(expected),
                             "Received non-empty search results!")

        # ensure elasticsearch_dsl Search endpoint was not called
        # assert_not_called doesn't work. See here: http://engineroom.trackmaven.com/blog/mocking-mistakes/
        self.assertTrue(mock_search.call_count == 0)

    @patch('elasticsearch_dsl.Search.execute')
    def test_search_with_empty_result(self,
                                      mock_search: MagicMock) -> None:

        mock_results = MagicMock()
        mock_results.hits.total = 0
        mock_search.return_value = mock_results

        expected = SearchResult(total_results=0, results=[])
        result = self.es_proxy.fetch_table_search_results(query_term='test_query_term')
        self.assertDictEqual(vars(result), vars(expected),
                             "Received non-empty search results!")

    @patch('elasticsearch_dsl.Search.execute')
    def test_search_with_one_table_result(self,
                                          mock_search: MagicMock) -> None:

        mock_results = MagicMock()
        mock_results.hits.total = 1
        mock_results.__iter__.return_value = [TableResponse(result=vars(self.mock_result1))]
        mock_search.return_value = mock_results

        expected = SearchResult(total_results=1,
                                results=[Table(id='test_key',
                                               name='test_table',
                                               key='test_key',
                                               description='test_description',
                                               cluster='gold',
                                               database='test_db',
                                               schema='test_schema',
                                               column_names=['test_col1', 'test_col2'],
                                               tags=[],
                                               badges=self.mock_empty_badge,
                                               last_updated_timestamp=1527283287,
                                               programmatic_descriptions=[])])

        resp = self.es_proxy.fetch_table_search_results(query_term='test_query_term')

        self.assertEqual(resp.total_results, expected.total_results,
                         "search result is not of length 1")
        self.assertIsInstance(resp.results[0],
                              Table,
                              "Search result received is not of 'Table' type!")
        self.assertDictEqual(vars(resp.results[0]), vars(expected.results[0]),
                             "Search Result doesn't match with expected result!")

    @patch('elasticsearch_dsl.Search.execute')
    def test_search_with_multiple_result(self,
                                         mock_search: MagicMock) -> None:
        mock_results = MagicMock()
        mock_results.hits.total = 2
        mock_results.__iter__.return_value = [TableResponse(result=vars(self.mock_result1)),
                                              TableResponse(result=vars(self.mock_result2))]
        mock_search.return_value = mock_results

        expected = SearchResult(total_results=2,
                                results=[Table(id='test_key',
                                               name='test_table',
                                               key='test_key',
                                               description='test_description',
                                               cluster='gold',
                                               database='test_db',
                                               schema='test_schema',
                                               column_names=['test_col1', 'test_col2'],
                                               tags=[],
                                               badges=self.mock_empty_badge,
                                               last_updated_timestamp=1527283287,
                                               programmatic_descriptions=[]),
                                         Table(id='test_key2',
                                               name='test_table2',
                                               key='test_key2',
                                               description='test_description2',
                                               cluster='gold',
                                               database='test_db2',
                                               schema='test_schema2',
                                               column_names=['test_col1', 'test_col2'],
                                               tags=[],
                                               badges=self.mock_empty_badge,
                                               last_updated_timestamp=1527283287)])

        resp = self.es_proxy.fetch_table_search_results(query_term='test_query_term')

        self.assertEqual(resp.total_results, expected.total_results,
                         "search result is not of length 2")
        for i in range(2):
            self.assertIsInstance(resp.results[i],
                                  Table,
                                  "Search result received is not of 'Table' type!")
            self.assertDictEqual(vars(resp.results[i]),
                                 vars(expected.results[i]),
                                 "Search result doesn't match with expected result!")

    @patch('elasticsearch_dsl.Search.execute')
    def test_search_table_filter(self, mock_search: MagicMock) -> None:
        mock_results = MagicMock()
        mock_results.hits.total = 1
        mock_results.__iter__.return_value = [TableResponse(result=vars(self.mock_result1))]
        mock_search.return_value = mock_results

        expected = SearchResult(total_results=1,
                                results=[Table(id='test_key',
                                               name='test_table',
                                               key='test_key',
                                               description='test_description',
                                               cluster='gold',
                                               database='test_db',
                                               schema='test_schema',
                                               column_names=['test_col1', 'test_col2'],
                                               tags=self.mock_empty_tag,
                                               badges=self.mock_empty_badge,
                                               last_updated_timestamp=1527283287,
                                               programmatic_descriptions=[])])
        search_request = {
            'type': 'AND',
            'filters': {
                'database': ['hive', 'bigquery'],
                'schema': ['test-schema1', 'test-schema2'],
                'table': ['*amundsen*'],
                'column': ['*ds*'],
                'tag': ['test-tag'],
            }
        }
        resp = self.es_proxy.fetch_search_results_with_filter(search_request=search_request, query_term='test')
        self.assertEqual(resp.total_results, expected.total_results)
        self.assertIsInstance(resp.results[0], Table)
        self.assertDictEqual(vars(resp.results[0]), vars(expected.results[0]))

    def test_search_table_filter_return_no_results_if_no_search_request(self) -> None:
        resp = self.es_proxy.fetch_search_results_with_filter(search_request=None, query_term='test')

        self.assertEqual(resp.total_results, 0)
        self.assertEqual(resp.results, [])

    def test_search_table_filter_return_no_results_if_dsl_conversion_error(self) -> None:
        search_request = {
            'type': 'AND',
            'filters': {}
        }
        with patch.object(self.es_proxy, 'convert_query_json_to_query_dsl') as mock:
            mock.side_effect = MagicMock(side_effect=Exception('Test'))
            resp = self.es_proxy.fetch_search_results_with_filter(search_request=search_request,
                                                                  query_term='test')

            self.assertEqual(resp.total_results, 0)
            self.assertEqual(resp.results, [])

    def test_get_model_by_index_table(self) -> None:
        self.assertEqual(self.es_proxy.get_model_by_index(TABLE_INDEX), Table)

    def test_get_model_by_index_user(self) -> None:
        self.assertEqual(self.es_proxy.get_model_by_index(USER_INDEX), User)

    def test_get_model_by_index_raise_exception(self) -> None:
        self.assertRaises(Exception, self.es_proxy.convert_query_json_to_query_dsl, 'some_fake_index')

    def test_parse_filters_return_results(self) -> None:
        filter_list = {
            'database': ['hive', 'bigquery'],
            'schema': ['test-schema1', 'test-schema2'],
            'table': ['*amundsen*'],
            'column': ['*ds*'],
            'tag': ['test-tag'],
        }
        expected_result = "database.raw:(hive OR bigquery) " \
                          "AND schema.raw:(test-schema1 OR test-schema2) " \
                          "AND name.raw:(*amundsen*) " \
                          "AND column_names.raw:(*ds*) " \
                          "AND tags:(test-tag)"
        self.assertEqual(self.es_proxy.parse_filters(filter_list,
                                                     index=TABLE_INDEX), expected_result)

    def test_parse_filters_return_no_results(self) -> None:
        filter_list = {
            'unsupported_category': ['fake']
        }
        self.assertEqual(self.es_proxy.parse_filters(filter_list,
                                                     index=TABLE_INDEX), '')

    def test_validate_wrong_filters_values(self) -> None:
        search_request = {
            "type": "AND",
            "filters": {
                "schema": ["test_schema:test_schema"],
                "table": ["test/table"]
            },
            "query_term": "",
            "page_index": 0
        }
        self.assertEqual(self.es_proxy.validate_filter_values(search_request), False)

    def test_validate_accepted_filters_values(self) -> None:
        search_request = {
            "type": "AND",
            "filters": {
                "schema": ["test_schema"],
                "table": ["test_table"]
            },
            "query_term": "a",
            "page_index": 0
        }
        self.assertEqual(self.es_proxy.validate_filter_values(search_request), True)

    def test_parse_query_term(self) -> None:
        term = 'test'
        expected_result = "(name:(*test*) OR name:(test) OR schema:(*test*) OR " \
                          "schema:(test) OR description:(*test*) OR description:(test) OR " \
                          "column_names:(*test*) OR column_names:(test) OR " \
                          "column_descriptions:(*test*) OR column_descriptions:(test))"
        self.assertEqual(self.es_proxy.parse_query_term(term,
                                                        index=TABLE_INDEX), expected_result)

    def test_convert_query_json_to_query_dsl_term_and_filters(self) -> None:
        term = 'test'
        test_filters = {
            'database': ['hive', 'bigquery'],
            'schema': ['test-schema1', 'test-schema2'],
            'table': ['*amundsen*'],
            'column': ['*ds*'],
            'tag': ['test-tag'],
        }
        search_request = {
            'type': 'AND',
            'filters': test_filters
        }

        expected_result = self.es_proxy.parse_filters(test_filters, index=TABLE_INDEX) + " AND " + \
            self.es_proxy.parse_query_term(term, index=TABLE_INDEX)
        ret_result = self.es_proxy.convert_query_json_to_query_dsl(search_request=search_request,
                                                                   query_term=term,
                                                                   index=TABLE_INDEX)
        self.assertEqual(ret_result, expected_result)

    def test_convert_query_json_to_query_dsl_no_term(self) -> None:
        term = ''
        test_filters = {
            'database': ['hive', 'bigquery'],
        }
        search_request = {
            'type': 'AND',
            'filters': test_filters
        }
        expected_result = self.es_proxy.parse_filters(test_filters,
                                                      index=TABLE_INDEX)
        ret_result = self.es_proxy.convert_query_json_to_query_dsl(search_request=search_request,
                                                                   query_term=term,
                                                                   index=TABLE_INDEX)
        self.assertEqual(ret_result, expected_result)

    def test_convert_query_json_to_query_dsl_no_filters(self) -> None:
        term = 'test'
        search_request = {
            'type': 'AND',
            'filters': {}
        }
        expected_result = self.es_proxy.parse_query_term(term,
                                                         index=TABLE_INDEX)
        ret_result = self.es_proxy.convert_query_json_to_query_dsl(search_request=search_request,
                                                                   query_term=term,
                                                                   index=TABLE_INDEX)
        self.assertEqual(ret_result, expected_result)

    def test_convert_query_json_to_query_dsl_raise_exception_no_term_or_filters(self) -> None:
        term = ''
        search_request = {
            'type': 'AND',
            'filters': {}
        }
        self.assertRaises(Exception, self.es_proxy.convert_query_json_to_query_dsl, search_request, term)

    @patch('elasticsearch_dsl.Search.execute')
    def test_search_with_one_user_result(self,
                                         mock_search: MagicMock) -> None:

        mock_results = MagicMock()
        mock_results.hits.total = 1
        mock_results.__iter__.return_value = [UserResponse(result=vars(self.mock_result4))]
        mock_search.return_value = mock_results

        expected = SearchResult(total_results=1,
                                results=[User(id='test@email.com',
                                              full_name='First Last',
                                              first_name='First',
                                              last_name='Last',
                                              team_name='Test team',
                                              email='test@email.com',
                                              github_username='ghub',
                                              manager_email='manager@email.com',
                                              is_active=True,
                                              role_name='swe',
                                              employee_type='FTE')])

        resp = self.es_proxy.fetch_user_search_results(query_term='test_query_term',
                                                       index='user_search_index')

        self.assertEqual(resp.total_results, expected.total_results,
                         "search result is not of length 1")
        self.assertIsInstance(resp.results[0],
                              User,
                              "Search result received is not of 'Table' type!")
        self.assertDictEqual(vars(resp.results[0]), vars(expected.results[0]),
                             "Search Result doesn't match with expected result!")

    def test_create_document_with_no_data(self) -> None:
        expected = ''
        result = self.es_proxy.create_document(data=None, index='table_search_index')
        print('result: {}'.format(result))
        self.assertEqual(expected, result)

    @patch('uuid.uuid4')
    def test_create_document(self, mock_uuid: MagicMock) -> None:
        mock_elasticsearch = self.es_proxy.elasticsearch
        new_index_name = 'tester_index_name'
        mock_uuid.return_value = new_index_name
        mock_elasticsearch.indices.get_alias.return_value = dict([(new_index_name, {})])
        start_data = [
            Table(id='snowflake://blue.test_schema/bank_accounts', cluster='blue', column_names=['1', '2'],
                  database='snowflake', schema='test_schema', description='A table for something',
                  key='snowflake://blue.test_schema/bank_accounts',
                  last_updated_timestamp=0, name='bank_accounts', tags=[], badges=self.mock_empty_badge,
                  column_descriptions=['desc'], schema_description='schema description 1'),
            Table(id='snowflake://blue.test_schema/bitcoin_wallets', cluster='blue', column_names=['5', '6'],
                  database='snowflake', schema='test_schema', description='A table for lots of things!',
                  key='snowflake://blue.test_schema/bitcoin_wallets',
                  last_updated_timestamp=0, name='bitcoin_wallets', tags=[], badges=self.mock_empty_badge,
                  schema_description='schema description 2', programmatic_descriptions=["test"])
        ]
        expected_data = [
            {
                'index': {
                    '_index': new_index_name,
                    '_type': 'table',
                    '_id': 'snowflake://blue.test_schema/bank_accounts'
                }
            },
            {
                'id': 'snowflake://blue.test_schema/bank_accounts',
                'cluster': 'blue',
                'column_names': ['1', '2'],
                'column_descriptions': ['desc'],
                'database': 'snowflake',
                'schema': 'test_schema',
                'description': 'A table for something',
                'display_name': None,
                'key': 'snowflake://blue.test_schema/bank_accounts',
                'last_updated_timestamp': 0,
                'name': 'bank_accounts',
                'tags': [],
                'badges': [],
                'total_usage': 0,
                'programmatic_descriptions': None,
                'schema_description': 'schema description 1',
            },
            {
                'index': {
                    '_index': new_index_name,
                    '_type': 'table',
                    '_id': 'snowflake://blue.test_schema/bitcoin_wallets'
                }
            },
            {
                'id': 'snowflake://blue.test_schema/bitcoin_wallets',
                'cluster': 'blue',
                'column_names': ['5', '6'],
                'column_descriptions': None,
                'database': 'snowflake',
                'schema': 'test_schema',
                'description': 'A table for lots of things!',
                'display_name': None,
                'key': 'snowflake://blue.test_schema/bitcoin_wallets',
                'last_updated_timestamp': 0,
                'name': 'bitcoin_wallets',
                'tags': [],
                'badges': [],
                'total_usage': 0,
                'schema_description': 'schema description 2',
                'programmatic_descriptions': ["test"]
            }
        ]
        mock_elasticsearch.bulk.return_value = {'errors': False}

        expected_alias = 'table_search_index'
        result = self.es_proxy.create_document(data=start_data, index=expected_alias)
        self.assertEqual(expected_alias, result)
        mock_elasticsearch.bulk.assert_called_with(expected_data)

    def test_update_document_with_no_data(self) -> None:
        expected = ''
        result = self.es_proxy.update_document(data=None, index='table_search_index')
        self.assertEqual(expected, result)

    @patch('uuid.uuid4')
    def test_update_document(self, mock_uuid: MagicMock) -> None:
        mock_elasticsearch = self.es_proxy.elasticsearch
        new_index_name = 'tester_index_name'
        mock_elasticsearch.indices.get_alias.return_value = dict([(new_index_name, {})])
        mock_uuid.return_value = new_index_name
        table_key = 'snowflake://blue.test_schema/bitcoin_wallets'
        expected_alias = 'table_search_index'
        data = [
            Table(id=table_key, cluster='blue', column_names=['5', '6'], database='snowflake',
                  schema='test_schema', description='A table for lots of things!',
                  key=table_key, last_updated_timestamp=0, name='bitcoin_wallets',
                  tags=[], column_descriptions=['hello'], badges=self.mock_empty_badge,
                  schema_description='schema description 1')
        ]
        expected_data = [
            {
                'update': {
                    '_index': new_index_name,
                    '_type': 'table',
                    '_id': table_key
                }
            },
            {
                'doc': {
                    'id': table_key,
                    'cluster': 'blue',
                    'column_names': ['5', '6'],
                    'column_descriptions': ['hello'],
                    'database': 'snowflake',
                    'schema': 'test_schema',
                    'description': 'A table for lots of things!',
                    'display_name': None,
                    'key': table_key,
                    'last_updated_timestamp': 0,
                    'name': 'bitcoin_wallets',
                    'tags': [],
                    'badges': [],
                    'total_usage': 0,
                    'programmatic_descriptions': None,
                    'schema_description': 'schema description 1',
                }
            }
        ]
        result = self.es_proxy.update_document(data=data, index=expected_alias)
        self.assertEqual(expected_alias, result)
        mock_elasticsearch.bulk.assert_called_with(expected_data)

    @patch('uuid.uuid4')
    def test_delete_table_document(self, mock_uuid: MagicMock) -> None:
        mock_elasticsearch = self.es_proxy.elasticsearch
        new_index_name = 'tester_index_name'
        mock_uuid.return_value = new_index_name
        mock_elasticsearch.indices.get_alias.return_value = dict([(new_index_name, {})])
        expected_alias = 'table_search_index'
        data = ['id1', 'id2']

        expected_data = [
            {'delete': {'_index': new_index_name, '_id': 'id1', '_type': 'table'}},
            {'delete': {'_index': new_index_name, '_id': 'id2', '_type': 'table'}}
        ]
        result = self.es_proxy.delete_document(data=data, index=expected_alias)

        self.assertEqual(expected_alias, result)
        mock_elasticsearch.bulk.assert_called_with(expected_data)

    @patch('uuid.uuid4')
    def test_delete_user_document(self, mock_uuid: MagicMock) -> None:
        mock_elasticsearch = self.es_proxy.elasticsearch
        new_index_name = 'tester_index_name'
        mock_uuid.return_value = new_index_name
        mock_elasticsearch.indices.get_alias.return_value = dict([(new_index_name, {})])
        expected_alias = 'user_search_index'
        data = ['id1', 'id2']

        expected_data = [
            {'delete': {'_index': new_index_name, '_id': 'id1', '_type': 'user'}},
            {'delete': {'_index': new_index_name, '_id': 'id2', '_type': 'user'}}
        ]
        result = self.es_proxy.delete_document(data=data, index=expected_alias)

        self.assertEqual(expected_alias, result)
        mock_elasticsearch.bulk.assert_called_with(expected_data)

    @patch('uuid.uuid4')
    def test_delete_feature_document(self, mock_uuid: MagicMock) -> None:
        mock_elasticsearch = self.es_proxy.elasticsearch
        new_index_name = 'test_indx'
        mock_uuid.return_value = new_index_name
        mock_elasticsearch.indices.get_alias.return_value = dict([(new_index_name, {})])
        expected_alias = 'feature_search_index'
        data = ['id1', 'id2']

        expected_data = [
            {'delete': {'_index': new_index_name, '_id': 'id1', '_type': 'feature'}},
            {'delete': {'_index': new_index_name, '_id': 'id2', '_type': 'feature'}}
        ]
        result = self.es_proxy.delete_document(data=data, index=expected_alias)

        self.assertEqual(expected_alias, result)
        mock_elasticsearch.bulk.assert_called_with(expected_data)

    def test_get_instance_string(self) -> None:
        result = self.es_proxy._get_instance('column', 'value')
        self.assertEqual('value', result)

    def test_get_instance_tag(self) -> None:
        result = self.es_proxy._get_instance('tags', ['value'])
        tags = [Tag(tag_name='value')]
        self.assertEqual(tags, result)

    def test_get_instance_badge(self) -> None:
        result = self.es_proxy._get_instance('badges', ['badge1'])
        badges = [Tag(tag_name='badge1')]
        self.assertEqual(badges, result)

    @patch('search_service.proxy.elasticsearch.ElasticsearchProxy._search_helper')
    def test_fetch_dashboard_search_results(self, mock_search: MagicMock) -> None:
        mock_dashboard_result = Dashboard(id='mode_dashboard',
                                          uri='dashboard_uri',
                                          cluster='gold',
                                          group_name='mode_dashboard_group',
                                          group_url='mode_dashboard_group_url',
                                          product='mode',
                                          name='mode_dashboard',
                                          url='mode_dashboard_url',
                                          description='test_dashboard',
                                          last_successful_run_timestamp=1000)

        mock_search.return_value = SearchResult(total_results=1,
                                                results=[mock_dashboard_result])

        expected = SearchResult(total_results=1,
                                results=[Dashboard(id='mode_dashboard',
                                                   uri='dashboard_uri',
                                                   cluster='gold',
                                                   group_name='mode_dashboard_group',
                                                   group_url='mode_dashboard_group_url',
                                                   product='mode',
                                                   name='mode_dashboard',
                                                   url='mode_dashboard_url',
                                                   description='test_dashboard',
                                                   last_successful_run_timestamp=1000)])

        resp = self.es_proxy.fetch_dashboard_search_results(query_term='test_query_term',
                                                            page_index=0,
                                                            index='dashboard_search_index')
        self.assertEqual(resp.total_results, expected.total_results)

        self.assertDictEqual(vars(resp.results[0]),
                             vars(expected.results[0]),
                             "Search result doesn't match with expected result!")

    @patch('search_service.proxy.elasticsearch.ElasticsearchProxy._search_helper')
    def test_fetch_feature_search_results(self, mock_search: MagicMock) -> None:
        query_term = 'panda'
        self.es_proxy.fetch_feature_search_results(query_term=query_term)

        mock_search.assert_called_with(
            page_index=0,
            client=Search(using=self.es_proxy.elasticsearch, index=FEATURE_INDEX),
            query_name=self.es_proxy.get_feature_search_query(query_term),
            model=Feature,
            search_result_model=SearchFeatureResult,
        )
