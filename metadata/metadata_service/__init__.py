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
from werkzeug.utils import import_string

from metadata_service.api.badge import BadgeAPI
from metadata_service.api.column import (ColumnBadgeAPI, ColumnDescriptionAPI,
                                         ColumnLineageAPI)
from metadata_service.api.dashboard import (DashboardBadgeAPI,
                                            DashboardDescriptionAPI,
                                            DashboardDetailAPI,
                                            DashboardTagAPI)
from metadata_service.api.feature import (FeatureBadgeAPI,
                                          FeatureDescriptionAPI,
                                          FeatureDetailAPI,
                                          FeatureGenerationCodeAPI,
                                          FeatureLineageAPI, FeatureOwnerAPI,
                                          FeatureSampleAPI, FeatureStatsAPI,
                                          FeatureTagAPI)
from metadata_service.api.healthcheck import HealthcheckAPI
from metadata_service.api.popular_resources import PopularResourcesAPI
from metadata_service.api.popular_tables import PopularTablesAPI
from metadata_service.api.system import Neo4jDetailAPI, StatisticsMetricsAPI
from metadata_service.api.table import (TableBadgeAPI, TableDashboardAPI,
                                        TableDescriptionAPI, TableDetailAPI,
                                        TableLineageAPI, TableOwnerAPI,
                                        TableTagAPI)
from metadata_service.api.tag import TagAPI
from metadata_service.api.user import (UserDetailAPI, UserFollowAPI,
                                       UserFollowsAPI, UserOwnAPI, UserOwnsAPI,
                                       UserReadsAPI)
