# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import json
import unittest
from unittest.mock import Mock

from http import HTTPStatus
from typing import Dict, List, Optional

from flask import jsonify, make_response, Response

from amundsen_application import create_app
from amundsen_application.api.exceptions import MailClientNotImplemented
from amundsen_application.api.utils.notification_utils import get_mail_client, \
    get_notification_html, get_notification_subject, send_notification, NotificationType
from amundsen_application.base.base_mail_client import BaseMailClient

local_app = create_app('amundsen_application.config.TestConfig', 'tests/templates')
local_no_notification_app = create_app('amundsen_application.config.TestNotificationsDisabledConfig', 'tests/templates')


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


class NotificationUtilsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_table_key = 'db://cluster.schema/table'

    def test_validate_resource_path_none(self) -> None:
        """
        Test Exception is raised if resource_path is None
        :return:
        """
        with local_app.app_context():
            self.assertRaises(Exception,
                              get_notification_html,
                              notification_type=NotificationType.OWNER_REMOVED,
                              options={'resource_name': 'testtable'},
                              sender='test@test.com')

    def test_validate_resource_path_bad_syntax(self) -> None:
        """
        Test Exception is raised if resource_path violates leading '/' syntax
        :return:
        """
        with local_app.app_context():
            self.assertRaises(Exception,
                              get_notification_html,
                              notification_type=NotificationType.OWNER_REMOVED,
                              options={'resource_name': 'testtable', 'resource_path': 'testpath'},
                              sender='test@test.com')

    def test_get_notification_html_bad_base_url(self) -> None:
        """
        Test Exception is raised if configured FRONTEND_BASE violates no trailing '/' syntax
        :return:
        """
        with local_app.app_context():
            temp = local_app.config['FRONTEND_BASE']
            local_app.config['FRONTEND_BASE'] = 'garbagetest_rewrite_file_to_setup_teardown_each_case/'
            self.assertRaises(Exception,
                              get_notification_html,
                              notification_type=NotificationType.OWNER_ADDED,
                              options={'resource_name': 'testtable', 'resource_path': '/testpath'},
                              sender='test@test.com')
            local_app.config['FRONTEND_BASE'] = temp

    def test_get_notification_html_no_resource_name(self) -> None:
        """
        Test Exception is raised if resource_name is not provided
        :return:
        """
        with local_app.app_context():
            self.assertRaises(Exception,
                              get_notification_html,
                              notification_type=NotificationType.OWNER_ADDED,
                              options={'resource_path': '/testpath'},
                              sender='test@test.com')

    def test_get_notification_html_unsupported_type(self) -> None:
        """
        Test Exception is raised if notification_type is not supported
        :return:
        """
        with local_app.app_context():
            self.assertRaises(Exception,
                              get_notification_html,
                              notification_type='invalid_type',
                              options={'resource_name': 'testtable', 'resource_path': '/testpath'},
                              sender='test@test.com')

    def test_get_notification_html_added_success(self) -> None:
        """
        Test successful generation of html for 'added' notification email
        :return:
        """
        test_sender = 'test@test.com'
        test_options = {'resource_name': 'testtable', 'resource_path': '/testpath'}

        with local_app.app_context():
            html = get_notification_html(notification_type=NotificationType.OWNER_ADDED,
                                         options=test_options,
                                         sender=test_sender)
        expectedHTML = ('Hello,<br/><br/>You have been added to the owners list of the '
                        '<a href="http://0.0.0.0:5000/testpath?source=notification">testtable</a>'
                        ' dataset by test@test.com.<br/><br/>What is expected of you?<br/>As an owner, you take an '
                        'important part in making sure that the datasets you own can be used as swiftly as possible '
                        'across the company.<br/>Make sure the metadata is correct and up to date.<br/><br/>If you '
                        'think you are not the best person to own this dataset and know someone who might be, please '
                        'contact this person and ask them if they want to replace you. It is important that we keep '
                        'multiple owners for each dataset to ensure continuity.<br/><br/>Thanks,<br/>Amundsen Team')
        self.assertEqual(html, expectedHTML)

    def test_get_notification_html_removed_success(self) -> None:
        """
        Test successful generation of html for 'removed' notification email
        :return:
        """
        test_sender = 'test@test.com'
        test_options = {'resource_name': 'testtable', 'resource_path': '/testpath'}

        with local_app.app_context():
            html = get_notification_html(notification_type=NotificationType.OWNER_REMOVED,
                                         options=test_options,
                                         sender=test_sender)
        expectedHTML = ('Hello,<br/><br/>You have been removed from the owners list of the '
                        '<a href="http://0.0.0.0:5000/testpath?source=notification">testtable</a> dataset by'
                        ' test@test.com.<br/><br/>If you think you have been incorrectly removed as an owner,'
                        ' add yourself back to the owners list.<br/><br/>Thanks,<br/>Amundsen Team')
        self.assertEqual(html, expectedHTML)

    def test_get_notification_html_requested_success_all_fields(self) -> None:
        """
        Test successful generation of html for 'requested' notification email using
        all required and optional fields
        :return:
        """
        test_sender = 'test@test.com'
        test_options = {
            'resource_name': 'testtable',
            'resource_path': '/testpath',
            'description_requested': True,
            'fields_requested': True,
            'comment': 'Test Comment'
        }
        with local_app.app_context():
            html = get_notification_html(notification_type=NotificationType.METADATA_REQUESTED,
                                         options=test_options,
                                         sender=test_sender)
        expectedHTML = ('Hello,<br/><br/>test@test.com is trying to use '
                        '<a href="http://0.0.0.0:5000/testpath?source=notification">testtable</a>, '
                        'and requests improved table and column descriptions.<br/><br/>test@test.com has included the '
                        'following information with their request:<br/>Test Comment<br/><br/>Please visit the provided '
                        'link and improve descriptions on that resource.<br/><br/>Thanks,<br/>Amundsen Team')
        self.assertEqual(html, expectedHTML)

    def test_get_notification_html_requested_success_table_only(self) -> None:
        """
        Test successful generation of html for 'requested' notification email using
        all required fields and 'description_requested' optional field
        :return:
        """
        test_sender = 'test@test.com'
        test_options = {
            'resource_name': 'testtable',
            'resource_path': '/testpath',
            'description_requested': True,
        }

        with local_app.app_context():
            html = get_notification_html(notification_type=NotificationType.METADATA_REQUESTED,
                                         options=test_options,
                                         sender=test_sender)
        expectedHTML = ('Hello,<br/><br/>test@test.com is trying to use '
                        '<a href="http://0.0.0.0:5000/testpath?source=notification">testtable</a>, and requests '
                        'an improved table description.<br/><br/>Please visit the provided link and improve '
                        'descriptions on that resource.<br/><br/>Thanks,<br/>Amundsen Team')
        self.assertEqual(html, expectedHTML)

    def test_get_notification_html_requested_success_columns_only(self) -> None:
        """
        Test successful generation of html for 'requested' notification email using
        all required fields and 'fields_requested' optional field
        :return:
        """
        test_sender = 'test@test.com'
        test_options = {
            'resource_name': 'testtable',
            'resource_path': '/testpath',
            'fields_requested': True,
        }

        with local_app.app_context():
            html = get_notification_html(notification_type=NotificationType.METADATA_REQUESTED,
                                         options=test_options,
                                         sender=test_sender)
        expectedHTML = ('Hello,<br/><br/>test@test.com is trying to use '
                        '<a href="http://0.0.0.0:5000/testpath?source=notification">testtable</a>, and requests '
                        'improved column descriptions.<br/><br/>Please visit the provided link and improve '
                        'descriptions on that resource.<br/><br/>Thanks,<br/>Amundsen Team')
        self.assertEqual(html, expectedHTML)

    def test_get_notification_html_requested_success_no_optional_options(self) -> None:
        """
        Test successful generation of html for 'requested' notification email using
        all required fields and no optional fields
        :return:
        """
        test_sender = 'test@test.com'
        test_options = {
            'resource_name': 'testtable',
            'resource_path': '/testpath',
        }

        with local_app.app_context():
            html = get_notification_html(notification_type=NotificationType.METADATA_REQUESTED,
                                         options=test_options,
                                         sender=test_sender)
        expectedHTML = ('Hello,<br/><br/>test@test.com is trying to use '
                        '<a href="http://0.0.0.0:5000/testpath?source=notification">testtable</a>, and requests '
                        'more information about that resource.<br/><br/>Please visit the provided link and improve '
                        'descriptions on that resource.<br/><br/>Thanks,<br/>Amundsen Team')
        self.assertEqual(html, expectedHTML)

    def test_get_notification_subject_added(self) -> None:
        """
        Test successful executed of get_notification_subject for the OWNER_ADDED notification type
        :return:
        """
        result = get_notification_subject(notification_type=NotificationType.OWNER_ADDED,
                                          options={'resource_name': 'testtable'})
        self.assertEqual(result, 'You are now an owner of testtable')

    def test_get_notification_subject_removed(self) -> None:
        """
        Test successful executed of get_notification_subject for the OWNER_REMOVED notification type
        :return:
        """
        result = get_notification_subject(notification_type=NotificationType.OWNER_REMOVED,
                                          options={'resource_name': 'testtable'})
        self.assertEqual(result, 'You have been removed as an owner of testtable')

    def test_get_notification_subject_edited(self) -> None:
        """
        Test successful executed of get_notification_subject for the METADATA_EDITED notification type
        :return:
        """
        result = get_notification_subject(notification_type=NotificationType.METADATA_EDITED,
                                          options={'resource_name': 'testtable'})
        self.assertEqual(result, 'Your dataset testtable\'s metadata has been edited')

    def test_get_notification_subject_requested(self) -> None:
        """
        Test successful executed of get_notification_subject for the METADATA_REQUESTED notification type
        :return:
        """
        result = get_notification_subject(notification_type=NotificationType.METADATA_REQUESTED,
                                          options={'resource_name': 'testtable'})
        self.assertEqual(result, 'Request for metadata on testtable')

    def test_get_notification_subject_unsupported_type(self) -> None:
        """
        Test Exception is raised if notification_type is not supported
        :return:
        """
        with local_app.app_context():
            self.assertRaises(Exception,
                              get_notification_subject,
                              notification_type='invalid_type',
                              options={'resource_name': 'testtable'})

    def test_get_mail_client_success(self) -> None:
        """
        Test get_mail_client returns the configured mail client if one is configured
        :return:
        """
        with local_app.app_context():
            local_app.config['MAIL_CLIENT'] = unittest.mock.Mock()
            self.assertEqual(get_mail_client(), local_app.config['MAIL_CLIENT'])

    def test_get_mail_client_error(self) -> None:
        """
        Test get_mail_client raised MailClientNotImplemented if no mail client is configured
        :return:
        """
        with local_app.app_context():
            self.assertRaises(MailClientNotImplemented, get_mail_client)

    def test_send_notification_disabled(self) -> None:
        """
        Test send_notification fails gracefully if notifications are not enabled
        :return:
        """
        with local_no_notification_app.app_context():
            response = send_notification(
                notification_type=NotificationType.OWNER_ADDED,
                options={},
                recipients=['test@test.com'],
                sender='test2@test.com'
            )
            self.assertEqual(response.status_code, HTTPStatus.ACCEPTED)

    @unittest.mock.patch('amundsen_application.api.utils.notification_utils.get_notification_html')
    @unittest.mock.patch('amundsen_application.api.utils.notification_utils.get_notification_subject')
    @unittest.mock.patch('amundsen_application.api.utils.notification_utils.get_mail_client')
    def test_send_notification_success(self,
                                       get_mail_client: Mock,
                                       get_notif_subject: Mock,
                                       get_notif_html: Mock) -> None:
        """
        Test successful execution of send_notification
        :return:
        """
        status_codes = [HTTPStatus.OK, HTTPStatus.ACCEPTED]

        for status_code in status_codes:
            with self.subTest():
                with local_app.app_context():
                    get_mail_client.return_value = MockMailClient(status_code=status_code)
                    get_notif_subject.return_value = 'Test Subject'
                    get_notif_html.return_value = '<div>test html</div>'

                    test_recipients = ['test@test.com']
                    test_sender = 'test2@test.com'
                    test_notification_type = NotificationType.OWNER_ADDED
                    test_options: Dict = {}

                    response = send_notification(
                        notification_type=test_notification_type,
                        options=test_options,
                        recipients=test_recipients,
                        sender=test_sender
                    )

                    get_mail_client.assert_called
                    get_notif_subject.assert_called_with(notification_type=test_notification_type,
                                                         options=test_options)
                    get_notif_html.assert_called_with(notification_type=test_notification_type,
                                                      options=test_options,
                                                      sender=test_sender)
                    self.assertTrue(200 <= response.status_code <= 300)

    @unittest.mock.patch('amundsen_application.api.utils.notification_utils.get_notification_html')
    @unittest.mock.patch('amundsen_application.api.utils.notification_utils.get_notification_subject')
    @unittest.mock.patch('amundsen_application.api.utils.notification_utils.get_mail_client')
    def test_remove_sender_from_notification(self,
                                             get_mail_client: Mock,
                                             get_notif_subject: Mock,
                                             get_notif_html: Mock) -> None:
        """
        Test sender is removed if they exist in recipients
        :return:
        """
        with local_app.app_context():
            mock_client = MockMailClient(status_code=HTTPStatus.OK)
            with unittest.mock.patch.object(mock_client, "send_email") as mock_send_email:

                get_mail_client.return_value = mock_client

                mock_subject = 'Test Subject'
                get_notif_subject.return_value = mock_subject

                mock_html = '<div>test html</div>'
                get_notif_html.return_value = mock_html

                test_sender = 'test@test.com'
                test_recipients = [test_sender, 'test2@test.com']
                test_notification_type = NotificationType.OWNER_ADDED
                test_options: Dict = {}
                expected_recipients = ['test2@test.com']

                send_notification(
                    notification_type=test_notification_type,
                    options=test_options,
                    recipients=test_recipients,
                    sender=test_sender
                )
                mock_send_email.assert_called_with(
                    html=mock_html,
                    subject=mock_subject,
                    optional_data={'email_type': test_notification_type},
                    recipients=expected_recipients,
                    sender=test_sender
                )

    def test_no_recipients_for_notification(self) -> None:
        """
        Test 200 response with appropriate message if no recipients exist
        :return:
        """
        with local_app.app_context():
            response = send_notification(
                notification_type=NotificationType.OWNER_ADDED,
                options={},
                recipients=[],
                sender='test@test.com'
            )
            data = json.loads(response.data)
            self.assertEqual(response.status_code, HTTPStatus.OK)
            self.assertEqual(data.get('msg'), 'No valid recipients exist for notification, notification was not sent.')
