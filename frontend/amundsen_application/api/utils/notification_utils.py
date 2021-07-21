# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import logging

from http import HTTPStatus
from enum import Enum

from flask import current_app as app
from flask import jsonify, make_response, Response
from typing import Dict, List

from amundsen_application.api.exceptions import MailClientNotImplemented
from amundsen_application.log.action_log import action_logging


class NotificationType(str, Enum):
    """
    Enum to describe supported notification types. Must match NotificationType interface defined in:
    https://github.com/lyft/amundsenfrontendlibrary/blob/master/amundsen_application/static/js/interfaces/Notifications.ts
    """
    OWNER_ADDED = 'owner_added'
    OWNER_REMOVED = 'owner_removed'
    METADATA_EDITED = 'metadata_edited'
    METADATA_REQUESTED = 'metadata_requested'
    DATA_ISSUE_REPORTED = 'data_issue_reported'

    @classmethod
    def has_value(cls, value: str) -> bool:
        for key in cls:
            if key.value == value:
                return True
        return False


NOTIFICATION_STRINGS = {
    NotificationType.OWNER_ADDED.value: {
        'comment': ('<br/>What is expected of you?<br/>As an owner, you take an important part in making '
                    'sure that the datasets you own can be used as swiftly as possible across the company.<br/>'
                    'Make sure the metadata is correct and up to date.<br/>'),
        'end_note': ('<br/>If you think you are not the best person to own this dataset and know someone who might '
                     'be, please contact this person and ask them if they want to replace you. It is important that we '
                     'keep multiple owners for each dataset to ensure continuity.<br/>'),
        'notification': ('<br/>You have been added to the owners list of the <a href="{resource_url}">'
                         '{resource_name}</a> dataset by {sender}.<br/>'),
    },
    NotificationType.OWNER_REMOVED.value: {
        'comment': '',
        'end_note': ('<br/>If you think you have been incorrectly removed as an owner, '
                     'add yourself back to the owners list.<br/>'),
        'notification': ('<br/>You have been removed from the owners list of the <a href="{resource_url}">'
                         '{resource_name}</a> dataset by {sender}.<br/>'),
    },
    NotificationType.METADATA_REQUESTED.value: {
        'comment': '',
        'end_note': '<br/>Please visit the provided link and improve descriptions on that resource.<br/>',
        'notification': '<br/>{sender} is trying to use <a href="{resource_url}">{resource_name}</a>, ',
    },
    NotificationType.DATA_ISSUE_REPORTED.value: {
        'comment': '<br/>Link to the issue: {data_issue_url}<br/>',
        'end_note': '<br/>Please visit the provided issue link for more information. You are getting this email '
                    'because you are listed as an owner of the resource. Please do not reply to this email.<br/>',
        'notification': '<br/>{sender} has reported a data issue for <a href="{resource_url}">{resource_name}</a>, ',
    }
}


def get_mail_client():  # type: ignore
    """
    Gets a mail_client object to send emails, raises an exception
    if mail client isn't implemented
    """
    mail_client = app.config['MAIL_CLIENT']

    if not mail_client:
        raise MailClientNotImplemented('An instance of BaseMailClient client must be configured on MAIL_CLIENT')

    return mail_client


def validate_options(*, options: Dict) -> None:
    """
    Raises an Exception if the options do not contain resource_path or resource_name
    """
    if options.get('resource_path') is None:
        raise Exception('resource_path was not provided in the notification options')
    if options.get('resource_name') is None:
        raise Exception('resource_name was not provided in the notification options')


