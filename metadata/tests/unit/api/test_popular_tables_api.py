# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from http import HTTPStatus
from unittest.mock import Mock, patch

from tests.unit.test_basics import BasicTestCase

API_RESPONSE = [{'database': 'ministry',
                 'cluster': 'postgres',
                 'schema': 'ministry',
                 'name': 'wizards',
                 'description': 'all wizards'}]

CLIENT_RESPONSE = [{'database': 'ministry',
                    'cluster': 'postgres',
                    'schema': 'ministry',
                    'name': 'wizards',
                    'description': 'all wizards'}]


class TestPopularTablesAPI(BasicTestCase):
    def setUp(self) -> None:
        super().setUp()

        self.mock_client = patch('metadata_service.api.popular_tables.get_proxy_client')
        self.mock_proxy = self.mock_client.start().return_value = Mock()

    def tearDown(self) -> None:
        super().tearDown()

        self.mock_client.stop()

    def test_should_get_popular_tables_with_default_limits(self) -> None:
        self.mock_proxy.get_popular_tables.return_value = CLIENT_RESPONSE

        response = self.app.test_client().get('popular_tables/')

        self.assertEqual(response.json, {'popular_tables': API_RESPONSE})
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.mock_proxy.get_popular_tables.assert_called_with(num_entries=10,
                                                              user_id=None)

    def test_should_get_popular_tables_with_requested_limits(self) -> None:
        self.mock_proxy.get_popular_tables.return_value = CLIENT_RESPONSE

        self.app.test_client().get('popular_tables/?limit=90')

        self.mock_proxy.get_popular_tables.assert_called_with(num_entries=90,
                                                              user_id=None)
