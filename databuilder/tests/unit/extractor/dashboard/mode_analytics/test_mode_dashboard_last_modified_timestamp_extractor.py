# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import unittest

from mock import patch
from pyhocon import ConfigFactory

from databuilder import Scoped
from databuilder.extractor.dashboard.mode_analytics.mode_dashboard_last_modified_timestamp_extractor import (
    ModeDashboardLastModifiedTimestampExtractor,
)
from databuilder.models.dashboard.dashboard_last_modified import DashboardLastModifiedTimestamp


class TestModeDashboardLastModifiedTimestampExtractor(unittest.TestCase):
    def setUp(self) -> None:
        config = ConfigFactory.from_dict({
            'extractor.mode_dashboard_last_modified_timestamp_execution.organization': 'amundsen',
            'extractor.mode_dashboard_last_modified_timestamp_execution.mode_bearer_token': 'amundsen_bearer_token',
        })
        self.config = config

    def test_extractor_extract_record(self) -> None:
        extractor = ModeDashboardLastModifiedTimestampExtractor()
        extractor.init(Scoped.get_scoped_conf(conf=self.config, scope=extractor.get_scope()))

        with patch('databuilder.rest_api.rest_api_query.RestApiQuery._send_request') as mock_request:
            mock_request.return_value.json.return_value = {
                'reports': [
                    {
                        'space_token': 'ggg',
                        'token': 'ddd',
                        'edited_at': '2021-02-05T21:20:09.019Z',
                    }
                ]
            }

            record = next(extractor.extract())
            self.assertIsInstance(record, DashboardLastModifiedTimestamp)
            self.assertEqual(record._dashboard_group_id, 'ggg')
            self.assertEqual(record._dashboard_id, 'ddd')
            self.assertEqual(record._last_modified_timestamp, 1612560009)
            self.assertEqual(record._product, 'mode')
            self.assertEqual(record._cluster, 'gold')


if __name__ == '__main__':
    unittest.main()
