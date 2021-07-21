# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import logging
import unittest
from typing import Any, Dict

from mock import patch
from pyhocon import ConfigFactory

from databuilder import Scoped
from databuilder.extractor.dashboard.tableau.tableau_dashboard_query_extractor import TableauDashboardQueryExtractor
from databuilder.extractor.dashboard.tableau.tableau_dashboard_utils import (
    TableauDashboardAuth, TableauGraphQLApiExtractor,
)

logging.basicConfig(level=logging.INFO)


def mock_query(*_args: Any, **_kwargs: Any) -> Dict[str, Any]:
    return {
        'customSQLTables': [
            {
                'id': 'fake-query-id',
                'name': 'Test Query',
                'query': 'SELECT * FROM foo',
                'downstreamWorkbooks': [
                    {
                        'name': 'Test Workbook',
                        'projectName': 'Test Project'
                    }
                ]
            }
        ]
    }


def mock_token(*_args: Any, **_kwargs: Any) -> str:
    return '123-abc'


class TestTableauDashboardQuery(unittest.TestCase):

    @patch.object(TableauDashboardAuth, '_authenticate', mock_token)
    @patch.object(TableauGraphQLApiExtractor, 'execute_query', mock_query)
    def test_dashboard_query_extractor(self) -> None:

        config = ConfigFactory.from_dict({
            'extractor.tableau_dashboard_query.api_base_url': 'api_base_url',
            'extractor.tableau_dashboard_query.api_version': 'tableau_api_version',
            'extractor.tableau_dashboard_query.site_name': 'tableau_site_name',
            'extractor.tableau_dashboard_query.tableau_personal_access_token_name':
                'tableau_personal_access_token_name',
            'extractor.tableau_dashboard_query.tableau_personal_access_token_secret':
                'tableau_personal_access_token_secret',
            'extractor.tableau_dashboard_query.excluded_projects': [],
            'extractor.tableau_dashboard_query.cluster': 'tableau_dashboard_cluster',
            'extractor.tableau_dashboard_query.database': 'tableau_dashboard_database',
            'extractor.tableau_dashboard_query.transformer.timestamp_str_to_epoch.timestamp_format':
                '%Y-%m-%dT%H:%M:%SZ',

        })

        extractor = TableauDashboardQueryExtractor()
        extractor.init(Scoped.get_scoped_conf(conf=config, scope=extractor.get_scope()))
        record = extractor.extract()

        self.assertEqual(record._query_name, 'Test Query')
        self.assertEqual(record._query_text, 'SELECT * FROM foo')
        self.assertEqual(record._dashboard_id, 'Test Workbook')
        self.assertEqual(record._dashboard_group_id, 'Test Project')


if __name__ == '__main__':
    unittest.main()
