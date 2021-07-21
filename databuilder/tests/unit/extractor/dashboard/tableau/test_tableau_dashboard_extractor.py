# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import logging
import unittest
from typing import Any, Dict

from mock import patch
from pyhocon import ConfigFactory

from databuilder import Scoped
from databuilder.extractor.dashboard.tableau.tableau_dashboard_extractor import TableauDashboardExtractor
from databuilder.extractor.dashboard.tableau.tableau_dashboard_utils import (
    TableauDashboardAuth, TableauGraphQLApiExtractor,
)

logging.basicConfig(level=logging.INFO)


def mock_query(*_args: Any, **_kwargs: Any) -> Dict[str, Any]:
    return {
        'workbooks': [
            {
                'id': 'fake-id',
                'name': 'Test Workbook',
                'createdAt': '2020-04-08T05:32:01Z',
                'description': '',
                'projectName': 'Test Project',
                'projectVizportalUrlId': 123,
                'vizportalUrlId': 456
            },
            {
                'id': 'fake-id',
                'name': None,
                'createdAt': '2020-04-08T05:32:01Z',
                'description': '',
                'projectName': None,
                'projectVizportalUrlId': 123,
                'vizportalUrlId': 456
            }
        ]
    }


def mock_token(*_args: Any, **_kwargs: Any) -> str:
    return '123-abc'


class TestTableauDashboardExtractor(unittest.TestCase):

    @patch.object(TableauDashboardAuth, '_authenticate', mock_token)
    @patch.object(TableauGraphQLApiExtractor, 'execute_query', mock_query)
    def test_dashboard_metadata_extractor(self) -> None:

        config = ConfigFactory.from_dict({
            'extractor.tableau_dashboard_metadata.api_base_url': 'https://api_base_url',
            'extractor.tableau_dashboard_metadata.tableau_base_url': 'https://tableau_base_url',
            'extractor.tableau_dashboard_metadata.api_version': 'tableau_api_version',
            'extractor.tableau_dashboard_metadata.site_name': 'tableau_site_name',
            'extractor.tableau_dashboard_metadata.tableau_personal_access_token_name':
                'tableau_personal_access_token_name',
            'extractor.tableau_dashboard_metadata.tableau_personal_access_token_secret':
                'tableau_personal_access_token_secret',
            'extractor.tableau_dashboard_metadata.excluded_projects': [],
            'extractor.tableau_dashboard_metadata.cluster': 'tableau_dashboard_cluster',
            'extractor.tableau_dashboard_metadata.database': 'tableau_dashboard_database',
            'extractor.tableau_dashboard_metadata.transformer.timestamp_str_to_epoch.timestamp_format':
                '%Y-%m-%dT%H:%M:%SZ',

        })

        extractor = TableauDashboardExtractor()
        extractor.init(Scoped.get_scoped_conf(conf=config, scope=extractor.get_scope()))

        record = extractor.extract()
        self.assertEqual(record.dashboard_id, 'Test Workbook')
        self.assertEqual(record.dashboard_name, 'Test Workbook')
        self.assertEqual(record.dashboard_group_id, 'Test Project')
        self.assertEqual(record.dashboard_group, 'Test Project')
        self.assertEqual(record.product, 'tableau')
        self.assertEqual(record.cluster, 'tableau_dashboard_cluster')
        self.assertEqual(record.dashboard_group_url, 'https://tableau_base_url/#/site/tableau_site_name/projects/123')
        self.assertEqual(record.dashboard_url, 'https://tableau_base_url/#/site/tableau_site_name/workbooks/456/views')
        self.assertEqual(record.created_timestamp, 1586323921)

        record = extractor.extract()
        self.assertIsNone(record)

        # Test for Tableau single site deployment
        config = ConfigFactory.from_dict({
            'extractor.tableau_dashboard_metadata.api_base_url': 'https://api_base_url',
            'extractor.tableau_dashboard_metadata.tableau_base_url': 'https://tableau_base_url',
            'extractor.tableau_dashboard_metadata.api_version': 'tableau_api_version',
            'extractor.tableau_dashboard_metadata.site_name': '',
            'extractor.tableau_dashboard_metadata.tableau_personal_access_token_name':
                'tableau_personal_access_token_name',
            'extractor.tableau_dashboard_metadata.tableau_personal_access_token_secret':
                'tableau_personal_access_token_secret',
            'extractor.tableau_dashboard_metadata.excluded_projects': [],
            'extractor.tableau_dashboard_metadata.cluster': 'tableau_dashboard_cluster',
            'extractor.tableau_dashboard_metadata.database': 'tableau_dashboard_database',
            'extractor.tableau_dashboard_metadata.transformer.timestamp_str_to_epoch.timestamp_format':
                '%Y-%m-%dT%H:%M:%SZ',

        })

        extractor = TableauDashboardExtractor()
        extractor.init(Scoped.get_scoped_conf(conf=config, scope=extractor.get_scope()))

        record = extractor.extract()
        self.assertEqual(record.dashboard_id, 'Test Workbook')
        self.assertEqual(record.dashboard_name, 'Test Workbook')
        self.assertEqual(record.dashboard_group_id, 'Test Project')
        self.assertEqual(record.dashboard_group, 'Test Project')
        self.assertEqual(record.product, 'tableau')
        self.assertEqual(record.cluster, 'tableau_dashboard_cluster')
        self.assertEqual(record.dashboard_group_url, 'https://tableau_base_url/#/projects/123')
        self.assertEqual(record.dashboard_url, 'https://tableau_base_url/#/workbooks/456/views')
        self.assertEqual(record.created_timestamp, 1586323921)

        record = extractor.extract()
        self.assertIsNone(record)


if __name__ == '__main__':
    unittest.main()
