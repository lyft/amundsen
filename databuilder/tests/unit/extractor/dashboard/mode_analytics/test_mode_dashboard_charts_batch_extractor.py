# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import unittest

from mock import patch
from pyhocon import ConfigFactory

from databuilder import Scoped
from databuilder.extractor.dashboard.mode_analytics.mode_dashboard_charts_batch_extractor import (
    ModeDashboardChartsBatchExtractor,
)
from databuilder.models.dashboard.dashboard_chart import DashboardChart


class TestModeDashboardChartsBatchExtractor(unittest.TestCase):
    def setUp(self) -> None:
        config = ConfigFactory.from_dict({
            'extractor.mode_dashboard_chart_batch.organization': 'amundsen',
            'extractor.mode_dashboard_chart_batch.mode_bearer_token': 'amundsen_bearer_token',
        })
        self.config = config

    def test_dashboard_chart_extractor_empty_record(self) -> None:
        extractor = ModeDashboardChartsBatchExtractor()
        extractor.init(Scoped.get_scoped_conf(conf=self.config, scope=extractor.get_scope()))

        with patch('databuilder.rest_api.rest_api_query.RestApiQuery._send_request') as mock_request:
            mock_request.return_value.json.return_value = {'charts': []}
            record = extractor.extract()
            self.assertIsNone(record)

    def test_dashboard_chart_extractor_actual_record(self) -> None:
        extractor = ModeDashboardChartsBatchExtractor()
        extractor.init(Scoped.get_scoped_conf(conf=self.config, scope=extractor.get_scope()))

        with patch('databuilder.rest_api.rest_api_query.RestApiQuery._send_request') as mock_request:
            mock_request.return_value.json.return_value = {
                'charts': [
                    {
                        'space_token': 'ggg',
                        'report_token': 'ddd',
                        'query_token': 'yyy',
                        'token': 'xxx',
                        'chart_title': 'some chart',
                        'chart_type': 'bigNumber'
                    }
                ]
            }

            record = extractor.extract()
            self.assertIsInstance(record, DashboardChart)
            self.assertEqual(record._dashboard_group_id, 'ggg')
            self.assertEqual(record._dashboard_id, 'ddd')
            self.assertEqual(record._query_id, 'yyy')
            self.assertEqual(record._chart_id, 'xxx')
            self.assertEqual(record._chart_name, 'some chart')
            self.assertEqual(record._chart_type, 'bigNumber')
            self.assertEqual(record._product, 'mode')
            self.assertEqual(record._cluster, 'gold')


if __name__ == '__main__':
    unittest.main()
