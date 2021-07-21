# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0
import unittest
from typing import Any

from mock import MagicMock, Mock
from pyhocon import ConfigFactory

from databuilder import Scoped
from databuilder.extractor.dashboard.apache_superset.apache_superset_metadata_extractor import (
    ApacheSupersetMetadataExtractor,
)
from databuilder.models.dashboard.dashboard_last_modified import DashboardLastModifiedTimestamp
from databuilder.models.dashboard.dashboard_metadata import DashboardMetadata

dashboard_data_response = {
    'result': {
        'id': 2,
        'changed_on': '2021-05-14 08:41:05.934134',
        'dashboard_title': 'dashboard name',
        'url': '/2',
        'published': 'true'
    }
}


class TestApacheSupersetMetadataExtractor(unittest.TestCase):
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
        return ApacheSupersetMetadataExtractor

    def test_extractor(self) -> None:
        extractor = self._get_extractor()

        extractor.execute_query = Mock(side_effect=[{'ids': [2]}, dashboard_data_response])

        record = extractor.extract()

        self.assertIsInstance(record, DashboardMetadata)
        self.assertEqual(record.dashboard_group, 'dashboard group')
        self.assertEqual(record.dashboard_name, 'dashboard name')
        self.assertEqual(record.description, '')
        self.assertEqual(record.cluster, 'gold')
        self.assertEqual(record.product, 'superset')
        self.assertEqual(record.dashboard_group_id, '1')
        self.assertEqual(record.dashboard_id, '2')
        self.assertEqual(record.dashboard_group_description, 'dashboard group description')
        self.assertEqual(record.created_timestamp, 0)
        self.assertEqual(record.dashboard_group_url, 'http://localhost:8088')
        self.assertEqual(record.dashboard_url, 'http://localhost:8088/2')

        record = extractor.extract()

        self.assertIsInstance(record, DashboardLastModifiedTimestamp)
        self.assertEqual(record._dashboard_group_id, '1')
        self.assertEqual(record._dashboard_id, '2')
        self.assertEqual(record._last_modified_timestamp, 1620981665)
        self.assertEqual(record._product, 'superset')
        self.assertEqual(record._cluster, 'gold')
