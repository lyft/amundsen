# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import unittest

from http import HTTPStatus
from typing import List

import flask

from amundsen_application.base.base_announcement_client import BaseAnnouncementClient
from amundsen_application.models.announcements import Announcements

app = flask.Flask(__name__)
app.config.from_object('amundsen_application.config.LocalConfig')


class MockClient(BaseAnnouncementClient):
    def __init__(self, posts: List) -> None:
        self.posts = posts
        self.announcements = Announcements(posts=posts)

    def get_posts(self) -> Announcements:
        return self.announcements


class MockExceptionClient(BaseAnnouncementClient):
    def __init__(self) -> None:
        pass

    def get_posts(self) -> Announcements:
        raise Exception('Simulate client raising exception')


class AnnouncementClientTest(unittest.TestCase):
    def test_get_posts_raise_exception(self) -> None:
        """
        Test catching any exception raised in get_posts(), which should result in
        a response with 500 error
        :return:
        """
        with app.test_request_context():
            response = MockExceptionClient()._get_posts()
            self.assertEqual(response.status_code, HTTPStatus.INTERNAL_SERVER_ERROR)

    def test_get_posts_invalid_posts_no_date(self) -> None:
        """
        Test get_posts() failure if the client returns an object that does not match
        AnnouncementsSchema
        :return:
        """
        with app.test_request_context():
            invalid_posts = [{'test': 'This is not a valid list of posts'}]
            response = MockClient(invalid_posts)._get_posts()
            self.assertEqual(response.status_code, HTTPStatus.INTERNAL_SERVER_ERROR)

    def test_get_posts_invalid_posts_no_title(self) -> None:
        """
        Test get_posts() failure if the client returns an object that does not match
        AnnouncementsSchema
        :return:
        """
        with app.test_request_context():
            invalid_posts = [{'date': 'December 31, 1999', 'not_a_title': 'This is still invalid'}]
            response = MockClient(invalid_posts)._get_posts()
            self.assertEqual(response.status_code, HTTPStatus.INTERNAL_SERVER_ERROR)

    def test_get_posts_success(self) -> None:
        """
        Test get_posts() success
        :return:
        """
        with app.test_request_context():
            success_posts = [
                {
                    'title': 'Test Title',
                    'date': 'December 31, 1999',
                    'html_content': 'content',
                }
            ]
            response = MockClient(success_posts)._get_posts()
            self.assertEqual(response.status_code, HTTPStatus.OK)
