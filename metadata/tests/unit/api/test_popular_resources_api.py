# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from http import HTTPStatus
from unittest.mock import Mock, patch

from amundsen_common.entity.resource_type import ResourceType

from tests.unit.test_basics import BasicTestCase

API_RESPONSE = [{'database': 'ministry',
                 'cluster': 'postgres',
                 'schema': 'ministry',
                 'name': 'wizards',
                 'description': 'all wizards'}]

CLIENT_RESPONSE = {
    ResourceType.Table.name: [{'database': 'ministry',
                               'cluster': 'postgres',
                               'schema': 'ministry',
                               'name': 'wizards',
                               'description': 'all wizards'}],
    ResourceType.Dashboard.name: []
}

API_RESPONSE_WITH_DASHBOARD = {
    ResourceType.Table.name: [{'database': 'ministry',
                               'cluster': 'postgres',
                               'schema': 'ministry',
                               'name': 'wizards',
                               'description': 'all wizards'}],
    ResourceType.Dashboard.name: [{
        'cluster': 'postgres dashboard',
        'name': 'wizards dashboard',
        'description': 'all wizards dashboard'}]
}

CLIENT_RESPONSE_WITH_DASHBOARD = {
    ResourceType.Table.name: [{'database': 'ministry',
                               'cluster': 'postgres',
                               'schema': 'ministry',
                               'name': 'wizards',
                               'description': 'all wizards'}],
    ResourceType.Dashboard.name: [{
        'cluster': 'postgres dashboard',
        'name': 'wizards dashboard',
        'description': 'all wizards dashboard'}]
}


class TestPopularResourcesAPI(BasicTestCase):
    def setUp(self) -> None:
        super().setUp()

        self.mock_client = patch('metadata_service.api.popular_resources.get_proxy_client')
        self.mock_proxy = self.mock_client.start().return_value = Mock()

    def tearDown(self) -> None:
        super().tearDown()

        self.mock_client.stop()

    def test_should_only_get_popular_tables_with_default_limits(self) -> None:
        self.mock_proxy.get_popular_resources.return_value = CLIENT_RESPONSE

        response = self.app.test_client().get('popular_resources/')

        self.assertEqual(response.json, {ResourceType.Table.name: API_RESPONSE,
                                         ResourceType.Dashboard.name: []}
                         )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.mock_proxy.get_popular_resources.assert_called_with(
            num_entries=10,
            resource_types=["table"],
            user_id=None
        )

    def test_should_get_popular_tables_with_requested_limits(self) -> None:
        self.mock_proxy.get_popular_resources.return_value = CLIENT_RESPONSE

        self.app.test_client().get('popular_resources/?limit=90')

        self.mock_proxy.get_popular_resources.assert_called_with(
            num_entries=90,
            resource_types=["table"],
            user_id=None
        )

    def test_should_get_popular_tables_and_dashboards(self) -> None:
        self.mock_proxy.get_popular_resources.return_value = CLIENT_RESPONSE_WITH_DASHBOARD

        response = self.app.test_client().get('popular_resources/?types=table,dashboard')

        self.assertEqual(response.json, API_RESPONSE_WITH_DASHBOARD)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.mock_proxy.get_popular_resources.assert_called_with(
            num_entries=10,
            resource_types=["table", "dashboard"],
            user_id=None
        )
