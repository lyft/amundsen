# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import unittest

from mock import patch
from pyhocon import ConfigFactory

from databuilder import Scoped
from databuilder.extractor.dashboard.mode_analytics.mode_dashboard_owner_extractor import ModeDashboardOwnerExtractor
from databuilder.models.dashboard.dashboard_metadata import DashboardMetadata
from databuilder.models.dashboard.dashboard_owner import DashboardOwner


class TestModeDashboardLastModifiedTimestampExtractor(unittest.TestCase):
    def setUp(self) -> None:
        config = ConfigFactory.from_dict({
            'extractor.mode_dashboard_owner.organization': 'amundsen',
            'extractor.mode_dashboard_owner.mode_bearer_token': 'amundsen_bearer_token',
        })
        self.config = config

    def test_extractor_extract_record(self) -> None:
        extractor = ModeDashboardOwnerExtractor()
        extractor.init(Scoped.get_scoped_conf(conf=self.config, scope=extractor.get_scope()))

        with patch('databuilder.rest_api.rest_api_query.RestApiQuery._send_request') as mock_request:
            mock_request.return_value.json.return_value = {
                'reports': [
                    {
                        'space_token': 'ggg',
                        'token': 'ddd',
                        'creator_email': 'amundsen@abc.com',
                    }
                ]
            }

            record = extractor.extract()
            self.assertIsInstance(record, DashboardOwner)
            self.assertEqual(record.owner_emails, ['amundsen@abc.com'])
            self.assertEqual(record.start_label, DashboardMetadata.DASHBOARD_NODE_LABEL)
            self.assertEqual(record.start_key, 'mode_dashboard://gold.ggg/ddd')


if __name__ == '__main__':
    unittest.main()
