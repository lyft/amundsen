# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import ast
import importlib
import logging
import logging.config
import os
import sys
from typing import Any, Dict  # noqa: F401

from flasgger import Swagger
from flask import Blueprint, Flask
from flask_cors import CORS
from flask_restful import Api

from search_service.api.dashboard import SearchDashboardAPI, SearchDashboardFilterAPI
from search_service.api.document import (
    DocumentFeatureAPI, DocumentFeaturesAPI, DocumentTableAPI, DocumentTablesAPI, DocumentUserAPI, DocumentUsersAPI,
)
from search_service.api.feature import SearchFeatureAPI, SearchFeatureFilterAPI
from search_service.api.healthcheck import healthcheck
from search_service.api.table import SearchTableAPI, SearchTableFilterAPI
from search_service.api.user import SearchUserAPI

# For customized flask use below arguments to override.
FLASK_APP_MODULE_NAME = os.getenv('FLASK_APP_MODULE_NAME')
FLASK_APP_CLASS_NAME = os.getenv('FLASK_APP_CLASS_NAME')
FLASK_APP_KWARGS_DICT_STR = os.getenv('FLASK_APP_KWARGS_DICT')
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

# Environment Variable to enable cors
CORS_ENABLED = os.environ.get('CORS_ENABLED', False)


def create_app(*, config_module_class: str) -> Flask:
    """
    Creates app in function so that flask with flask extensions can be
    initialized with specific config. Here it defines the route of APIs
    so that it can be seen in one place where implementation is separated.

    Config is being fetched via module.class name where module.class name
    can be passed through environment variable.
    This is to make config fetched through runtime PYTHON_PATH so that
    Config class can be easily injected.
    More on: http://flask.pocoo.org/docs/1.0/config/

    :param config_module_class: name of the config
    :return: Flask
    """
    if FLASK_APP_MODULE_NAME and FLASK_APP_CLASS_NAME:
        print(f'Using requested Flask module {FLASK_APP_MODULE_NAME} '
              f'and class {FLASK_APP_CLASS_NAME}', file=sys.stderr)
        class_obj = getattr(
            importlib.import_module(FLASK_APP_MODULE_NAME),
            FLASK_APP_CLASS_NAME
        )

        flask_kwargs_dict = {}  # type: Dict[str, Any]
        if FLASK_APP_KWARGS_DICT_STR:
            print(f'Using kwargs {FLASK_APP_KWARGS_DICT_STR} to instantiate Flask',
                  file=sys.stderr)
            flask_kwargs_dict = ast.literal_eval(FLASK_APP_KWARGS_DICT_STR)

        app = class_obj(__name__, **flask_kwargs_dict)

    else:
        app = Flask(__name__)

    if CORS_ENABLED:
        CORS(app)
    config_module_class = \
        os.getenv('SEARCH_SVC_CONFIG_MODULE_CLASS') or config_module_class
    app.config.from_object(config_module_class)

    if app.config.get('LOG_CONFIG_FILE'):
        logging.config.fileConfig(app.config.get('LOG_CONFIG_FILE'), disable_existing_loggers=False)
    else:
        logging.basicConfig(format=app.config.get('LOG_FORMAT'), datefmt=app.config.get('LOG_DATE_FORMAT'))
        logging.getLogger().setLevel(app.config.get('LOG_LEVEL'))

    logging.info('Creating app with config name {}'
                 .format(config_module_class))
    logging.info('Created app with config name {}'.format(config_module_class))

    api_bp = Blueprint('api', __name__)
    api_bp.add_url_rule('/healthcheck', 'healthcheck', healthcheck)
    api = Api(api_bp)
    # Table Search API

    api.add_resource(SearchTableFilterAPI, '/search_table')
    # TODO: Rename endpoint to be more generic and accept a resource type so that logic can be re-used
    api.add_resource(SearchTableAPI, '/search')

    # User Search API
    api.add_resource(SearchUserAPI, '/search_user')

    # Dashboard Search API
    api.add_resource(SearchDashboardAPI, '/search_dashboard')
    api.add_resource(SearchDashboardFilterAPI, '/search_dashboard_filter')

    # Feature Search API
    api.add_resource(SearchFeatureAPI, '/search_feature')
    api.add_resource(SearchFeatureFilterAPI, '/search_feature_filter')

    # DocumentAPI
    # todo: needs to handle dashboard
    api.add_resource(DocumentTablesAPI, '/document_table')
    api.add_resource(DocumentTableAPI, '/document_table/<document_id>')

    api.add_resource(DocumentUsersAPI, '/document_user')
    api.add_resource(DocumentUserAPI, '/document_user/<document_id>')

    api.add_resource(DocumentFeaturesAPI, '/document_feature')
    api.add_resource(DocumentFeatureAPI, '/document_feature/<document_id>')

    app.register_blueprint(api_bp)

    if app.config.get('SWAGGER_ENABLED'):
        Swagger(app, template_file=os.path.join(ROOT_DIR, app.config.get('SWAGGER_TEMPLATE_PATH')), parse=True)
    return app
