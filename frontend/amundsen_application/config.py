# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import os
from typing import Callable, Dict, List, Optional, Set  # noqa: F401
from amundsen_application.models.user import User

from flask import Flask  # noqa: F401

from amundsen_application.tests.test_utils import get_test_user


class MatchRuleObject:
    def __init__(self,
                 schema_regex=None,  # type: str
                 table_name_regex=None,   # type: str
                 ) -> None:
        self.schema_regex = schema_regex
        self.table_name_regex = table_name_regex


class Config:
    LOG_FORMAT = '%(asctime)s.%(msecs)03d [%(levelname)s] %(module)s.%(funcName)s:%(lineno)d (%(process)d:' \
                 + '%(threadName)s) - %(message)s'
    LOG_DATE_FORMAT = '%Y-%m-%dT%H:%M:%S%z'
    LOG_LEVEL = 'INFO'

    # Path to the logging configuration file to be used by `fileConfig()` method
    # https://docs.python.org/3.7/library/logging.config.html#logging.config.fileConfig
    # LOG_CONFIG_FILE = 'amundsen_application/logging.conf'
    LOG_CONFIG_FILE = None

    COLUMN_STAT_ORDER = None  # type: Dict[str, int]

    UNEDITABLE_SCHEMAS = set()  # type: Set[str]

    UNEDITABLE_TABLE_DESCRIPTION_MATCH_RULES = []  # type: List[MatchRuleObject]

    # DEPRECATED (since version 3.9.0): Please use `POPULAR_RESOURCES_COUNT`
    # Number of popular tables to be displayed on the index/search page
    POPULAR_TABLE_COUNT = None
    POPULAR_RESOURCES_COUNT = 4     # type: int

    # DEPRECATED (since version 3.9.0): Please use `POPULAR_RESOURCES_PERSONALIZATION`
    # Personalize the popular tables response for the current authenticated user
    POPULAR_TABLE_PERSONALIZATION = None
    POPULAR_RESOURCES_PERSONALIZATION = False  # type: bool

    # Request Timeout Configurations in Seconds
    REQUEST_SESSION_TIMEOUT_SEC = 3

    # Frontend Application
    FRONTEND_BASE = ''

    # Search Service
    SEARCHSERVICE_REQUEST_CLIENT = None
    SEARCHSERVICE_REQUEST_HEADERS = None
    SEARCHSERVICE_BASE = ''

    # Metadata Service
    METADATASERVICE_REQUEST_CLIENT = None
    METADATASERVICE_REQUEST_HEADERS = None
    METADATASERVICE_BASE = ''

    # Mail Client Features
    MAIL_CLIENT = None
    NOTIFICATIONS_ENABLED = False

    # Initialize custom routes
    INIT_CUSTOM_ROUTES = None  # type: Callable[[Flask], None]

    # Settings for Preview Client integration
    PREVIEW_CLIENT_ENABLED = os.getenv('PREVIEW_CLIENT_ENABLED') == 'true'  # type: bool
    # Maps to a class path and name
    PREVIEW_CLIENT = os.getenv('PREVIEW_CLIENT', None)  # type: Optional[str]
    PREVIEW_CLIENT_URL = os.getenv('PREVIEW_CLIENT_URL')  # type: Optional[str]
    PREVIEW_CLIENT_USERNAME = os.getenv('PREVIEW_CLIENT_USERNAME')  # type: Optional[str]
    PREVIEW_CLIENT_PASSWORD = os.getenv('PREVIEW_CLIENT_PASSWORD')  # type: Optional[str]
    PREVIEW_CLIENT_CERTIFICATE = os.getenv('PREVIEW_CLIENT_CERTIFICATE')  # type: Optional[str]

    # Settings for Announcement Client integration
    ANNOUNCEMENT_CLIENT_ENABLED = os.getenv('ANNOUNCEMENT_CLIENT_ENABLED') == 'true'  # type: bool
    # Maps to a class path and name
    ANNOUNCEMENT_CLIENT = os.getenv('ANNOUNCEMENT_CLIENT', None)  # type: Optional[str]

    # Settings for Issue tracker integration
    ISSUE_LABELS = []  # type: List[str]
    ISSUE_TRACKER_API_TOKEN = None  # type: str
    ISSUE_TRACKER_URL = None  # type: str
    ISSUE_TRACKER_USER = None  # type: str
    ISSUE_TRACKER_PASSWORD = None  # type: str
    ISSUE_TRACKER_PROJECT_ID = None  # type: int
    # Maps to a class path and name
    ISSUE_TRACKER_CLIENT = None  # type: str
    ISSUE_TRACKER_CLIENT_ENABLED = False  # type: bool
    # Max issues to display at a time
    ISSUE_TRACKER_MAX_RESULTS = None  # type: int
    # Override issue type ID for cloud Jira deployments
    ISSUE_TRACKER_ISSUE_TYPE_ID = None

    # Programmatic Description configuration. Please see docs/flask_config.md
    PROGRAMMATIC_DISPLAY = None  # type: Optional[Dict]

    # If specified, will be used to generate headers for service-to-service communication
    # Please note that if specified, this will ignore following config properties:
    # 1. METADATASERVICE_REQUEST_HEADERS
    # 2. SEARCHSERVICE_REQUEST_HEADERS
    REQUEST_HEADERS_METHOD: Optional[Callable[[Flask], Optional[Dict]]] = None

    AUTH_USER_METHOD: Optional[Callable[[Flask], User]] = None
    GET_PROFILE_URL = None

    # For additional preview client, register more at DefaultPreviewMethodFactory.__init__()
    # For any private preview client, use custom factory that implements BasePreviewMethodFactory
    DASHBOARD_PREVIEW_FACTORY = None  # By default DefaultPreviewMethodFactory will be used.
    DASHBOARD_PREVIEW_IMAGE_CACHE_MAX_AGE_SECONDS = 60 * 60 * 24 * 1  # 1 day

    CREDENTIALS_MODE_ADMIN_TOKEN = os.getenv('CREDENTIALS_MODE_ADMIN_TOKEN', None)
    CREDENTIALS_MODE_ADMIN_PASSWORD = os.getenv('CREDENTIALS_MODE_ADMIN_PASSWORD', None)
    MODE_ORGANIZATION = None
    MODE_REPORT_URL_TEMPLATE = None
    # Add Preview class name below to enable ACL, assuming it is supported by the Preview class
    # e.g: ACL_ENABLED_DASHBOARD_PREVIEW = {'ModePreview'}
    ACL_ENABLED_DASHBOARD_PREVIEW = set()  # type: Set[Optional[str]]

    MTLS_CLIENT_CERT = os.getenv('MTLS_CLIENT_CERT')
    """
    Optional.
    The path to a PEM formatted certificate to present when calling the metadata and search services.
    MTLS_CLIENT_KEY must also be set.
    """

    MTLS_CLIENT_KEY = os.getenv('MTLS_CLIENT_KEY')
    """Optional. The path to a PEM formatted key to use with the MTLS_CLIENT_CERT. MTLS_CLIENT_CERT must also be set."""


