# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import io
import logging
from http import HTTPStatus

from flask import send_file, jsonify, make_response, Response, current_app as app
from flask.blueprints import Blueprint

from amundsen_application.api.preview.dashboard.dashboard_preview.preview_factory_method import \
    DefaultPreviewMethodFactory, BasePreviewMethodFactory

LOGGER = logging.getLogger(__name__)
PREVIEW_FACTORY: BasePreviewMethodFactory = None  # type: ignore

dashboard_preview_blueprint = Blueprint('dashboard_preview', __name__, url_prefix='/api/dashboard_preview/v0')


def initialize_preview_factory_class() -> None:
    """
    Instantiates Preview factory class and assign it to PREVIEW_FACTORY
    :return: None
    """
    global PREVIEW_FACTORY

    PREVIEW_FACTORY = app.config['DASHBOARD_PREVIEW_FACTORY']
    if not PREVIEW_FACTORY:
        PREVIEW_FACTORY = DefaultPreviewMethodFactory()

    LOGGER.info('Using {} for Dashboard'.format(PREVIEW_FACTORY))


@dashboard_preview_blueprint.route('/dashboard/<path:uri>/preview.jpg', methods=['GET'])
def get_preview_image(uri: str) -> Response:
    """
    Provides preview image of Dashboard which can be cached for a day (by default).
    :return:
    """

    if not PREVIEW_FACTORY:
        LOGGER.info('Initializing Dashboard PREVIEW_FACTORY')
        initialize_preview_factory_class()

    preview_client = PREVIEW_FACTORY.get_instance(uri=uri)
    try:
        return send_file(io.BytesIO(preview_client.get_preview_image(uri=uri)),
                         mimetype='image/jpeg',
                         cache_timeout=app.config['DASHBOARD_PREVIEW_IMAGE_CACHE_MAX_AGE_SECONDS'])
    except FileNotFoundError as fne:
        LOGGER.exception('FileNotFoundError on get_preview_image')
        return make_response(jsonify({'msg': fne.args[0]}), HTTPStatus.NOT_FOUND)
    except PermissionError as pe:
        LOGGER.exception('PermissionError on get_preview_image')
        return make_response(jsonify({'msg': pe.args[0]}), HTTPStatus.UNAUTHORIZED)
    except Exception as e:
        LOGGER.exception('Unexpected failure on get_preview_image')
        return make_response(jsonify({'msg': 'Encountered exception: ' + str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR)
