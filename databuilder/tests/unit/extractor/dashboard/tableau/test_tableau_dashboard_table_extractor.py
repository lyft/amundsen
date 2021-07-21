# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import logging
import unittest
from typing import Any, Dict

from mock import patch
from pyhocon import ConfigFactory

from databuilder import Scoped
from databuilder.extractor.dashboard.tableau.tableau_dashboard_table_extractor import TableauDashboardTableExtractor
from databuilder.extractor.dashboard.tableau.tableau_dashboard_utils import (
    TableauDashboardAuth, TableauGraphQLApiExtractor,
)

logging.basicConfig(level=logging.INFO)


def mock_query(*_args: Any, **_kwargs: Any) -> Dict[str, Any]:
    return {
        'workbooks': [
            {
                'name': 'Test Workbook',
                'projectName': 'Test Project',
                'upstreamTables': [
                    {
                        'name': 'test_table_1',
                        'schema': 'test_schema_1',
                        'database': {
                            'name': 'test_database_1',
                            'connectionType': 'redshift'
                        }
                    },
                    {
                        'name': 'test_table_2',
                        'schema': 'test_schema_2',
                        'database': {
                            'name': 'test_database_2',
                            'connectionType': 'redshift'
                        }
                    }
                ]
            }
        ]
    }


def mock_token(*_args: Any, **_kwargs: Any) -> str:
    return '123-abc'


class TestTableauDashboardTable(unittest.TestCase):

    @patch.object(TableauDashboardAuth, '_authenticate', mock_token)
    @patch.object(TableauGraphQLApiExtractor, 'execute_query', mock_query)
    def test_dashboard_table_extractor(self) -> None:

        config = ConfigFactory.from_dict({
            'extractor.tableau_dashboard_table.api_base_url': 'api_base_url',
            'extractor.tableau_dashboard_table.api_version': 'tableau_api_version',
            'extractor.tableau_dashboard_table.site_name': 'tableau_site_name',
            'extractor.tableau_dashboard_table.tableau_personal_access_token_name':
                'tableau_personal_access_token_name',
            'extractor.tableau_dashboard_table.tableau_personal_access_token_secret':
                'tableau_personal_access_token_secret',
            'extractor.tableau_dashboard_table.excluded_projects': [],
            'extractor.tableau_dashboard_table.cluster': 'tableau_dashboard_cluster',
            'extractor.tableau_dashboard_table.database': 'tableau_dashboard_database',
            'extractor.tableau_dashboard_table.transformer.timestamp_str_to_epoch.timestamp_format':
                '%Y-%m-%dT%H:%M:%SZ',

        })

        extractor = TableauDashboardTableExtractor()
        extractor.init(Scoped.get_scoped_conf(conf=config, scope=extractor.get_scope()))
        record = extractor.extract()

        self.assertEqual(record._dashboard_id, 'Test Workbook')
        self.assertEqual(record._dashboard_group_id, 'Test Project')
        self.assertEqual(record._product, 'tableau')
        self.assertEqual(record._cluster, 'tableau_dashboard_cluster')
        self.assertEqual(record._table_ids, [
            'tableau_dashboard_database://tableau_dashboard_cluster.test_schema_1/test_table_1',
            'tableau_dashboard_database://tableau_dashboard_cluster.test_schema_2/test_table_2'])


if __name__ == '__main__':
    unittest.main()
