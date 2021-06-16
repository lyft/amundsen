# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import ast
import importlib
import logging
import logging.config
import os

from flask import Flask, Blueprint
from flask_restful import Api

from amundsen_application.api import init_routes
from amundsen_application.api.v0 import blueprint
from amundsen_application.api.announcements.v0 import announcements_blueprint
from amundsen_application.api.log.v0 import log_blueprint
from amundsen_application.api.mail.v0 import mail_blueprint
from amundsen_application.api.metadata.v0 import metadata_blueprint
from amundsen_application.api.preview.v0 import preview_blueprint
from amundsen_application.api.quality.v0 import quality_blueprint
from amundsen_application.api.search.v0 import search_blueprint
from amundsen_application.api.preview.dashboard.v0 import dashboard_preview_blueprint
from amundsen_application.api.issue.issue import IssueAPI, IssuesAPI


app_wrapper_class = Flask

""" Support for importing a subclass of flask.Flask, via env variables """
if os.getenv('APP_WRAPPER') and os.getenv('APP_WRAPPER_CLASS'):
    moduleName = os.getenv('APP_WRAPPER', '')
    module = importlib.import_module(moduleName)
    moduleClass = os.getenv('APP_WRAPPER_CLASS', '')
    app_wrapper_class = getattr(module, moduleClass)  # type: ignore

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
STATIC_ROOT = os.getenv('STATIC_ROOT', 'static')
static_dir = os.path.join(PROJECT_ROOT, STATIC_ROOT)


def create_app(config_module_class: str = None, template_folder: str = None) -> Flask:
    """ Support for importing arguments for a subclass of flask.Flask """
    args = ast.literal_eval(os.getenv('APP_WRAPPER_ARGS', '')) if os.getenv('APP_WRAPPER_ARGS') else {}

    tmpl_dir = template_folder if template_folder else os.path.join(PROJECT_ROOT, static_dir, 'dist/templates')
    app = app_wrapper_class(__name__, static_folder=static_dir, template_folder=tmpl_dir, **args)

    # Support for importing a custom config class
    if not config_module_class:
        config_module_class = os.getenv('FRONTEND_SVC_CONFIG_MODULE_CLASS')

    app.config.from_object(config_module_class)

    if app.config.get('LOG_CONFIG_FILE'):
        logging.config.fileConfig(app.config['LOG_CONFIG_FILE'], disable_existing_loggers=False)
    else:
        logging.basicConfig(format=app.config['LOG_FORMAT'], datefmt=app.config.get('LOG_DATE_FORMAT'))
        logging.getLogger().setLevel(app.config['LOG_LEVEL'])

    logging.info('Created app with config name {}'.format(config_module_class))
    logging.info('Using metadata service at {}'.format(app.config.get('METADATASERVICE_BASE')))
    logging.info('Using search service at {}'.format(app.config.get('SEARCHSERVICE_BASE')))

    api_bp = Blueprint('api', __name__)
    api = Api(api_bp)

    api.add_resource(IssuesAPI,
                     '/api/issue/issues', endpoint='issues')
    api.add_resource(IssueAPI,
                     '/api/issue/issue', endpoint='issue')

    app.register_blueprint(blueprint)
    app.register_blueprint(announcements_blueprint)
    app.register_blueprint(log_blueprint)
    app.register_blueprint(mail_blueprint)
    app.register_blueprint(metadata_blueprint)
    app.register_blueprint(preview_blueprint)
    app.register_blueprint(quality_blueprint)
    app.register_blueprint(search_blueprint)
    app.register_blueprint(api_bp)
    app.register_blueprint(dashboard_preview_blueprint)
    init_routes(app)

    init_custom_routes = app.config.get('INIT_CUSTOM_ROUTES')
    if init_custom_routes:
        init_custom_routes(app)

    return app