def get_notification_html(*, notification_type: str, options: Dict, sender: str) -> str:
    """
    Returns the formatted html for the notification based on the notification_type
    :return: A string representing the html markup to send in the notification
    """
    validate_options(options=options)

    url_base = app.config['FRONTEND_BASE']
    resource_url = '{url_base}{resource_path}?source=notification'.format(resource_path=options.get('resource_path'),
                                                                          url_base=url_base)
    joined_chars = resource_url[len(url_base) - 1:len(url_base) + 1]
    if joined_chars.count('/') != 1:
        raise Exception('Configured "FRONTEND_BASE" and "resource_path" do not form a valid url')

    notification_strings = NOTIFICATION_STRINGS.get(notification_type)
    if notification_strings is None:
        raise Exception('Unsupported notification_type')

    greeting = 'Hello,<br/>'
    notification = notification_strings.get('notification', '').format(resource_url=resource_url,
                                                                       resource_name=options.get('resource_name'),
                                                                       sender=sender)
    comment = notification_strings.get('comment', '')
    end_note = notification_strings.get('end_note', '')
    salutation = '<br/>Thanks,<br/>Amundsen Team'

    if notification_type == NotificationType.METADATA_REQUESTED:
        options_comment = options.get('comment')
        need_resource_description = options.get('description_requested')
        need_fields_descriptions = options.get('fields_requested')

        if need_resource_description and need_fields_descriptions:
            notification = notification + 'and requests improved table and column descriptions.<br/>'
        elif need_resource_description:
            notification = notification + 'and requests an improved table description.<br/>'
        elif need_fields_descriptions:
            notification = notification + 'and requests improved column descriptions.<br/>'
        else:
            notification = notification + 'and requests more information about that resource.<br/>'

        if options_comment:
            comment = ('<br/>{sender} has included the following information with their request:'
                       '<br/>{comment}<br/>').format(sender=sender, comment=options_comment)

    if notification_type == NotificationType.DATA_ISSUE_REPORTED:
        greeting = 'Hello data owner,<br>'
        data_issue_url = options.get('data_issue_url')
        comment = comment.format(data_issue_url=data_issue_url)

    return '{greeting}{notification}{comment}{end_note}{salutation}'.format(greeting=greeting,
                                                                            notification=notification,
                                                                            comment=comment,
                                                                            end_note=end_note,
                                                                            salutation=salutation)


def get_notification_subject(*, notification_type: str, options: Dict) -> str:
    """
    Returns the subject to use for the given notification_type
    :param notification_type: type of notification
    :param options: data necessary to render email template content
    :return: The subject to be used with the notification
    """
    resource_name = options.get('resource_name')
    notification_subject_dict = {
        NotificationType.OWNER_ADDED.value: 'You are now an owner of {}'.format(resource_name),
        NotificationType.OWNER_REMOVED.value: 'You have been removed as an owner of {}'.format(resource_name),
        NotificationType.METADATA_EDITED.value: 'Your dataset {}\'s metadata has been edited'.format(resource_name),
        NotificationType.METADATA_REQUESTED.value: 'Request for metadata on {}'.format(resource_name),
        NotificationType.DATA_ISSUE_REPORTED.value: 'A data issue has been reported for {}'.format(resource_name)
    }
    subject = notification_subject_dict.get(notification_type)
    if subject is None:
        raise Exception('Unsupported notification_type')
    return subject


def send_notification(*, notification_type: str, options: Dict, recipients: List, sender: str) -> Response:
    """
    Sends a notification via email to a given list of recipients
    :param notification_type: type of notification
    :param options: data necessary to render email template content
    :param recipients: list of recipients who should receive notification
    :param sender: email of notification sender
    :return: Response
    """
    @action_logging
    def _log_send_notification(*, notification_type: str, options: Dict, recipients: List, sender: str) -> None:
        """ Logs the content of a sent notification"""
        pass  # pragma: no cover

    try:
        if not app.config['NOTIFICATIONS_ENABLED']:
            message = 'Notifications are not enabled. Request was accepted but no notification will be sent.'
            logging.exception(message)
            return make_response(jsonify({'msg': message}), HTTPStatus.ACCEPTED)
        if sender in recipients:
            recipients.remove(sender)
        if len(recipients) == 0:
            logging.info('No recipients exist for notification')
            return make_response(
                jsonify({
                    'msg': 'No valid recipients exist for notification, notification was not sent.'
                }),
                HTTPStatus.OK
            )

        mail_client = get_mail_client()

        html = get_notification_html(notification_type=notification_type, options=options, sender=sender)
        subject = get_notification_subject(notification_type=notification_type, options=options)

        _log_send_notification(
            notification_type=notification_type,
            options=options,
            recipients=recipients,
            sender=sender
        )

        response = mail_client.send_email(
            html=html,
            subject=subject,
            optional_data={
                'email_type': notification_type,
            },
            recipients=recipients,
            sender=sender,
        )
        status_code = response.status_code

        if 200 <= status_code < 300:
            message = 'Success'
        else:
            message = 'Mail client failed with status code ' + str(status_code)
            logging.error(message)

        return make_response(jsonify({'msg': message}), status_code)
    except MailClientNotImplemented as e:
        message = 'Encountered exception: ' + str(e)
        logging.exception(message)
        return make_response(jsonify({'msg': message}), HTTPStatus.NOT_IMPLEMENTED)
    except Exception as e1:
        message = 'Encountered exception: ' + str(e1)
        logging.exception(message)
        return make_response(jsonify({'msg': message}), HTTPStatus.INTERNAL_SERVER_ERROR)