from metadata_service.deprecations import process_deprecations

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

    :param config_module_class: name of the config (TODO: Implement config.py)
    :return: Flask
    """
    if FLASK_APP_MODULE_NAME and FLASK_APP_CLASS_NAME:
        print('Using requested Flask module {module_name} and class {class_name}'
              .format(module_name=FLASK_APP_MODULE_NAME, class_name=FLASK_APP_CLASS_NAME), file=sys.stderr)
        class_obj = getattr(importlib.import_module(FLASK_APP_MODULE_NAME), FLASK_APP_CLASS_NAME)

        flask_kwargs_dict = {}  # type: Dict[str, Any]
        if FLASK_APP_KWARGS_DICT_STR:
            print('Using kwargs {kwargs} to instantiate Flask'.format(kwargs=FLASK_APP_KWARGS_DICT_STR),
                  file=sys.stderr)
            flask_kwargs_dict = ast.literal_eval(FLASK_APP_KWARGS_DICT_STR)

        app = class_obj(__name__, **flask_kwargs_dict)

    else:
        app = Flask(__name__)

    if CORS_ENABLED:
        CORS(app)
    config_module_class = \
        os.getenv('METADATA_SVC_CONFIG_MODULE_CLASS') or config_module_class
    app.config.from_object(config_module_class)

    if app.config.get('LOG_CONFIG_FILE'):
        logging.config.fileConfig(app.config.get('LOG_CONFIG_FILE'), disable_existing_loggers=False)
    else:
        logging.basicConfig(format=app.config.get('LOG_FORMAT'), datefmt=app.config.get('LOG_DATE_FORMAT'))
        logging.getLogger().setLevel(app.config.get('LOG_LEVEL'))
    logging.info('Created app with config name {}'.format(config_module_class))
    logging.info('Using backend {}'.format(app.config.get('PROXY_CLIENT')))

    # Initialize custom extensions and routes
    init_custom_ext_routes = app.config.get('INIT_CUSTOM_EXT_AND_ROUTES')
    if init_custom_ext_routes:
        init_custom_ext_routes(app)

    api_bp = Blueprint('api', __name__)
    api = Api(api_bp)

    api.add_resource(HealthcheckAPI, '/healthcheck')

    # `PopularTablesAPI` is deprecated, and will be removed in version 4.
    api.add_resource(PopularTablesAPI,
                     '/popular_tables/',
                     '/popular_tables/<path:user_id>')
    api.add_resource(PopularResourcesAPI,
                     '/popular_resources/',
                     '/popular_resources/<path:user_id>')
    api.add_resource(TableDetailAPI, '/table/<path:table_uri>')
    api.add_resource(TableDescriptionAPI,
                     '/table/<path:id>/description')
    api.add_resource(TableTagAPI,
                     '/table/<path:id>/tag/<tag>')
    api.add_resource(TableBadgeAPI,
                     '/table/<path:id>/badge/<badge>')
    api.add_resource(TableLineageAPI,
                     '/table/<path:id>/lineage')
    api.add_resource(TableOwnerAPI,
                     '/table/<path:table_uri>/owner/<owner>')
    api.add_resource(TableDashboardAPI,
                     '/table/<path:id>/dashboard/')
    api.add_resource(ColumnDescriptionAPI,
                     '/table/<path:table_uri>/column/<column_name>/description')
    api.add_resource(ColumnBadgeAPI,
                     '/table/<path:table_uri>/column/<column_name>/badge/<badge>')
    api.add_resource(ColumnLineageAPI,
                     '/table/<path:table_uri>/column/<column_name>/lineage')
    api.add_resource(Neo4jDetailAPI,
                     '/latest_updated_ts')
    api.add_resource(StatisticsMetricsAPI,
                     '/system/statistics')
    api.add_resource(TagAPI,
                     '/tags/')
    api.add_resource(BadgeAPI,
                     '/badges/')
    api.add_resource(UserDetailAPI,
                     '/user',
                     '/user/<path:id>')
    api.add_resource(UserFollowsAPI,
                     '/user/<path:user_id>/follow/')
    api.add_resource(UserFollowAPI,
                     '/user/<path:user_id>/follow/<resource_type>/<path:resource_id>')
    api.add_resource(UserOwnsAPI,
                     '/user/<path:user_id>/own/')
    api.add_resource(UserOwnAPI,
                     '/user/<path:user_id>/own/<resource_type>/<path:table_uri>')
    api.add_resource(UserReadsAPI,
                     '/user/<path:user_id>/read/')
    api.add_resource(DashboardDetailAPI,
                     '/dashboard/<path:id>')
    api.add_resource(DashboardDescriptionAPI,
                     '/dashboard/<path:id>/description')
    api.add_resource(DashboardTagAPI,
                     '/dashboard/<path:id>/tag/<tag>')
    api.add_resource(DashboardBadgeAPI,
                     '/dashboard/<path:id>/badge/<badge>')
    api.add_resource(FeatureDetailAPI, '/feature/<path:feature_uri>')
    api.add_resource(FeatureDescriptionAPI,
                     '/feature/<path:id>/description')
    api.add_resource(FeatureTagAPI,
                     '/feature/<path:id>/tag/<tag>')
    api.add_resource(FeatureBadgeAPI,
                     '/feature/<path:id>/badge/<badge>')
    api.add_resource(FeatureLineageAPI,
                     '/feature/<path:id>/lineage')
    api.add_resource(FeatureOwnerAPI,
                     '/feature/<path:feature_uri>/owner/<owner>')
    api.add_resource(FeatureStatsAPI,
                     '/feature/<path:id>/stats')
    api.add_resource(FeatureSampleAPI,
                     '/feature/<path:id>/sample_data')
    api.add_resource(FeatureGenerationCodeAPI,
                     '/feature/<path:feature_uri>/generation_code')
    app.register_blueprint(api_bp)

    # cli registration
    proxy_cli = app.config.get('PROXY_CLI')
    if proxy_cli:
        app.cli.add_command(import_string(proxy_cli))
        logging.info('Using cli {}'.format(proxy_cli))

    if app.config.get('SWAGGER_ENABLED'):
        Swagger(app, template_file=os.path.join(ROOT_DIR, app.config.get('SWAGGER_TEMPLATE_PATH')), parse=True)

    # handles the deprecation warnings
    # and process any config/environment variables accordingly
    process_deprecations(app)

    return app
