# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import json
import logging
from pkg_resources import iter_entry_points

from http import HTTPStatus

from flask import Response, jsonify, make_response, request, current_app as app
from flask.blueprints import Blueprint
from marshmallow import ValidationError
from werkzeug.utils import import_string

from amundsen_application.models.quality import TableQualityChecks

LOGGER = logging.getLogger(__name__)
QUALITY_CLIENT_CLASS = None
QUALITY_CLIENT_INSTANCE = None

for entry_point in iter_entry_points(group='quality_client', name='quality_client_class'):
    quality_client_class = entry_point.load()
    if quality_client_class is not None:
        QUALITY_CLIENT_CLASS = quality_client_class

quality_blueprint = Blueprint('quality', __name__, url_prefix='/api/quality/v0')


@quality_blueprint.route('/table', methods=['GET'])
def get_table_quality_checks() -> Response:
    global QUALITY_CLIENT_INSTANCE
    global QUALITY_CLIENT_CLASS
    try:
        if QUALITY_CLIENT_INSTANCE is None:
            if QUALITY_CLIENT_CLASS is not None:
                QUALITY_CLIENT_INSTANCE = QUALITY_CLIENT_CLASS()
                logging.warn('Setting quality_client via entry_point is DEPRECATED and '
                             'will be removed in a future version')
            elif (app.config['QUALITY_CLIENT_ENABLED']
                  and app.config['QUALITY_CLIENT'] is not None):
                QUALITY_CLIENT_CLASS = import_string(app.config['QUALITY_CLIENT'])
                QUALITY_CLIENT_INSTANCE = QUALITY_CLIENT_CLASS()
            else:
                payload = jsonify({'checks': {}, 'msg': 'A client for the quality feature must be configured'})
                return make_response(payload, HTTPStatus.NOT_IMPLEMENTED)
        response = QUALITY_CLIENT_INSTANCE.get_table_quality_checks(params=request.args)
        status_code = response.status_code
        quality_checks = json.loads(response.data).get('checks')
        if status_code == HTTPStatus.OK:
            # validate the returned table checks data
            try:
                payload = jsonify({'checks': quality_checks, 'msg': 'Success'})
            except ValidationError as err:
                logging.error('Quality data dump returned errors: ' + str(err.messages))
                raise Exception('The preview client did not return a valid PreviewData object')
        else:
            message = 'Encountered error: Quality client request failed with code ' + str(status_code)
            logging.error(message)
            # only necessary to pass the error text
            payload = jsonify({'checks': {'error_text': quality_checks.get('error_text', '')}, 'msg': message})
        return make_response(payload, status_code)
    except Exception as e:
        message = 'Encountered exception: ' + str(e)
        logging.exception(message)
        payload = jsonify({'checks': {}, 'msg': message})
        return make_response(payload, HTTPStatus.INTERNAL_SERVER_ERROR)
