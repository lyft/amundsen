# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import unittest
from http import HTTPStatus

from amundsen_common.entity.resource_type import ResourceType

from tests.unit.api.table.table_test_case import TableTestCase

TABLE_URI = 'wizards'

QUERY_RESPONSE = {
    'dashboards': [
        {
            'uri': 'foo_dashboard://gold.foo/bar1',
            'cluster': 'gold',
            'group_name': 'foo',
            'group_url': 'https://foo',
            'product': 'foo',
            'name': 'test dashboard 1',
            'url': 'https://foo.bar',
            'description': 'test dashboard description 1',
            'last_successful_run_timestamp': 1234567890
        },
        {
            'uri': 'foo_dashboard://gold.foo/bar1',
            'cluster': 'gold',
            'group_name': 'foo',
            'group_url': 'https://foo',
            'product': 'foo',
            'name': 'test dashboard 1',
            'url': 'https://foo.bar',
            'description': None,
            'last_successful_run_timestamp': None
        }
    ]
}

API_RESPONSE = {
    'dashboards':
        [
            {
                'group_url': 'https://foo', 'uri': 'foo_dashboard://gold.foo/bar1',
                'last_successful_run_timestamp': 1234567890, 'group_name': 'foo', 'name': 'test dashboard 1',
                'url': 'https://foo.bar', 'description': 'test dashboard description 1', 'cluster': 'gold',
                'product': 'foo'
            },
            {
                'group_url': 'https://foo', 'uri': 'foo_dashboard://gold.foo/bar1',
                'last_successful_run_timestamp': None,
                'group_name': 'foo', 'name': 'test dashboard 1', 'url': 'https://foo.bar', 'description': None,
                'cluster': 'gold', 'product': 'foo'
            }
        ]
}


class TestTableDashboardAPI(TableTestCase):

    def test_get_dashboards_using_table(self) -> None:
        self.mock_proxy.get_resources_using_table.return_value = QUERY_RESPONSE

        response = self.app.test_client().get(f'/table/{TABLE_URI}/dashboard/')
        self.assertEqual(response.json, API_RESPONSE)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.mock_proxy.get_resources_using_table.assert_called_with(id=TABLE_URI,
                                                                     resource_type=ResourceType.Dashboard)


if __name__ == '__main__':
    unittest.main()
