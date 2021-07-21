# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import unittest

from mock import patch
from pyhocon import ConfigFactory

from databuilder import Scoped
from databuilder.extractor.dashboard.mode_analytics.mode_dashboard_executions_extractor import (
    ModeDashboardExecutionsExtractor,
)
from databuilder.models.dashboard.dashboard_execution import DashboardExecution


class TestModeDashboardExecutionsExtractor(unittest.TestCase):
    def setUp(self) -> None:
        config = ConfigFactory.from_dict({
            'extractor.mode_dashboard_execution.organization': 'amundsen',
            'extractor.mode_dashboard_execution.mode_bearer_token': 'amundsen_bearer_token',
        })
        self.config = config

    def test_extractor_extract_record(self) -> None:
        extractor = ModeDashboardExecutionsExtractor()
        extractor.init(Scoped.get_scoped_conf(conf=self.config, scope=extractor.get_scope()))

        with patch('databuilder.rest_api.rest_api_query.RestApiQuery._send_request') as mock_request:
            mock_request.return_value.json.return_value = {
                'reports': [
                    {
                        'space_token': 'ggg',
                        'token': 'ddd',
                        'last_run_at': '2021-02-05T21:20:09.019Z',
                        'last_run_state': 'failed',
                    }
                ]
            }

            record = next(extractor.extract())
            self.assertIsInstance(record, DashboardExecution)
            self.assertEqual(record._dashboard_group_id, 'ggg')
            self.assertEqual(record._dashboard_id, 'ddd')
            self.assertEqual(record._execution_timestamp, 1612560009)
            self.assertEqual(record._execution_state, 'failed')
            self.assertEqual(record._product, 'mode')
            self.assertEqual(record._cluster, 'gold')
            self.assertEqual(record._execution_id, '_last_execution')


if __name__ == '__main__':
    unittest.main()
