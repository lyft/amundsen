# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import unittest
from http import HTTPStatus

from flask import Response

from amundsen_application import create_app
from amundsen_application.api.announcements import v0

local_app = create_app('amundsen_application.config.TestConfig', 'tests/templates')
ANNOUNCEMENT_CLIENT_CLASS = ('amundsen_application.base.examples.'
                             'example_announcement_client.SQLAlchemyAnnouncementClient')


class AnnouncementTest(unittest.TestCase):

    def setUp(self) -> None:
        local_app.config['ANNOUNCEMENT_CLIENT_ENABLED'] = True

    def test_no_client_class(self) -> None:
        """
        Test that Not Implemented error is raised when PREVIEW_CLIENT is None
        :return:
        """
        # Reset side effects of other tests to ensure that the results are the
        # same regardless of execution order
        v0.ANNOUNCEMENT_CLIENT_CLASS = None
        v0.ANNOUNCEMENT_CLIENT_INSTANCE = None

        local_app.config['ANNOUNCEMENT_CLIENT'] = None
        with local_app.test_client() as test:
            response = test.get('/api/announcements/v0/')
            self.assertEqual(response.status_code, HTTPStatus.NOT_IMPLEMENTED)

    @unittest.mock.patch(ANNOUNCEMENT_CLIENT_CLASS + '._get_posts')
    def test_good_client_response(self, mock_get_posts: unittest.mock.Mock) -> None:
        """
        :return:
        """
        local_app.config['ANNOUNCEMENT_CLIENT'] = ANNOUNCEMENT_CLIENT_CLASS
        mock_get_posts.return_value = Response(response='',
                                               status=HTTPStatus.OK)
        with local_app.test_client() as test:
            response = test.get('/api/announcements/v0/')
            self.assertEqual(response.status_code, HTTPStatus.OK)
