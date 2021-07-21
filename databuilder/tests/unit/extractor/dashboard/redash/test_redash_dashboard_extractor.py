# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import logging
import unittest
from typing import (
    Any, Dict, List,
)

from mock import patch
from pyhocon import ConfigFactory

from databuilder import Scoped
from databuilder.extractor.dashboard.redash.redash_dashboard_extractor import (
    RedashDashboardExtractor, TableRelationData,
)
from databuilder.models.dashboard.dashboard_chart import DashboardChart
from databuilder.models.dashboard.dashboard_last_modified import DashboardLastModifiedTimestamp
from databuilder.models.dashboard.dashboard_owner import DashboardOwner
from databuilder.models.dashboard.dashboard_query import DashboardQuery
from databuilder.models.dashboard.dashboard_table import DashboardTable

logging.basicConfig(level=logging.INFO)


def dummy_tables(*args: Any) -> List[TableRelationData]:
    return [TableRelationData('some_db', 'prod', 'public', 'users')]


class MockApiResponse:
    def __init__(self, data: Any) -> None:
        self.json_data = data
        self.status_code = 200

    def json(self) -> Any:
        return self.json_data

    def raise_for_status(self) -> None:
        pass


class TestRedashDashboardExtractor(unittest.TestCase):
    def test_table_relation_data(self) -> None:
        tr = TableRelationData('db', 'cluster', 'schema', 'tbl')
        self.assertEqual(tr.key, 'db://cluster.schema/tbl')

    def test_with_one_dashboard(self) -> None:
        def mock_api_get(url: str, *args: Any, **kwargs: Any) -> MockApiResponse:
            if '1000' in url:
                return MockApiResponse({
                    'id': 1000,
                    'widgets': [
                        {
                            'visualization': {
                                'query': {
                                    'data_source_id': 1,
                                    'id': 1234,
                                    'name': 'Test Query',
                                    'query': 'SELECT id FROM users'
                                },
                                'id': 12345,
                                'name': 'test_widget',
                                'type': 'CHART',
                            },
                            'options': {}
                        }
                    ]
                })

            return MockApiResponse({
                'page': 1,
                'count': 1,
                'page_size': 50,
                'results': [
                    {
                        'id': 1000,
                        'name': 'Test Dash',
                        'slug': 'test-dash',
                        'created_at': '2020-01-01T00:00:00.000Z',
                        'updated_at': '2020-01-02T00:00:00.000Z',
                        'is_archived': False,
                        'is_draft': False,
                        'user': {'email': 'asdf@example.com'}
                    }
                ]
            })

        redash_base_url = 'https://redash.example.com'
        config = ConfigFactory.from_dict({
            'extractor.redash_dashboard.redash_base_url': redash_base_url,
            'extractor.redash_dashboard.api_base_url': redash_base_url,  # probably not but doesn't matter
            'extractor.redash_dashboard.api_key': 'abc123',
            'extractor.redash_dashboard.table_parser':
                'tests.unit.extractor.dashboard.redash.test_redash_dashboard_extractor.dummy_tables'
        })

        with patch('databuilder.rest_api.rest_api_query.requests.get') as mock_get:
            mock_get.side_effect = mock_api_get

            extractor = RedashDashboardExtractor()
            extractor.init(Scoped.get_scoped_conf(conf=config, scope=extractor.get_scope()))

            # DashboardMetadata
            record = extractor.extract()
            self.assertEqual(record.dashboard_id, '1000')
            self.assertEqual(record.dashboard_name, 'Test Dash')
            self.assertEqual(record.dashboard_group_id, RedashDashboardExtractor.DASHBOARD_GROUP_ID)
            self.assertEqual(record.dashboard_group, RedashDashboardExtractor.DASHBOARD_GROUP_NAME)
            self.assertEqual(record.product, RedashDashboardExtractor.PRODUCT)
            self.assertEqual(record.cluster, RedashDashboardExtractor.DEFAULT_CLUSTER)
            self.assertEqual(record.created_timestamp, 1577836800)
            self.assertTrue(redash_base_url in record.dashboard_url)
            self.assertTrue('1000' in record.dashboard_url)

            # DashboardLastModified
            record = extractor.extract()
            identity: Dict[str, Any] = {
                'dashboard_id': '1000',
                'dashboard_group_id': RedashDashboardExtractor.DASHBOARD_GROUP_ID,
                'product': RedashDashboardExtractor.PRODUCT,
                'cluster': u'prod'
            }
            expected_timestamp = DashboardLastModifiedTimestamp(
                last_modified_timestamp=1577923200,
                **identity
            )
            self.assertEqual(record.__repr__(), expected_timestamp.__repr__())

            # DashboardOwner
            record = extractor.extract()
            expected_owner = DashboardOwner(email='asdf@example.com', **identity)
            self.assertEqual(record.__repr__(), expected_owner.__repr__())

            # DashboardQuery
            record = extractor.extract()
            expected_query = DashboardQuery(
                query_id='1234',
                query_name='Test Query',
                url=f'{redash_base_url}/queries/1234',
                query_text='SELECT id FROM users',
                **identity
            )
            self.assertEqual(record.__repr__(), expected_query.__repr__())

            # DashboardChart
            record = extractor.extract()
            expected_chart = DashboardChart(
                query_id='1234',
                chart_id='12345',
                chart_name='test_widget',
                chart_type='CHART',
                **identity
            )
            self.assertEqual(record.__repr__(), expected_chart.__repr__())

            # DashboardTable
            record = extractor.extract()
            expected_table = DashboardTable(
                table_ids=[TableRelationData('some_db', 'prod', 'public', 'users').key],
                **identity
            )
            self.assertEqual(record.__repr__(), expected_table.__repr__())

    def test_with_verion_8(self) -> None:
        def mock_api_get(url: str, *args: Any, **kwargs: Any) -> MockApiResponse:
            if 'test-dash' in url:
                return MockApiResponse({
                    'id': 1000,
                    'widgets': [
                        {
                            'visualization': {
                                'query': {
                                    'data_source_id': 1,
                                    'id': 1234,
                                    'name': 'Test Query',
                                    'query': 'SELECT id FROM users'
                                },
                                'id': 12345,
                                'name': 'test_widget',
                                'type': 'CHART',
                            },
                            'options': {}
                        }
                    ]
                })

            return MockApiResponse({
                'page': 1,
                'count': 1,
                'page_size': 50,
                'results': [
                    {
                        'id': 1000,
                        'name': 'Test Dash',
                        'slug': 'test-dash',
                        'created_at': '2020-01-01T00:00:00.000Z',
                        'updated_at': '2020-01-02T00:00:00.000Z',
                        'is_archived': False,
                        'is_draft': False,
                        'user': {'email': 'asdf@example.com'}
                    }
                ]
            })

        redash_base_url = 'https://redash.example.com'
        config = ConfigFactory.from_dict({
            'extractor.redash_dashboard.redash_base_url': redash_base_url,
            'extractor.redash_dashboard.api_base_url': redash_base_url,  # probably not but doesn't matter
            'extractor.redash_dashboard.api_key': 'abc123',
            'extractor.redash_dashboard.table_parser':
                'tests.unit.extractor.dashboard.redash.test_redash_dashboard_extractor.dummy_tables',
            'extractor.redash_dashboard.redash_version': 8
        })

        with patch('databuilder.rest_api.rest_api_query.requests.get') as mock_get:
            mock_get.side_effect = mock_api_get

            extractor = RedashDashboardExtractor()
            extractor.init(Scoped.get_scoped_conf(conf=config, scope=extractor.get_scope()))

            # DashboardMetadata
            record = extractor.extract()
            self.assertEqual(record.dashboard_id, '1000')
            self.assertEqual(record.dashboard_name, 'Test Dash')
            self.assertEqual(record.dashboard_group_id, RedashDashboardExtractor.DASHBOARD_GROUP_ID)
            self.assertEqual(record.dashboard_group, RedashDashboardExtractor.DASHBOARD_GROUP_NAME)
            self.assertEqual(record.product, RedashDashboardExtractor.PRODUCT)
            self.assertEqual(record.cluster, RedashDashboardExtractor.DEFAULT_CLUSTER)
            self.assertEqual(record.created_timestamp, 1577836800)
            self.assertTrue(redash_base_url in record.dashboard_url)
            self.assertTrue('test-dash' in record.dashboard_url)

            # DashboardLastModified
            record = extractor.extract()
            identity: Dict[str, Any] = {
                'dashboard_id': '1000',
                'dashboard_group_id': RedashDashboardExtractor.DASHBOARD_GROUP_ID,
                'product': RedashDashboardExtractor.PRODUCT,
                'cluster': u'prod'
            }
            expected_timestamp = DashboardLastModifiedTimestamp(
                last_modified_timestamp=1577923200,
                **identity
            )
            self.assertEqual(record.__repr__(), expected_timestamp.__repr__())

            # DashboardOwner
            record = extractor.extract()
            expected_owner = DashboardOwner(email='asdf@example.com', **identity)
            self.assertEqual(record.__repr__(), expected_owner.__repr__())

            # DashboardQuery
            record = extractor.extract()
            expected_query = DashboardQuery(
                query_id='1234',
                query_name='Test Query',
                url=f'{redash_base_url}/queries/1234',
                query_text='SELECT id FROM users',
                **identity
            )
            self.assertEqual(record.__repr__(), expected_query.__repr__())

            # DashboardChart
            record = extractor.extract()
            expected_chart = DashboardChart(
                query_id='1234',
                chart_id='12345',
                chart_name='test_widget',
                chart_type='CHART',
                **identity
            )
            self.assertEqual(record.__repr__(), expected_chart.__repr__())

            # DashboardTable
            record = extractor.extract()
            expected_table = DashboardTable(
                table_ids=[TableRelationData('some_db', 'prod', 'public', 'users').key],
                **identity
            )
            self.assertEqual(record.__repr__(), expected_table.__repr__())


if __name__ == '__main__':
    unittest.main()
