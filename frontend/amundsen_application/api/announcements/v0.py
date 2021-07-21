# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import logging
from pkg_resources import iter_entry_points

from http import HTTPStatus

from flask import Response, jsonify, make_response, current_app as app
from flask.blueprints import Blueprint
from werkzeug.utils import import_string

LOGGER = logging.getLogger(__name__)
ANNOUNCEMENT_CLIENT_CLASS = None
ANNOUNCEMENT_CLIENT_INSTANCE = None

for entry_point in iter_entry_points(group='announcement_client', name='announcement_client_class'):
    announcement_client_class = entry_point.load()
    if announcement_client_class is not None:
        ANNOUNCEMENT_CLIENT_CLASS = announcement_client_class

announcements_blueprint = Blueprint('announcements', __name__, url_prefix='/api/announcements/v0')


@announcements_blueprint.route('/', methods=['GET'])
def get_announcements() -> Response:
    global ANNOUNCEMENT_CLIENT_INSTANCE
    global ANNOUNCEMENT_CLIENT_CLASS
    try:
        if ANNOUNCEMENT_CLIENT_INSTANCE is None:
            if ANNOUNCEMENT_CLIENT_CLASS is not None:
                ANNOUNCEMENT_CLIENT_INSTANCE = ANNOUNCEMENT_CLIENT_CLASS()
                logging.warn('Setting announcement_client via entry_point is DEPRECATED'
                             ' and will be removed in a future version')
            elif (app.config['ANNOUNCEMENT_CLIENT_ENABLED']
                    and app.config['ANNOUNCEMENT_CLIENT'] is not None):
                ANNOUNCEMENT_CLIENT_CLASS = import_string(app.config['ANNOUNCEMENT_CLIENT'])
                ANNOUNCEMENT_CLIENT_INSTANCE = ANNOUNCEMENT_CLIENT_CLASS()
            else:
                payload = jsonify({'posts': [],
                                   'msg': 'A client for retrieving announcements must be configured'})
                return make_response(payload, HTTPStatus.NOT_IMPLEMENTED)
        return ANNOUNCEMENT_CLIENT_INSTANCE._get_posts()
    except Exception as e:
        message = 'Encountered exception: ' + str(e)
        logging.exception(message)
        payload = jsonify({'posts': [], 'msg': message})
        return make_response(payload, HTTPStatus.INTERNAL_SERVER_ERROR)
