# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import logging

from http import HTTPStatus

from flask import Response, jsonify, make_response, request
from flask.blueprints import Blueprint

from amundsen_application.log.action_log import action_logging
from amundsen_application.api.utils.request_utils import get_query_param


LOGGER = logging.getLogger(__name__)

log_blueprint = Blueprint('log', __name__, url_prefix='/api/log/v0')


@log_blueprint.route('/log_event', methods=['POST'])
def log_generic_action() -> Response:
    """
    Log a generic action on the frontend. Captured parameters include

    :param command: Req. User Action E.g. click, scroll, hover, search, etc
    :param target_id: Req. Unique identifier for the object acted upon E.g. tag::payments, table::schema.database
    :param target_type: Opt. Type of element event took place on (button, link, tag, icon, etc)
    :param label: Opt. Displayed text for target
    :param location: Opt. Where the the event occurred
    :param value: Opt. Value to be logged
    :return:
    """
    @action_logging
    def _log_generic_action(*,
                            command: str,
                            target_id: str,
                            target_type: str,
                            label: str,
                            location: str,
                            value: str) -> None:
        pass  # pragma: no cover

    try:
        args = request.get_json()
        command = get_query_param(args, 'command', '"command" is a required parameter.')
        target_id = get_query_param(args, 'target_id', '"target_id" is a required field.')
        _log_generic_action(
            command=command,
            target_id=target_id,
            target_type=args.get('target_type', None),
            label=args.get('label', None),
            location=args.get('location', None),
            value=args.get('value', None)
        )
        message = 'Logging of {} action successful'.format(command)
        return make_response(jsonify({'msg': message}), HTTPStatus.OK)

    except Exception as e:
        message = 'Log action failed. Encountered exception: ' + str(e)
        logging.exception(message)
        payload = jsonify({'msg': message})
        return make_response(payload, HTTPStatus.INTERNAL_SERVER_ERROR)
