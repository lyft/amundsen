# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import unittest

from mock import patch
from pyhocon import ConfigFactory

from databuilder import Scoped
from databuilder.extractor.dashboard.mode_analytics.mode_dashboard_queries_extractor import (
    ModeDashboardQueriesExtractor,
)
from databuilder.models.dashboard.dashboard_query import DashboardQuery


class TestModeDashboardLastModifiedTimestampExtractor(unittest.TestCase):
    def setUp(self) -> None:
        config = ConfigFactory.from_dict({
            'extractor.mode_dashboard_query.organization': 'amundsen',
            'extractor.mode_dashboard_query.mode_bearer_token': 'amundsen_bearer_token',
        })
        self.config = config

    def test_extractor_extract_record(self) -> None:
        extractor = ModeDashboardQueriesExtractor()
        extractor.init(Scoped.get_scoped_conf(conf=self.config, scope=extractor.get_scope()))

        with patch('databuilder.rest_api.rest_api_query.RestApiQuery._send_request') as mock_request:
            mock_request.return_value.json.return_value = {
                'queries': [
                    {
                        'space_token': 'ggg',
                        'report_token': 'ddd',
                        'token': 'qqq',
                        'name': 'this query name',
                        'raw_query': 'select 1',
                    }
                ]
            }

            record = next(extractor.extract())
            self.assertIsInstance(record, DashboardQuery)
            self.assertEqual(record._dashboard_group_id, 'ggg')
            self.assertEqual(record._dashboard_id, 'ddd')
            self.assertEqual(record._query_id, 'qqq')
            self.assertEqual(record._query_name, 'this query name')
            self.assertEqual(record._query_text, 'select 1')
            self.assertEqual(record._url, 'https://app.mode.com/amundsen/reports/ddd/queries/qqq')
            self.assertEqual(record._product, 'mode')
            self.assertEqual(record._cluster, 'gold')


if __name__ == '__main__':
    unittest.main()
