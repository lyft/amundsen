# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import unittest
from unittest.mock import Mock

from http import HTTPStatus
from typing import Dict, List, Optional

from flask import Response, jsonify, make_response

from amundsen_application import create_app
from amundsen_application.base.base_mail_client import BaseMailClient


class MockMailClient(BaseMailClient):
    def __init__(self, status_code: int, recipients: List = []) -> None:
        self.status_code = status_code

    def send_email(self,
                   html: str,
                   subject: str,
                   optional_data: Optional[Dict] = None,
                   recipients: Optional[List[str]] = None,
                   sender: Optional[str] = None) -> Response:
        return make_response(jsonify({}), self.status_code)


class MockBadClient(BaseMailClient):
    def __init__(self) -> None:
        pass

    def send_email(self,
                   html: str,
                   subject: str,
                   optional_data: Optional[Dict] = None,
                   recipients: Optional[List[str]] = None,
                   sender: Optional[str] = None) -> Response:
        raise Exception('Bad client')


class MailTest(unittest.TestCase):
    def setUp(self) -> None:
        self.app = create_app('amundsen_application.config.TestConfig', 'tests/templates')
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self) -> None:
        self.app_context.pop()

    def test_feedback_client_not_implemented(self) -> None:
        """
        Test mail client is not implemented, and endpoint should return appropriate code
        :return:
        """
        with self.app.test_client() as test:
            response = test.post('/api/mail/v0/feedback', json={
                'rating': '10', 'comment': 'test'
            })
            self.assertEqual(response.status_code, HTTPStatus.NOT_IMPLEMENTED)

    def test_feedback_client_success(self) -> None:
        """
        Test mail client success
        :return:
        """
        status_codes = [HTTPStatus.OK, HTTPStatus.ACCEPTED]
        for status_code in status_codes:
            self.app.config['MAIL_CLIENT'] = MockMailClient(status_code=status_code)
            with self.subTest():
                with self.app.test_client() as test:
                    response = test.post('/api/mail/v0/feedback', json={
                        'rating': '10', 'comment': 'test'
                    })
                    self.assertTrue(200 <= response.status_code <= 300)

    def test_feedback_client_raise_exception(self) -> None:
        """
        Test failure due to incorrect implementation of base_mail_client
        :return:
        """
        self.app.config['MAIL_CLIENT'] = MockBadClient()
        with self.app.test_client() as test:
            response = test.post('/api/mail/v0/feedback', json={
                'rating': '10', 'comment': 'test'
            })
            self.assertEqual(response.status_code, HTTPStatus.INTERNAL_SERVER_ERROR)

    def test_feedback_client_propagate_status_code(self) -> None:
        """
        Test that specific status codes returned from a custom mail client propagate,
        so that they may be appropriately logged and surfaced to the React application
        :return:
        """
        expected_code = HTTPStatus.BAD_REQUEST
        self.app.config['MAIL_CLIENT'] = MockMailClient(status_code=expected_code)
        with self.app.test_client() as test:
            response = test.post('/api/mail/v0/feedback', json={
                'rating': '10', 'comment': 'test'
            })
            self.assertEqual(response.status_code, expected_code)

    @unittest.mock.patch('amundsen_application.api.mail.v0.send_notification')
    def test_notification_endpoint_calls_send_notification(self, send_notification_mock: Mock) -> None:
        """
        Test that the endpoint calls send_notification with the correct information
        from the request json
        :return:
        """
        test_recipients = ['test@test.com']
        test_notification_type = 'added'
        test_options: Dict = {}

        with self.app.test_client() as test:
            test.post('/api/mail/v0/notification', json={
                'recipients': test_recipients,
                'notificationType': test_notification_type,
                'options': test_options,
            })
            send_notification_mock.assert_called_with(
                notification_type=test_notification_type,
                options=test_options,
                recipients=test_recipients,
                sender=self.app.config['AUTH_USER_METHOD'](self.app).email
            )

    @unittest.mock.patch('amundsen_application.api.mail.v0.send_notification')
    def test_notification_endpoint_fails_missing_notification_type(self, send_notification_mock: Mock) -> None:
        """
        Test that the endpoint fails if notificationType is not provided in the
        request json
        :return:
        """
        test_recipients = ['test@test.com']
        test_sender = 'test2@test.com'
        test_options: Dict = {}

        with self.app.test_client() as test:
            response = test.post('/api/mail/v0/notification', json={
                'recipients': test_recipients,
                'sender': test_sender,
                'options': test_options,
            })
            self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)
            self.assertFalse(send_notification_mock.called)

    @unittest.mock.patch('amundsen_application.api.mail.v0.send_notification')
    def test_notification_endpoint_fails_with_exception(self, send_notification_mock: Mock) -> None:
        """
        Test that the endpoint returns 500 exception when error occurs
        and that send_notification is not called
        :return:
        """
        with self.app.test_client() as test:
            # generates error
            response = test.post('/api/mail/v0/notification', json=None)

            self.assertEqual(response.status_code, HTTPStatus.INTERNAL_SERVER_ERROR)
            self.assertFalse(send_notification_mock.called)
