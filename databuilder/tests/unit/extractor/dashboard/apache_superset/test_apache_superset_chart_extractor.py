# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0
import unittest
from typing import Any

from mock import MagicMock, Mock
from pyhocon import ConfigFactory

from databuilder import Scoped
from databuilder.extractor.dashboard.apache_superset.apache_superset_chart_extractor import ApacheSupersetChartExtractor
from databuilder.models.dashboard.dashboard_chart import DashboardChart
from databuilder.models.dashboard.dashboard_query import DashboardQuery

dashboard_details_response = {
    'dashboards': [
        {
            '__Dashboard__': {
                'slices': [
                    {
                        '__Slice__': {
                            'id': 1,
                            'slice_name': 'chart_1',
                            'viz_type': 'pie_chart',
                            'chart_url': '/chart_1'
                        }
                    },
                    {
                        '__Slice__': {
                            'id': 2,
                            'slice_name': 'chart_2',
                            'viz_type': 'table',
                            'chart_url': '/chart_2'
                        }
                    }
                ]
            }
        }
    ]
}


class TestApacheSupersetChartExtractor(unittest.TestCase):
    def setUp(self) -> None:
        config = ConfigFactory.from_dict({
            'extractor.apache_superset.dashboard_group_id': '1',
            'extractor.apache_superset.dashboard_group_name': 'dashboard group',
            'extractor.apache_superset.dashboard_group_description': 'dashboard group description',
            'extractor.apache_superset.cluster': 'gold',
            'extractor.apache_superset.apache_superset_security_settings_dict': dict(username='admin',
                                                                                     password='admin',
                                                                                     provider='db')
        })

        self.config = config

    def _get_extractor(self) -> Any:
        extractor = self._extractor_class()
        extractor.authenticate = MagicMock()
        extractor.init(Scoped.get_scoped_conf(conf=self.config, scope=extractor.get_scope()))

        return extractor

    @property
    def _extractor_class(self) -> Any:
        return ApacheSupersetChartExtractor

    def test_extractor(self) -> None:
        extractor = self._get_extractor()

        extractor.execute_query = Mock(side_effect=[{'ids': [1]}, dashboard_details_response])

        record = extractor.extract()

        self.assertIsInstance(record, DashboardQuery)
        self.assertEqual(record._query_name, 'default')
        self.assertEqual(record._query_id, '-1')
        self.assertEqual(record._product, 'superset')
        self.assertEqual(record._cluster, 'gold')

        record = extractor.extract()

        self.assertIsInstance(record, DashboardChart)
        self.assertEqual(record._query_id, '-1')
        self.assertEqual(record._chart_id, '1')
        self.assertEqual(record._chart_name, 'chart_1')
        self.assertEqual(record._chart_type, 'pie_chart')
        self.assertEqual(record._chart_url, '')

        record = extractor.extract()

        self.assertIsInstance(record, DashboardChart)
        self.assertEqual(record._query_id, '-1')
        self.assertEqual(record._chart_id, '2')
        self.assertEqual(record._chart_name, 'chart_2')
        self.assertEqual(record._chart_type, 'table')
        self.assertEqual(record._chart_url, '')
