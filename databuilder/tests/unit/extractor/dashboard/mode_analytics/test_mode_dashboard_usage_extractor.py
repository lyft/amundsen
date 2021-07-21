# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import unittest

from mock import patch
from pyhocon import ConfigFactory

from databuilder import Scoped
from databuilder.extractor.dashboard.mode_analytics.mode_dashboard_usage_extractor import ModeDashboardUsageExtractor


class TestModeDashboardUsageExtractor(unittest.TestCase):
    def setUp(self) -> None:
        config = ConfigFactory.from_dict({
            'extractor.mode_dashboard_usage.organization': 'amundsen',
            'extractor.mode_dashboard_usage.mode_bearer_token': 'amundsen_bearer_token',
        })
        self.config = config

    def test_extractor_extract_record(self) -> None:
        extractor = ModeDashboardUsageExtractor()
        extractor.init(Scoped.get_scoped_conf(conf=self.config, scope=extractor.get_scope()))

        with patch('databuilder.rest_api.rest_api_query.RestApiQuery._send_request') as mock_request:
            with patch('databuilder.rest_api.mode_analytics.mode_paginated_rest_api_query.ModePaginatedRestApiQuery._post_process'):  # noqa
                mock_request.return_value.json.side_effect = [
                    {
                        'report_stats': [
                            {
                                'report_token': 'ddd',
                                'view_count': 20,
                            }
                        ]
                    },
                    {
                        'reports': [
                            {
                                'token': 'ddd',
                                'space_token': 'ggg',
                            }
                        ]
                    },
                    {
                        'spaces': [
                            {
                                'token': 'ggg',
                                'name': 'dashboard group name',
                                'description': 'dashboard group description'
                            }
                        ]
                    },
                ]

                record = extractor.extract()
                self.assertEqual(record['organization'], 'amundsen')
                self.assertEqual(record['dashboard_id'], 'ddd')
                self.assertEqual(record['accumulated_view_count'], 20)
                self.assertEqual(record['dashboard_group_id'], 'ggg')
                self.assertEqual(record['dashboard_group'], 'dashboard group name')
                self.assertEqual(record['dashboard_group_description'], 'dashboard group description')
                self.assertEqual(record['product'], 'mode')


if __name__ == '__main__':
    unittest.main()