class LocalConfig(Config):
    DEBUG = False
    TESTING = False
    LOG_LEVEL = 'DEBUG'

    FRONTEND_PORT = '5000'
    # If installing locally directly from the github source
    # modify these ports if necessary to point to you local search and metadata services
    SEARCH_PORT = '5001'
    METADATA_PORT = '5002'

    # If installing using the Docker bootstrap, this should be modified to the docker host ip.
    LOCAL_HOST = '0.0.0.0'

    FRONTEND_BASE = os.environ.get('FRONTEND_BASE',
                                   'http://{LOCAL_HOST}:{PORT}'.format(
                                       LOCAL_HOST=LOCAL_HOST,
                                       PORT=FRONTEND_PORT)
                                   )

    SEARCHSERVICE_BASE = os.environ.get('SEARCHSERVICE_BASE',
                                        'http://{LOCAL_HOST}:{PORT}'.format(
                                            LOCAL_HOST=LOCAL_HOST,
                                            PORT=SEARCH_PORT)
                                        )

    METADATASERVICE_BASE = os.environ.get('METADATASERVICE_BASE',
                                          'http://{LOCAL_HOST}:{PORT}'.format(
                                              LOCAL_HOST=LOCAL_HOST,
                                              PORT=METADATA_PORT)
                                          )


class TestConfig(LocalConfig):
    POPULAR_RESOURCES_PERSONALIZATION = True
    AUTH_USER_METHOD = get_test_user
    NOTIFICATIONS_ENABLED = True
    ISSUE_TRACKER_URL = 'test_url'
    ISSUE_TRACKER_USER = 'test_user'
    ISSUE_TRACKER_PASSWORD = 'test_password'
    ISSUE_TRACKER_PROJECT_ID = 1
    ISSUE_TRACKER_CLIENT_ENABLED = True
    ISSUE_TRACKER_MAX_RESULTS = 3


class TestNotificationsDisabledConfig(LocalConfig):
    AUTH_USER_METHOD = get_test_user
    NOTIFICATIONS_ENABLED = False
