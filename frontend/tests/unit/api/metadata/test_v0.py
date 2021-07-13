# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import json
import responses
import unittest
from unittest.mock import patch

from http import HTTPStatus

from amundsen_application import create_app
from amundsen_application.api.metadata.v0 import TABLE_ENDPOINT, LAST_INDEXED_ENDPOINT,\
    POPULAR_RESOURCES_ENDPOINT, TAGS_ENDPOINT, USER_ENDPOINT, DASHBOARD_ENDPOINT, FEATURE_ENDPOINT
from amundsen_application.config import MatchRuleObject

from amundsen_application.tests.test_utils import TEST_USER_ID

from amundsen_common.entity.resource_type import ResourceType, to_label

local_app = create_app('amundsen_application.config.TestConfig', 'tests/templates')


class MetadataTest(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_popular_tables = {
            ResourceType.Table.name: [
                {
                    'cluster': 'test_cluster',
                    'database': 'test_db',
                    'schema': 'test_schema',
                    'description': 'This is a test',
                    'name': 'test_table',
                    'key': 'test_db://test_cluster.test_schema/test_table',
                }
            ]
        }
        self.expected_parsed_popular_tables = [
            {
                'cluster': 'test_cluster',
                'database': 'test_db',
                'description': 'This is a test',
                'schema': 'test_schema',
                'type': 'table',
                'name': 'test_table',
                'key': 'test_db://test_cluster.test_schema/test_table',
                'last_updated_timestamp': None,
            }
        ]
        self.mock_metadata = {
            'cluster': 'test_cluster',
            'columns': [
                {
                    'name': 'column_1',
                    'description': 'This is a test',
                    'col_type': 'bigint',
                    'sort_order': 0,
                    'stats': [
                        {'stat_type': 'count', 'stat_val': '100', 'start_epoch': 1538352000, 'end_epoch': 1538352000},
                        {'stat_type': 'count_null', 'stat_val': '0', 'start_epoch': 1538352000, 'end_epoch': 1538352000}
                    ]
                }
            ],
            'database': 'test_db',
            'is_view': False,
            'key': 'test_db://test_cluster.test_schema/test_table',
            'last_updated_timestamp': 1563872712,
            'owners': [],
            'schema': 'test_schema',
            'name': 'test_table',
            'description': 'This is a test',
            'resource_reports': [],
            'programmatic_descriptions': [
                {'source': 'c_1', 'text': 'description c'},
                {'source': 'a_1', 'text': 'description a'},
                {'source': 'b_1', 'text': 'description b'}
            ],
            'tags': [],
            'table_readers': [
                {'user': {'email': 'test@test.com', 'first_name': None, 'last_name': None}, 'read_count': 100}
            ],
            'watermarks': [
                {'watermark_type': 'low_watermark', 'partition_key': 'ds', 'partition_value': '', 'create_time': ''},
                {'watermark_type': 'high_watermark', 'partition_key': 'ds', 'partition_value': '', 'create_time': ''}
            ],
            'table_writer': {
                'application_url': 'https://test-test.test.test',
                'name': 'test_name',
                'id': 'test_id',
                'description': 'This is a test'
            }
        }
        self.expected_parsed_metadata = {
            'badges': [],
            'cluster': 'test_cluster',
            'database': 'test_db',
            'schema': 'test_schema',
            'name': 'test_table',
            'key': 'test_db://test_cluster.test_schema/test_table',
            'description': 'This is a test',
            'tags': [],
            'table_readers': [
                {
                    'user': {
                        'email': 'test@test.com',
                        'first_name': None,
                        'last_name': None,
                        'display_name': 'test@test.com',
                        'profile_url': ''
                    },
                    'read_count': 100
                }
            ],
            'partition': {
                'is_partitioned': True,
                'key': 'ds',
                'value': '01-30-2019'
            },
            'owners': [],
            'is_view': False,
            'columns': [
                {
                    'name': 'column_1',
                    'description': 'This is a test',
                    'col_type': 'bigint',
                    'sort_order': 0,
                    'stats': [
                        {'stat_type': 'count', 'stat_val': '100', 'start_epoch': 1538352000, 'end_epoch': 1538352000},
                        {'stat_type': 'count_null', 'stat_val': '0', 'start_epoch': 1538352000, 'end_epoch': 1538352000}
                    ],
                    'is_editable': True
                }
            ],
            "programmatic_descriptions": [
                {
                    'source': 'a',
                    'text': 'description a'
                },
                {
                    'source': 'b',
                    'text': 'description b'
                },
                {
                    'source': 'c',
                    'text': 'description c'
                },
            ],
            'resource_reports': [],
            'table_writer': {
                'application_url': 'https://test-test.test.test',
                'name': 'test_name',
                'id': 'test_id',
                'description': 'This is a test'
            },
            'watermarks': [
                {'watermark_type': 'low_watermark', 'partition_key': 'ds', 'partition_value': '', 'create_time': ''},
                {'watermark_type': 'high_watermark', 'partition_key': 'ds', 'partition_value': '', 'create_time': ''}
            ],
            'source': '/source',
            'is_editable': True,
            'last_updated_timestamp': None,
            'common_filters': [],
            'common_joins': []
        }
        self.expected_related_dashboard_response = {
            "dashboards": [{
                "group_name": "Group Test One",
                "description": None,
                "cluster": "gold",
                "group_url": "https://app.mode.com/companyName/spaces/123",
                "uri": "mode_dashboard://gold.123/234rt78",
                "last_successful_run_timestamp": 1590505846,
                "name": "Test Dashboard One",
                "product": "mode",
                "url": "https://app.mode.com/companyName/reports/234rt78"
            }, {
                "group_name": "Group Test Two",
                "description": None,
                "cluster": "gold",
                "group_url": "https://app.mode.com/companyName/spaces/334",
                "uri": "mode_dashboard://gold.334/34thyu56",
                "last_successful_run_timestamp": 1590519704,
                "name": "Test Dashboard Two",
                "product": "mode",
                "url": "https://app.mode.com/companyName/reports/34thyu56"
            }, {
                "group_name": "Group Test Three",
                "description": None,
                "cluster": "gold",
                "group_url": "https://app.mode.com/companyName/spaces/789",
                "uri": "mode_dashboard://gold.789/12ed34",
                "last_successful_run_timestamp": 1590538191,
                "name": "Test Dashboard Three",
                "product": "mode",
                "url": "https://app.mode.com/companyName/reports/12ed34"
            }]
        }

        self.expected_programmatic_descriptions_with_config = {
            "programmatic_descriptions": [
                {
                    'source': 'a',
                    'text': 'description a'
                },
                {
                    'source': 'b',
                    'text': 'description b'
                },
                {
                    'source': 'c',
                    'text': 'description c'
                },
            ]
        }
        self.mock_tags = {
            'tag_usages': [
                {
                    'tag_count': 3,
                    'tag_name': 'tag_0'
                }, {
                    'tag_count': 4,
                    'tag_name': 'tag_1'
                }, {
                    'tag_count': 5,
                    'tag_name': 'tag_2'
                }, {
                    'tag_count': 10,
                    'tag_name': 'tag_3'
                }, {
                    'tag_count': 1,
                    'tag_name': 'tag_4'
                }
            ]
        }
        self.expected_parsed_tags = [
            {
                'tag_count': 3,
                'tag_name': 'tag_0'
            },
            {
                'tag_count': 4,
                'tag_name': 'tag_1'
            },
            {
                'tag_count': 5,
                'tag_name': 'tag_2'
            },
            {
                'tag_count': 10,
                'tag_name': 'tag_3'
            },
            {
                'tag_count': 1,
                'tag_name': 'tag_4'
            }
        ]
        self.mock_user = {
            'email': 'test@test.com',
            'employee_type': 'FTE',
            'first_name': 'Firstname',
            'full_name': 'Firstname Lastname',
            'github_username': 'githubusername',
            'is_active': True,
            'last_name': 'Lastname',
            'manager_id': 'managerid',
            'manager_fullname': 'Manager Fullname',
            'role_name': 'SWE',
            'slack_id': 'slackuserid',
            'team_name': 'Amundsen',
            'user_id': 'testuserid',
        }
        self.expected_parsed_user = {
            'display_name': 'Firstname Lastname',
            'email': 'test@test.com',
            'employee_type': 'FTE',
            'first_name': 'Firstname',
            'full_name': 'Firstname Lastname',
            'github_username': 'githubusername',
            'is_active': True,
            'last_name': 'Lastname',
            'manager_email': None,
            'manager_fullname': 'Manager Fullname',
            'manager_id': 'managerid',
            'profile_url': '',
            'role_name': 'SWE',
            'slack_id': 'slackuserid',
            'team_name': 'Amundsen',
            'user_id': 'testuserid',
        }
        self.get_user_resource_response = {
            'table': [
                {
                    'cluster': 'cluster',
                    'database': 'database',
                    'schema': 'schema',
                    'name': 'table_name_0',
                    'description': 'description',
                },
                {
                    'cluster': 'cluster',
                    'database': 'database',
                    'schema': 'schema',
                    'name': 'table_name_1',
                    'description': 'description',
                },
            ],
            'dashboard': [],
        }
        self.expected_parsed_user_resources = {
            'table': [
                {
                    'cluster': 'cluster',
                    'database': 'database',
                    'description': 'description',
                    'last_updated_timestamp': None,
                    'name': 'table_name_0',
                    'schema': 'schema',
                    'type': 'table',
                    'key': 'database://cluster.schema/table_name_0',
                },
                {
                    'cluster': 'cluster',
                    'database': 'database',
                    'description': 'description',
                    'last_updated_timestamp': None,
                    'name': 'table_name_1',
                    'schema': 'schema',
                    'type': 'table',
                    'key': 'database://cluster.schema/table_name_1',
                },
            ],
            'dashboard': [],
        }
        self.mock_feature_metadata = {
            'entity': 'rider',
            'key': 'test_feature_group/test_feature_name/1.4',
            'availability': ['hive'],
            'last_updated_timestamp': 1563872712,
            'owners': [],
            'name': 'test_feature_name',
            'description': 'This is a test',
            'status': None,
            'programmatic_descriptions': [
                {'source': 'c_1', 'text': 'description c'},
                {'source': 'a_1', 'text': 'description a'},
                {'source': 'b_1', 'text': 'description b'}
            ],
            'data_type': 'bigint',
            'feature_group': 'test_feature_group',
            'version': '1.4',
            'tags': [],
            'watermarks': [
                {'key': 'test_key', 'watermark_type': 'high_watermark', 'time': ''},
                {'key': 'test_key', 'watermark_type': 'low_watermark', 'time': ''},
            ],
            'badges': [{'category': 'data', 'badge_name': 'pii'}],
        }
        self.expected_feature_metadata: dict = {
            'entity': 'rider',
            'key': 'test_feature_group/test_feature_name/1.4',
            'created_timestamp': None,
            'availability': ['hive'],
            'last_updated_timestamp': 1563872712,
            'owners': [],
            'name': 'test_feature_name',
            'description': 'This is a test',
            'status': None,
            'programmatic_descriptions': [
                {'source': 'c_1', 'text': 'description c'},
                {'source': 'a_1', 'text': 'description a'},
                {'source': 'b_1', 'text': 'description b'}
            ],
            'data_type': 'bigint',
            'feature_group': 'test_feature_group',
            'version': '1.4',
            'tags': [],
            'watermarks': [
                {'key': 'test_key', 'watermark_type': 'high_watermark', 'time': ''},
                {'key': 'test_key', 'watermark_type': 'low_watermark', 'time': ''},
            ],
            'badges': [{'category': 'data', 'badge_name': 'pii'}],
        }
        self.mock_dashboard_metadata = {
            "badges": [],
            "chart_names": [],
            "cluster": "gold",
            "created_timestamp": 1558035206,
            "description": "test description",
            "frequent_users": [],
            "group_name": "test group name",
            "group_url": "test url",
            "last_run_state": "failed",
            "last_run_timestamp": 1587395014,
            "last_successful_run_timestamp": 1578434241,
            "name": "test report name",
            "owners": [
                {
                    "display_name": "First Last",
                    "email": "email@mail.com",
                    "employee_type": "teamMember",
                    "first_name": "First",
                    "full_name": "First Last",
                    "github_username": "",
                    "is_active": True,
                    "last_name": "Last",
                    "manager_email": "",
                    "manager_fullname": "",
                    "profile_url": "",
                    "role_name": "Test Role",
                    "slack_id": "",
                    "team_name": "Team Name",
                    "user_id": "test_user_id"
                }
            ],
            "product": "mode",
            "query_names": [
                "test query 1",
                "test query 2",
                "test query 3",
            ],
            "recent_view_count": 8,
            "tables": [
                {
                    "cluster": "cluster",
                    "database": "database",
                    "description": "test description",
                    "key": "database://cluster.schema/name",
                    "last_updated_timestamp": None,
                    "name": "name",
                    "schema": "schema",
                    "type": "table"
                },
                {
                    "cluster": "cluster",
                    "database": "database",
                    "description": "test description",
                    "key": "database://cluster.schema/name_2",
                    "last_updated_timestamp": None,
                    "name": "name_2",
                    "schema": "schema",
                    "type": "table"
                },
            ],
            "tags": [
                {
                    "tag_name": "amundsen",
                    "tag_type": "default"
                },
            ],
            "updated_timestamp": 1578433917,
            "uri": "test_dashboard_uri",
            "url": "test_dashboard_url"
        }

        self.expected_parsed_dashboard = {
            "badges": [],
            "chart_names": [],
            "cluster": "gold",
            "created_timestamp": 1558035206,
            "description": "test description",
            "frequent_users": [],
            "group_name": "test group name",
            "group_url": "test url",
            "last_run_state": "failed",
            "last_run_timestamp": 1587395014,
            "last_successful_run_timestamp": 1578434241,
            "name": "test report name",
            "owners": [
                {
                    "display_name": "First Last",
                    "email": "email@mail.com",
                    "employee_type": "teamMember",
                    "first_name": "First",
                    "full_name": "First Last",
                    "github_username": "",
                    "is_active": True,
                    "last_name": "Last",
                    "manager_email": "",
                    "manager_fullname": "",
                    "profile_url": "",
                    "role_name": "Test Role",
                    "slack_id": "",
                    "team_name": "Team Name",
                    "user_id": "test_user_id"
                }
            ],
            "product": "mode",
            "query_names": [
                "test query 1",
                "test query 2",
                "test query 3",
            ],
            "recent_view_count": 8,
            "tables": [
                {
                    "cluster": "cluster",
                    "database": "database",
                    "description": "test description",
                    "key": "database://cluster.schema/name",
                    "last_updated_timestamp": None,
                    "name": "name",
                    "schema": "schema",
                    "type": "table"
                },
                {
                    "cluster": "cluster",
                    "database": "database",
                    "description": "test description",
                    "key": "database://cluster.schema/name_2",
                    "last_updated_timestamp": None,
                    "name": "name_2",
                    "schema": "schema",
                    "type": "table"
                },
            ],
            "tags": [
                {
                    "tag_name": "amundsen",
                    "tag_type": "default"
                },
            ],
            "updated_timestamp": 1578433917,
            "uri": "test_dashboard_uri",
            "url": "test_dashboard_url"
        }

    @responses.activate
    def test_popular_resources_success(self) -> None:
        """
        Test successful popular_resources request
        :return:
        """
        mock_url = local_app.config['METADATASERVICE_BASE'] \
            + POPULAR_RESOURCES_ENDPOINT \
            + f'/{TEST_USER_ID}'
        responses.add(responses.GET, mock_url,
                      json=self.mock_popular_tables, status=HTTPStatus.OK)

        with local_app.test_client() as test:
            response = test.get('/api/metadata/v0/popular_resources?types=table')
            data = json.loads(response.data)
            self.assertEqual(response.status_code, HTTPStatus.OK)
            _table_label = to_label(resource_type=ResourceType.Table)
            _dashboard_label = to_label(resource_type=ResourceType.Dashboard)
            self.assertCountEqual(data.get('results').get(_table_label), self.expected_parsed_popular_tables)
            self.assertCountEqual(data.get('results').get(_dashboard_label), [])

    @responses.activate
    def test_popular_resources_propagate_failure(self) -> None:
        """
        Test that any error codes from the request are propagated through, to be
        returned to the React application
        :return:
        """
        mock_url = local_app.config['METADATASERVICE_BASE'] \
            + POPULAR_RESOURCES_ENDPOINT \
            + f'/{TEST_USER_ID}'
        responses.add(responses.GET, mock_url,
                      json=self.mock_popular_tables, status=HTTPStatus.BAD_REQUEST)

        with local_app.test_client() as test:
            response = test.get('/api/metadata/v0/popular_resources?types=table')
            self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)

    @responses.activate
    def test_popular_resources_catch_exception(self) -> None:
        """
        Test catching exception if there is an issue processing the popular resources
        results from the metadata service
        :return:
        """
        mock_url = local_app.config['METADATASERVICE_BASE'] \
            + POPULAR_RESOURCES_ENDPOINT \
            + f'/{TEST_USER_ID}'
        responses.add(responses.GET, mock_url,
                      json={ResourceType.Table.name: None}, status=HTTPStatus.OK)

        with local_app.test_client() as test:
            response = test.get('/api/metadata/v0/popular_resources?types=table')
            self.assertEqual(response.status_code, HTTPStatus.INTERNAL_SERVER_ERROR)

    @responses.activate
    def test_get_table_metadata_success(self) -> None:
        """
        Test successful get_table_metadata request
        :return:
        """
        url = local_app.config['METADATASERVICE_BASE'] + TABLE_ENDPOINT + '/db://cluster.schema/table'
        responses.add(responses.GET, url, json=self.mock_metadata, status=HTTPStatus.OK)

        with local_app.test_client() as test:
            response = test.get(
                '/api/metadata/v0/table',
                query_string=dict(
                    key='db://cluster.schema/table',
                    index='0',
                    source='test_source'
                )
            )
            data = json.loads(response.data)
            self.assertEqual(response.status_code, HTTPStatus.OK)
            self.assertCountEqual(data.get('tableData'), self.expected_parsed_metadata)

    @responses.activate
    def test_update_table_owner_success(self) -> None:
        """
        Test successful update_table_owner request
        :return:
        """
        url = local_app.config['METADATASERVICE_BASE'] + TABLE_ENDPOINT + '/db://cluster.schema/table/owner/test'
        responses.add(responses.PUT, url, json={}, status=HTTPStatus.OK)

        with local_app.test_client() as test:
            response = test.put(
                '/api/metadata/v0/update_table_owner',
                json={
                    'key': 'db://cluster.schema/table',
                    'owner': 'test'
                }
            )
            self.assertEqual(response.status_code, HTTPStatus.OK)

    @responses.activate
    def test_update_table_owner_propagate_failure(self) -> None:
        """
        Test that any error codes from the update_table_owner request are propagated
        to be returned to the React application
        :return:
        """
        url = local_app.config['METADATASERVICE_BASE'] + TABLE_ENDPOINT + '/db://cluster.schema/table/owner/test'
        responses.add(responses.PUT, url, json={}, status=HTTPStatus.BAD_REQUEST)

        with local_app.test_client() as test:
            response = test.put(
                '/api/metadata/v0/update_table_owner',
                json={
                    'key': 'db://cluster.schema/table',
                    'owner': 'test'
                }
            )
            self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)

    @responses.activate
    def test_get_last_indexed_success(self) -> None:
        """
        Test successful get_last_indexed request
        :return:
        """
        responses.add(responses.GET, local_app.config['METADATASERVICE_BASE'] + LAST_INDEXED_ENDPOINT,
                      json={'neo4j_latest_timestamp': 1538352000}, status=HTTPStatus.OK)

        with local_app.test_client() as test:
            response = test.get('/api/metadata/v0/get_last_indexed')
            data = json.loads(response.data)
            self.assertEqual(response.status_code, HTTPStatus.OK)
            self.assertEqual(data.get('timestamp'), 1538352000)

    @responses.activate
    def test_get_last_indexed_propagate_failure(self) -> None:
        """
        Test that any error codes from the get_last_indexed request are propagated through,
        to be returned to the React application
        :return:
        """
        responses.add(responses.GET, local_app.config['METADATASERVICE_BASE'] + LAST_INDEXED_ENDPOINT,
                      json=None, status=HTTPStatus.BAD_REQUEST)

        with local_app.test_client() as test:
            response = test.get('/api/metadata/v0/get_last_indexed')
            self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)

    @responses.activate
    def test_get_table_description_success(self) -> None:
        """
        Test successful get_table_description request
        :return:
        """
        url = local_app.config['METADATASERVICE_BASE'] + TABLE_ENDPOINT + '/db://cluster.schema/table/description'
        responses.add(responses.GET, url, json={'description': 'This is a test'}, status=HTTPStatus.OK)

        with local_app.test_client() as test:
            response = test.get(
                '/api/metadata/v0/get_table_description',
                query_string=dict(key='db://cluster.schema/table')
            )
            data = json.loads(response.data)
            self.assertEqual(response.status_code, HTTPStatus.OK)
            self.assertEqual(data.get('description'), 'This is a test')

    @responses.activate
    def test_get_table_description_propagate_failure(self) -> None:
        """
        Test that any error codes from the get_table_description request are propagated through,
        to be returned to the React application
        :return:
        """
        url = local_app.config['METADATASERVICE_BASE'] + TABLE_ENDPOINT + '/db://cluster.schema/table/description'
        responses.add(responses.GET, url, json={'description': 'This is a test'}, status=HTTPStatus.BAD_REQUEST)

        with local_app.test_client() as test:
            response = test.get(
                '/api/metadata/v0/get_table_description',
                query_string=dict(key='db://cluster.schema/table')
            )
            self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)

    @responses.activate
    def test_put_table_description_success(self) -> None:
        """
        Test successful put_table_description request
        :return:
        """
        url = local_app.config['METADATASERVICE_BASE'] + TABLE_ENDPOINT + '/db://cluster.schema/table/description'
        responses.add(responses.PUT, url, json={}, status=HTTPStatus.OK)

        with local_app.test_client() as test:
            response = test.put(
                '/api/metadata/v0/put_table_description',
                json={
                    'key': 'db://cluster.schema/table',
                    'description': 'test',
                    'source': 'source'
                }
            )
            self.assertEqual(response.status_code, HTTPStatus.OK)

    @responses.activate
    def test_put_table_description_denied(self) -> None:
        """
        Test put_table_description that should be rejected due to permissions.
        :return:
        """
        url = local_app.config['METADATASERVICE_BASE'] + TABLE_ENDPOINT + \
            '/db://cluster.schema/table/column/colA/description'
        responses.add(responses.GET, url, json={'description': 'This is a test'}, status=HTTPStatus.OK)

        with patch.dict(local_app.config, {'UNEDITABLE_SCHEMAS': set(['schema'])}):
            with local_app.test_client() as test:
                response = test.put(
                    '/api/metadata/v0/put_table_description',
                    json={
                        'key': 'db://cluster.schema/table',
                        'description': 'test',
                        'source': 'source'
                    }
                )
                self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    @responses.activate
    def test_get_column_description_success(self) -> None:
        """
        Test successful get_column_description request
        :return:
        """
        url = local_app.config['METADATASERVICE_BASE'] + TABLE_ENDPOINT + \
            '/db://cluster.schema/table/column/colA/description'
        responses.add(responses.GET, url, json={'description': 'This is a test'}, status=HTTPStatus.OK)

        with local_app.test_client() as test:
            response = test.get(
                '/api/metadata/v0/get_column_description',
                query_string=dict(
                    key='db://cluster.schema/table',
                    index='0',
                    column_name='colA'
                )
            )
            data = json.loads(response.data)
            self.assertEqual(response.status_code, HTTPStatus.OK)
            self.assertEqual(data.get('description'), 'This is a test')

    @responses.activate
    def test_get_column_description_propagate_failure(self) -> None:
        """
        Test that any error codes from the get_column_description request are propagated through,
        to be returned to the React application
        :return:
        """
        url = local_app.config['METADATASERVICE_BASE'] + TABLE_ENDPOINT + \
            '/db://cluster.schema/table/column/colA/description'
        responses.add(responses.GET, url, json={'description': 'This is a test'}, status=HTTPStatus.BAD_REQUEST)

        with local_app.test_client() as test:
            response = test.get(
                '/api/metadata/v0/get_column_description',
                query_string=dict(
                    key='db://cluster.schema/table',
                    index='0',
                    column_name='colA'
                )
            )
            self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)

    @responses.activate
    def test_put_column_description_success(self) -> None:
        """
        Test successful put_column_description request
        :return:
        """
        url = local_app.config['METADATASERVICE_BASE'] + TABLE_ENDPOINT + \
            '/db://cluster.schema/table/column/col/description'
        responses.add(responses.PUT, url, json={}, status=HTTPStatus.OK)

        with local_app.test_client() as test:
            response = test.put(
                '/api/metadata/v0/put_column_description',
                json={
                    'key': 'db://cluster.schema/table',
                    'column_name': 'col',
                    'description': 'test',
                    'source': 'source'
                }
            )
            self.assertEqual(response.status_code, HTTPStatus.OK)

    @responses.activate
    def test_put_column_description_denied(self) -> None:
        """
        Test put_column_description on an unwritable table.
        :return:
        """
        url = local_app.config['METADATASERVICE_BASE'] + TABLE_ENDPOINT + \
            '/db://cluster.schema/an_uneditable_table/column/col/description'
        responses.add(responses.PUT, url, json={}, status=HTTPStatus.OK)

        rule = MatchRuleObject(table_name_regex=r".*uneditable_table.*")
        with patch.dict(local_app.config, {'UNEDITABLE_TABLE_DESCRIPTION_MATCH_RULES': [rule]}):
            with local_app.test_client() as test:
                response = test.put(
                    '/api/metadata/v0/put_column_description',
                    json={
                        'key': 'db://cluster.schema/an_uneditable_table',
                        'column_name': 'col',
                        'description': 'test',
                        'source': 'source'
                    }
                )
                self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    @responses.activate
    def test_get_tags(self) -> None:
        """
        Test successful fetch of all tags
        :return:
        """
        url = local_app.config['METADATASERVICE_BASE'] + TAGS_ENDPOINT
        responses.add(responses.GET, url, json=self.mock_tags, status=HTTPStatus.OK)

        with local_app.test_client() as test:
            response = test.get('/api/metadata/v0/tags')
            data = json.loads(response.data)
            self.assertCountEqual(data.get('tags'), self.expected_parsed_tags)

    @responses.activate
    def test_update_table_tags_put(self) -> None:
        """
        Test adding a tag on a table
        :return:
        """
        url = local_app.config['METADATASERVICE_BASE'] + TABLE_ENDPOINT + '/db://cluster.schema/table/tag/tag_5'
        responses.add(responses.PUT, url, json={}, status=HTTPStatus.OK)

        searchservice_base = local_app.config['SEARCHSERVICE_BASE']
        get_table_url = f'{searchservice_base}/search_table'
        responses.add(responses.POST, get_table_url,
                      json={'results': [{'id': '1', 'tags': [{'tag_name': 'tag_1'}, {'tag_name': 'tag_2'}]}]},
                      status=HTTPStatus.OK)

        post_table_url = f'{searchservice_base}/document_table'
        responses.add(responses.PUT, post_table_url, json={}, status=HTTPStatus.OK)

        with local_app.test_client() as test:
            response = test.put(
                '/api/metadata/v0/update_table_tags',
                json={
                    'key': 'db://cluster.schema/table',
                    'tag': 'tag_5'
                }
            )
            self.assertEqual(response.status_code, HTTPStatus.OK)

    @responses.activate
    def test_update_table_tags_delete(self) -> None:
        """
        Test deleting a tag on a table
        :return:
        """
        url = local_app.config['METADATASERVICE_BASE'] + TABLE_ENDPOINT + '/db://cluster.schema/table/tag/tag_5'
        responses.add(responses.DELETE, url, json={}, status=HTTPStatus.OK)

        searchservice_base = local_app.config['SEARCHSERVICE_BASE']
        get_table_url = f'{searchservice_base}/search_table'
        responses.add(responses.POST, get_table_url,
                      json={'results': [{'id': '1', 'tags': [{'tag_name': 'tag_1'}, {'tag_name': 'tag_2'}]}]},
                      status=HTTPStatus.OK)

        post_table_url = f'{searchservice_base}/document_table'
        responses.add(responses.PUT, post_table_url, json={}, status=HTTPStatus.OK)

        with local_app.test_client() as test:
            response = test.delete(
                '/api/metadata/v0/update_table_tags',
                json={
                    'key': 'db://cluster.schema/table',
                    'tag': 'tag_5'
                }
            )
            self.assertEqual(response.status_code, HTTPStatus.OK)

    @responses.activate
    def test_update_dashboard_tags_put(self) -> None:
        """
        Test adding a tag on a dashboard
        :return:
        """
        url = local_app.config['METADATASERVICE_BASE'] + DASHBOARD_ENDPOINT + '/test_dashboard_uri/tag/test_tag'
        responses.add(responses.PUT, url, json={}, status=HTTPStatus.OK)

        with local_app.test_client() as test:
            response = test.put(
                '/api/metadata/v0/update_dashboard_tags',
                json={
                    'key': 'test_dashboard_uri',
                    'tag': 'test_tag'
                }
            )
            self.assertEqual(response.status_code, HTTPStatus.OK)

    @responses.activate
    def test_update_dashboard_tags_delete(self) -> None:
        """
        Test deleting a tag on a dashboard
        :return:
        """
        url = local_app.config['METADATASERVICE_BASE'] + DASHBOARD_ENDPOINT + '/test_dashboard_uri/tag/test_tag'
        responses.add(responses.DELETE, url, json={}, status=HTTPStatus.OK)

        with local_app.test_client() as test:
            response = test.delete(
                '/api/metadata/v0/update_dashboard_tags',
                json={
                    'key': 'test_dashboard_uri',
                    'tag': 'test_tag'
                }
            )
            self.assertEqual(response.status_code, HTTPStatus.OK)

    @responses.activate
    def test_get_user_failure(self) -> None:
        """
        Test get_user fails when no user_id is specified
        """
        url = local_app.config['METADATASERVICE_BASE'] + USER_ENDPOINT + '/testuser'
        responses.add(responses.GET, url, json=self.mock_user, status=HTTPStatus.OK)

        with local_app.test_client() as test:
            response = test.get('/api/metadata/v0/user')
            self.assertEqual(response.status_code, HTTPStatus.INTERNAL_SERVER_ERROR)

    @responses.activate
    def test_get_user_success(self) -> None:
        """
        Test get_user success
        """
        url = local_app.config['METADATASERVICE_BASE'] + USER_ENDPOINT + '/testuser'
        responses.add(responses.GET, url, json=self.mock_user, status=HTTPStatus.OK)

        with local_app.test_client() as test:
            response = test.get('/api/metadata/v0/user', query_string=dict(user_id='testuser'))
            data = json.loads(response.data)
            self.assertEqual(response.status_code, HTTPStatus.OK)
            self.assertEqual(dict(data.get('user'), **self.expected_parsed_user), data.get('user'))

    @responses.activate
    def test_get_bookmark(self) -> None:
        """
        Test get_bookmark with no user specified
        """
        url = '{0}{1}/{2}/follow/'.format(local_app.config['METADATASERVICE_BASE'], USER_ENDPOINT, TEST_USER_ID)
        responses.add(responses.GET, url, json=self.get_user_resource_response, status=HTTPStatus.OK)

        with local_app.test_client() as test:
            response = test.get('/api/metadata/v0/user/bookmark')
            data = json.loads(response.data)
            self.assertEqual(response.status_code, HTTPStatus.OK)
            self.assertCountEqual(data.get('bookmarks'), self.expected_parsed_user_resources)

    @responses.activate
    def test_get_bookmark_failure(self) -> None:
        """
        Test correct response returned when get_bookmark fails
        """
        url = f"{local_app.config['METADATASERVICE_BASE']}{USER_ENDPOINT}/{TEST_USER_ID}/follow/"
        responses.add(responses.GET, url, json=self.mock_user, status=HTTPStatus.BAD_REQUEST)

        with local_app.test_client() as test:
            response = test.get('/api/metadata/v0/user/bookmark')
            self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)
            expected = {
                'bookmarks': {'table': [], 'dashboard': []},
                'msg': 'Encountered error: failed to get bookmark for user_id: test_user_id',
            }
            self.assertEqual(response.json, expected)

    @responses.activate
    def test_get_bookmark_for_user(self) -> None:
        """
        Test get_bookmark with a specified user
        """
        specified_user = 'other_user'
        url = '{0}{1}/{2}/follow/'.format(local_app.config['METADATASERVICE_BASE'], USER_ENDPOINT, specified_user)
        responses.add(responses.GET, url, json=self.get_user_resource_response, status=HTTPStatus.OK)

        with local_app.test_client() as test:
            response = test.get('/api/metadata/v0/user/bookmark', query_string=dict(user_id=specified_user))
            data = json.loads(response.data)
            self.assertEqual(response.status_code, HTTPStatus.OK)
            self.assertCountEqual(data.get('bookmarks'), self.expected_parsed_user_resources)

    @responses.activate
    def test_put_bookmark(self) -> None:
        """
        Test update_bookmark with a PUT request
        """
        resource_type = 'table'
        key = 'database://cluster.schema/table_name_1'
        url = '{0}{1}/{2}/follow/{3}/{4}'.format(local_app.config['METADATASERVICE_BASE'],
                                                 USER_ENDPOINT,
                                                 TEST_USER_ID,
                                                 resource_type,
                                                 key)
        responses.add(responses.PUT, url, json={}, status=HTTPStatus.OK)

        with local_app.test_client() as test:
            response = test.put(
                '/api/metadata/v0/user/bookmark',
                json={
                    'type': resource_type,
                    'key': key,
                })

            self.assertEqual(response.status_code, HTTPStatus.OK)

    @responses.activate
    def test_delete_bookmark(self) -> None:
        """
        Test update_bookmark with a DELETE request
        """
        resource_type = 'table'
        key = 'database://cluster.schema/table_name_1'
        url = '{0}{1}/{2}/follow/{3}/{4}'.format(local_app.config['METADATASERVICE_BASE'],
                                                 USER_ENDPOINT,
                                                 TEST_USER_ID,
                                                 resource_type,
                                                 key)
        responses.add(responses.DELETE, url, json={}, status=HTTPStatus.OK)

        with local_app.test_client() as test:
            response = test.delete(
                '/api/metadata/v0/user/bookmark',
                json={
                    'type': resource_type,
                    'key': key,
                })

            self.assertEqual(response.status_code, HTTPStatus.OK)

    @responses.activate
    def test_get_user_read(self) -> None:
        """
        Test get_user_read API request
        """
        test_user = 'test_user'
        url = '{0}{1}/{2}/read/'.format(local_app.config['METADATASERVICE_BASE'], USER_ENDPOINT, test_user)
        responses.add(responses.GET, url, json=self.get_user_resource_response, status=HTTPStatus.OK)

        with local_app.test_client() as test:
            response = test.get('/api/metadata/v0/user/read', query_string=dict(user_id=test_user))
            data = json.loads(response.data)
            self.assertEqual(response.status_code, HTTPStatus.OK)
            self.assertCountEqual(data.get('read'), self.expected_parsed_user_resources.get('table'))  # type: ignore

    @responses.activate
    def test_get_user_own(self) -> None:
        """
        Test get_user_own API request
        """
        test_user = 'test_user'
        url = '{0}{1}/{2}/own/'.format(local_app.config['METADATASERVICE_BASE'], USER_ENDPOINT, test_user)
        responses.add(responses.GET, url, json=self.get_user_resource_response, status=HTTPStatus.OK)

        with local_app.test_client() as test:
            response = test.get('/api/metadata/v0/user/own', query_string=dict(user_id=test_user))
            data = json.loads(response.data)
            self.assertEqual(response.status_code, HTTPStatus.OK)
            self.assertCountEqual(data.get('own'), self.expected_parsed_user_resources)

    @responses.activate
    def test_get_dashboard_success(self) -> None:
        """
        Test get_dashboard API success
        :return:
        """
        url = local_app.config['METADATASERVICE_BASE'] + DASHBOARD_ENDPOINT + '/test_dashboard_uri'
        responses.add(responses.GET, url, json=self.mock_dashboard_metadata, status=HTTPStatus.OK)

        with local_app.test_client() as test:
            response = test.get(
                '/api/metadata/v0/dashboard',
                query_string=dict(
                    uri='test_dashboard_uri',
                    index='0',
                    source='test_source'
                )
            )
            data = json.loads(response.data)
            self.assertEqual(response.status_code, HTTPStatus.OK)
            self.assertCountEqual(data.get('dashboard'), self.expected_parsed_dashboard)

    @responses.activate
    def test_get_dashboard_bad_parameters(self) -> None:
        """
        Test get_dashboard API failure with missing URI parameter
        :return:
        """
        url = local_app.config['METADATASERVICE_BASE'] + DASHBOARD_ENDPOINT + '/test_dashboard_uri'
        responses.add(responses.GET, url, json=self.mock_dashboard_metadata, status=HTTPStatus.OK)

        with local_app.test_client() as test:
            response = test.get(
                '/api/metadata/v0/dashboard',
                query_string=dict()
            )
            data = json.loads(response.data)
            self.assertEqual(response.status_code, HTTPStatus.INTERNAL_SERVER_ERROR)
            self.assertCountEqual(data.get('dashboard'), {})

    @responses.activate
    def test_get_related_dashboards_success(self) -> None:
        """
        Test get_related_dashboards API success
        :return:
        """
        test_table = 'db://cluster.schema/table'
        url = local_app.config['METADATASERVICE_BASE'] + TABLE_ENDPOINT + '/' + test_table + '/dashboard/'
        responses.add(responses.GET, url, json=self.expected_related_dashboard_response, status=HTTPStatus.OK)

        with local_app.test_client() as test:
            response = test.get(
                '/api/metadata/v0/table/{0}/dashboards'.format(test_table)
            )
            data = json.loads(response.data)
            self.assertEqual(response.status_code, HTTPStatus.OK)
            self.assertEqual(
                len(data.get('dashboards')),
                len(self.expected_related_dashboard_response['dashboards'])
            )

    @responses.activate
    def test_get_related_dashboards_failure(self) -> None:
        """
        Test get_related_dashboards API failure
        :return:
        """
        test_table = 'db://cluster.schema/table'
        url = local_app.config['METADATASERVICE_BASE'] + TABLE_ENDPOINT + '/' + test_table + '/dashboard/'
        responses.add(responses.GET, url, json=self.expected_related_dashboard_response, status=HTTPStatus.BAD_REQUEST)

        with local_app.test_client() as test:
            response = test.get(
                '/api/metadata/v0/table/{0}/dashboards'.format(test_table)
            )
            self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)
            expected = {
                'dashboards': [],
                'msg': 'Encountered 400 Error: Related dashboard metadata request failed',
                'status_code': 400
            }
            self.assertEqual(response.json, expected)

    @responses.activate
    def test_get_feature_metadata_failure(self) -> None:
        """
        Test get_feature_metadata API failure
        :return:
        """
        url = local_app.config['METADATASERVICE_BASE'] + FEATURE_ENDPOINT + '/test_feature_group/test_feature_name/1.4'
        responses.add(responses.GET, url, json=self.mock_feature_metadata, status=HTTPStatus.BAD_REQUEST)

        with local_app.test_client() as test:
            response = test.get(
                '/api/metadata/v0/feature',
                query_string=dict(
                    key='test_feature_group/test_feature_name/1.4'
                )
            )
            data = json.loads(response.data)
            expected = {
                'featureData': {},
                'msg': 'Encountered error: Metadata request failed',
                'status_code': 400
            }

            self.assertEqual(data, expected)

    @responses.activate
    def test_get_feature_metadata_success(self) -> None:
        """
        Test successful get_feature_metadata request
        :return:
        """
        url = local_app.config['METADATASERVICE_BASE'] + FEATURE_ENDPOINT + '/test_feature_group/test_feature_name/1.4'
        responses.add(responses.GET, url, json=self.mock_feature_metadata, status=HTTPStatus.OK)

        with local_app.test_client() as test:
            response = test.get(
                '/api/metadata/v0/feature',
                query_string=dict(
                    key='test_feature_group/test_feature_name/1.4'
                )
            )
            data = json.loads(response.data)
            self.assertEqual(response.status_code, HTTPStatus.OK)
            self.assertCountEqual(data.get('featureData'), self.expected_feature_metadata)

    @responses.activate
    def test_get_feature_description_success(self) -> None:
        """
        Test successful get_feature_description request
        :return:
        """
        url = local_app.config['METADATASERVICE_BASE'] + FEATURE_ENDPOINT + \
            '/test_feature_group/test_feature_name/1.4/description'
        responses.add(responses.GET, url, json={'description': 'This is a test'}, status=HTTPStatus.OK)

        with local_app.test_client() as test:
            response = test.get(
                '/api/metadata/v0/get_feature_description',
                query_string=dict(key='test_feature_group/test_feature_name/1.4')
            )
            data = json.loads(response.data)

            self.assertEqual(response.status_code, HTTPStatus.OK)
            self.assertEqual(data.get('description'), 'This is a test')

    @responses.activate
    def test_put_feature_description(self) -> None:
        """
        Test successful put_feature_description request
        :return:
        """
        url = local_app.config['METADATASERVICE_BASE'] + FEATURE_ENDPOINT + \
            '/test_feature_group/test_feature_name/1.4/description'
        responses.add(responses.PUT, url, json={}, status=HTTPStatus.OK)

        with local_app.test_client() as test:
            response = test.put(
                '/api/metadata/v0/put_feature_description',
                json={
                    'key': 'test_feature_group/test_feature_name/1.4',
                    'description': 'test',
                    'source': 'source'
                }
            )

            self.assertEqual(response.status_code, HTTPStatus.OK)

    @responses.activate
    def test_get_feature_generation_code(self) -> None:
        """
        Test successful get_feature_generation_code request
        :return:
        """
        url = local_app.config['METADATASERVICE_BASE'] + FEATURE_ENDPOINT + \
            '/test_feature_group/test_feature_name/1.4/generation_code'
        responses.add(responses.GET, url, json={'name': 'generation_query',
                                                'text': 'SELECT * FROM test_table',
                                                'url': 'github.com/repo/file'}, status=HTTPStatus.OK)

        with local_app.test_client() as test:
            response = test.get(
                '/api/metadata/v0/get_feature_generation_code',
                query_string=dict(key='test_feature_group/test_feature_name/1.4')
            )
            data = json.loads(response.data)

            self.assertEqual(response.status_code, HTTPStatus.OK)
            self.assertEqual(data.get('name'), 'generation_query')
            self.assertEqual(data.get('text'), 'SELECT * FROM test_table')
            self.assertEqual(data.get('url'), 'github.com/repo/file')

    @responses.activate
    def test_update_feature_owner(self) -> None:
        """
        Test successful update_feature_owner request
        :return:
        """
        url = local_app.config['METADATASERVICE_BASE'] + FEATURE_ENDPOINT + \
            '/test_feature_group/test_feature_name/1.4/owner/test'
        responses.add(responses.PUT, url, json={}, status=HTTPStatus.OK)

        with local_app.test_client() as test:
            response = test.put(
                '/api/metadata/v0/update_feature_owner',
                json={
                    'key': 'test_feature_group/test_feature_name/1.4',
                    'owner': 'test'
                }
            )

            self.assertEqual(response.status_code, HTTPStatus.OK)

    @responses.activate
    def test_update_feature_tags(self) -> None:
        """
        Test adding a tag on a feature
        :return:
        """
        url = local_app.config['METADATASERVICE_BASE'] + FEATURE_ENDPOINT + \
            '/test_feature_group/test_feature_name/1.4/tag/tag_5'
        responses.add(responses.PUT, url, json={}, status=HTTPStatus.OK)

        searchservice_base = local_app.config['SEARCHSERVICE_BASE']
        search_url = f'{searchservice_base}/search_feature_filter'
        responses.add(responses.POST, search_url,
                      json={'results': [{'id': '1', 'tags': [{'tag_name': 'tag_1'}, {'tag_name': 'tag_2'}]}]},
                      status=HTTPStatus.OK)

        search_update_url = f'{searchservice_base}/document_feature'
        responses.add(responses.PUT, search_update_url, json={}, status=HTTPStatus.OK)

        with local_app.test_client() as test:
            response = test.put(
                '/api/metadata/v0/update_feature_tags',
                json={
                    'key': 'test_feature_group/test_feature_name/1.4',
                    'tag': 'tag_5'
                }
            )
            self.assertEqual(response.status_code, HTTPStatus.OK)
