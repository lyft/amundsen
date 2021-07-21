# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import logging
import unittest
from typing import Any, Dict

from mock import patch
from pyhocon import ConfigFactory

from databuilder import Scoped
from databuilder.extractor.dashboard.tableau.tableau_dashboard_last_modified_extractor import (
    TableauDashboardLastModifiedExtractor,
)
from databuilder.extractor.dashboard.tableau.tableau_dashboard_utils import (
    TableauDashboardAuth, TableauGraphQLApiExtractor,
)

logging.basicConfig(level=logging.INFO)


def mock_query(*_args: Any, **_kwargs: Any) -> Dict[str, Any]:
    return {
        'workbooks': [
            {
                'id': 'fake-workbook-id',
                'name': 'Test Workbook',
                'projectName': 'Test Project',
                'updatedAt': '2020-08-04T20:16:05Z',
                'projectVizportalUrlId': 123,
                'vizportalUrlId': 456
            },
            {
                'id': 'fake-workbook-id',
                'name': None,
                'projectName': None,
                'createdAt': '2020-08-04T20:16:05Z',
                'projectVizportalUrlId': 123,
                'vizportalUrlId': 456
            }
        ]
    }


def mock_token(*_args: Any, **_kwargs: Any) -> str:
    return '123-abc'


class TestTableauDashboardLastModified(unittest.TestCase):

    @patch.object(TableauDashboardAuth, '_authenticate', mock_token)
    @patch.object(TableauGraphQLApiExtractor, 'execute_query', mock_query)
    def test_dashboard_last_modified_extractor(self) -> None:

        config = ConfigFactory.from_dict({
            'extractor.tableau_dashboard_last_modified.api_base_url': 'api_base_url',
            'extractor.tableau_dashboard_last_modified.api_version': 'tableau_api_version',
            'extractor.tableau_dashboard_last_modified.site_name': 'tableau_site_name',
            'extractor.tableau_dashboard_last_modified.tableau_personal_access_token_name':
                'tableau_personal_access_token_name',
            'extractor.tableau_dashboard_last_modified.tableau_personal_access_token_secret':
                'tableau_personal_access_token_secret',
            'extractor.tableau_dashboard_last_modified.excluded_projects': [],
            'extractor.tableau_dashboard_last_modified.cluster': 'tableau_dashboard_cluster',
            'extractor.tableau_dashboard_last_modified.database': 'tableau_dashboard_database',
            'extractor.tableau_dashboard_last_modified.transformer.timestamp_str_to_epoch.timestamp_format':
                '%Y-%m-%dT%H:%M:%SZ',

        })

        extractor = TableauDashboardLastModifiedExtractor()
        extractor.init(Scoped.get_scoped_conf(conf=config, scope=extractor.get_scope()))

        record = extractor.extract()
        self.assertEqual(record._dashboard_id, 'Test Workbook')
        self.assertEqual(record._dashboard_group_id, 'Test Project')
        self.assertEqual(record._product, 'tableau')
        self.assertEqual(record._cluster, 'tableau_dashboard_cluster')
        self.assertEqual(record._last_modified_timestamp, 1596572165)

        record = extractor.extract()
        self.assertIsNone(record)


if __name__ == '__main__':
    unittest.main()
