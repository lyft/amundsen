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

from amundsen_application.models.preview_data import PreviewDataSchema

LOGGER = logging.getLogger(__name__)
PREVIEW_CLIENT_CLASS = None
PREVIEW_CLIENT_INSTANCE = None

for entry_point in iter_entry_points(group='preview_client', name='table_preview_client_class'):
    preview_client_class = entry_point.load()
    if preview_client_class is not None:
        PREVIEW_CLIENT_CLASS = preview_client_class

preview_blueprint = Blueprint('preview', __name__, url_prefix='/api/preview/v0')


@preview_blueprint.route('/', methods=['POST'])
def get_table_preview() -> Response:
    global PREVIEW_CLIENT_INSTANCE
    global PREVIEW_CLIENT_CLASS
    try:
        if PREVIEW_CLIENT_INSTANCE is None:
            if PREVIEW_CLIENT_CLASS is not None:
                PREVIEW_CLIENT_INSTANCE = PREVIEW_CLIENT_CLASS()
                logging.warn('Setting preview_client via entry_point is DEPRECATED and '
                             'will be removed in a future version')
            elif (app.config['PREVIEW_CLIENT_ENABLED']
                    and app.config['PREVIEW_CLIENT'] is not None):
                PREVIEW_CLIENT_CLASS = import_string(app.config['PREVIEW_CLIENT'])
                PREVIEW_CLIENT_INSTANCE = PREVIEW_CLIENT_CLASS()
            else:
                payload = jsonify({'previewData': {}, 'msg': 'A client for the preview feature must be configured'})
                return make_response(payload, HTTPStatus.NOT_IMPLEMENTED)

        response = PREVIEW_CLIENT_INSTANCE.get_preview_data(params=request.get_json())
        status_code = response.status_code

        preview_data = json.loads(response.data).get('preview_data')
        if status_code == HTTPStatus.OK:
            # validate the returned table preview data
            try:
                data = PreviewDataSchema().load(preview_data)
                payload = jsonify({'previewData': data, 'msg': 'Success'})
            except ValidationError as err:
                logging.error('Preview data dump returned errors: ' + str(err.messages))
                raise Exception('The preview client did not return a valid PreviewData object')
        else:
            message = 'Encountered error: Preview client request failed with code ' + str(status_code)
            logging.error(message)
            # only necessary to pass the error text
            payload = jsonify({'previewData': {'error_text': preview_data.get('error_text', '')}, 'msg': message})
        return make_response(payload, status_code)
    except Exception as e:
        message = f'Encountered exception: {str(e)}'
        logging.exception(message)
        payload = jsonify({'previewData': {}, 'msg': message})
        return make_response(payload, HTTPStatus.INTERNAL_SERVER_ERROR)


@preview_blueprint.route('/feature_preview', methods=['POST'])
def get_feature_preview() -> Response:
    global PREVIEW_CLIENT_INSTANCE
    global PREVIEW_CLIENT_CLASS
    try:
        if PREVIEW_CLIENT_INSTANCE is None:
            if PREVIEW_CLIENT_CLASS is not None:
                PREVIEW_CLIENT_INSTANCE = PREVIEW_CLIENT_CLASS()
                logging.warn('Setting preview_client via entry_point is DEPRECATED and '
                             'will be removed in a future version')
            elif (app.config['PREVIEW_CLIENT_ENABLED']
                    and app.config['PREVIEW_CLIENT'] is not None):
                PREVIEW_CLIENT_CLASS = import_string(app.config['PREVIEW_CLIENT'])
                PREVIEW_CLIENT_INSTANCE = PREVIEW_CLIENT_CLASS()
            else:
                payload = jsonify({'previewData': {}, 'msg': 'A client for the preview feature must be configured'})
                return make_response(payload, HTTPStatus.NOT_IMPLEMENTED)

        response = PREVIEW_CLIENT_INSTANCE.get_feature_preview_data(params=request.get_json())
        status_code = response.status_code

        preview_data = json.loads(response.data).get('preview_data')
        if status_code == HTTPStatus.OK:
            # validate the returned feature preview data
            try:
                data = PreviewDataSchema().load(preview_data)
                payload = jsonify({'previewData': data, 'msg': 'Success'})
            except ValidationError as err:
                logging.error('Preview data dump returned errors: ' + str(err.messages))
                raise Exception('The preview client did not return a valid PreviewData object')
        else:
            message = 'Encountered error: Preview client request failed with code ' + str(status_code)
            logging.error(message)
            # only necessary to pass the error text
            payload = jsonify({'previewData': {'error_text': preview_data.get('error_text', '')}, 'msg': message})
        return make_response(payload, status_code)
    except Exception as e:
        message = f'Encountered exception: {str(e)}'
        logging.exception(message)
        payload = jsonify({'previewData': {}, 'msg': message})
        return make_response(payload, HTTPStatus.INTERNAL_SERVER_ERROR)
