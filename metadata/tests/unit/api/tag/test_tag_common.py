# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from http import HTTPStatus
from unittest.mock import MagicMock

from amundsen_common.entity.resource_type import ResourceType
from flask import current_app

from metadata_service import create_app
from metadata_service.api.tag import TagCommon
from metadata_service.entity.badge import Badge
from tests.unit.api.dashboard.dashboard_test_case import DashboardTestCase

BADGE_NAME = 'foo'
TAG_NAME = 'bar'


class TestDashboardTagAPI(DashboardTestCase):
    """
        Test the service if it can standup
        """

    def setUp(self) -> None:
        self.app = create_app(
            config_module_class='metadata_service.config.LocalConfig')
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self) -> None:
        self.app_context.pop()

    def test_app_exists(self) -> None:
        self.assertFalse(current_app is None)

    def test_block_tag_on_reserved_badge_value(self) -> None:
        self.app.config['WHITELIST_BADGES'] = [Badge(badge_name=BADGE_NAME,
                                                     category='table_status')]

        mock_proxy = MagicMock()

        tag_common = TagCommon(client=mock_proxy)
        response = tag_common.put(id='',
                                  resource_type=ResourceType.Dashboard,
                                  tag=BADGE_NAME,
                                  tag_type='default')

        self.assertEqual(response[1], HTTPStatus.CONFLICT)

    def test_tag_on_unreserved_badge_value(self) -> None:
        self.app.config['WHITELIST_BADGES'] = [Badge(badge_name=BADGE_NAME,
                                                     category='table_status')]

        mock_proxy = MagicMock()

        tag_common = TagCommon(client=mock_proxy)
        response = tag_common.put(id='',
                                  resource_type=ResourceType.Dashboard,
                                  tag=TAG_NAME,
                                  tag_type='default')

        self.assertEqual(response[1], HTTPStatus.OK)

    def test_badge_on_reserved_badge_value(self) -> None:
        self.app.config['WHITELIST_BADGES'] = [Badge(badge_name=BADGE_NAME,
                                                     category='table_status')]

        mock_proxy = MagicMock()
        tag_common = TagCommon(client=mock_proxy)
        response = tag_common.put(id='',
                                  resource_type=ResourceType.Dashboard,
                                  tag=BADGE_NAME,
                                  tag_type='badge')
        self.assertEqual(response[1], HTTPStatus.NOT_ACCEPTABLE)
