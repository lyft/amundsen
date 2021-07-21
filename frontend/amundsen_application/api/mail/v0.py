# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import logging

from http import HTTPStatus

from flask import Response, jsonify, make_response, request
from flask import current_app as app
from flask.blueprints import Blueprint

from amundsen_application.api.exceptions import MailClientNotImplemented
from amundsen_application.api.utils.notification_utils import get_mail_client, send_notification
from amundsen_application.log.action_log import action_logging

LOGGER = logging.getLogger(__name__)

mail_blueprint = Blueprint('mail', __name__, url_prefix='/api/mail/v0')


@mail_blueprint.route('/feedback', methods=['POST'])
def feedback() -> Response:
    """
    Uses the instance of BaseMailClient client configured on the MAIL_CLIENT
    config variable to send an email with feedback data
    """
    try:
        mail_client = get_mail_client()
        data = request.form.to_dict()
        html_content = ''.join('<div><strong>{}:</strong><br/>{}</div><br/>'.format(k, v) for k, v in data.items())

        # action logging
        feedback_type = data.get('feedback-type')
        rating = data.get('rating')
        comment = data.get('comment')
        bug_summary = data.get('bug-summary')
        repro_steps = data.get('repro-steps')
        feature_summary = data.get('feature-summary')
        value_prop = data.get('value-prop')
        subject = data.get('subject') or data.get('feedback-type')

        _feedback(feedback_type=feedback_type,
                  rating=rating,
                  comment=comment,
                  bug_summary=bug_summary,
                  repro_steps=repro_steps,
                  feature_summary=feature_summary,
                  value_prop=value_prop,
                  subject=subject)

        options = {
            'email_type': 'feedback',
            'form_data': data
        }

        response = mail_client.send_email(html=html_content, subject=subject, optional_data=options)
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


@action_logging
def _feedback(*,
              feedback_type: str,
              rating: str,
              comment: str,
              bug_summary: str,
              repro_steps: str,
              feature_summary: str,
              value_prop: str,
              subject: str) -> None:
    """ Logs the content of the feedback form """
    pass  # pragma: no cover


@mail_blueprint.route('/notification', methods=['POST'])
def notification() -> Response:
    """
    Uses the instance of BaseMailClient client configured on the MAIL_CLIENT
    config variable to send a notification email based on data passed from the request
    """
    try:
        data = request.get_json()

        notification_type = data.get('notificationType')
        if notification_type is None:
            message = 'Encountered exception: notificationType must be provided in the request payload'
            logging.exception(message)
            return make_response(jsonify({'msg': message}), HTTPStatus.BAD_REQUEST)

        sender = data.get('sender')
        if sender is None:
            sender = app.config['AUTH_USER_METHOD'](app).email

        options = data.get('options', {})
        recipients = data.get('recipients', [])

        return send_notification(
            notification_type=notification_type,
            options=options,
            recipients=recipients,
            sender=sender
        )
    except Exception as e:
        message = 'Encountered exception: ' + str(e)
        logging.exception(message)
        return make_response(jsonify({'msg': message}), HTTPStatus.INTERNAL_SERVER_ERROR)
