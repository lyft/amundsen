# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import distutils.util
import os
from typing import Any, Callable, Dict, List, Optional, Set  # noqa: F401

import boto3
from amundsen_gremlin.config import LocalGremlinConfig
from flask import Flask  # noqa: F401

from metadata_service.entity.badge import Badge

# PROXY configuration keys
PROXY_HOST = 'PROXY_HOST'
PROXY_PORT = 'PROXY_PORT'
PROXY_USER = 'PROXY_USER'
PROXY_PASSWORD = 'PROXY_PASSWORD'
PROXY_ENCRYPTED = 'PROXY_ENCRYPTED'
PROXY_VALIDATE_SSL = 'PROXY_VALIDATE_SSL'
PROXY_CLIENT = 'PROXY_CLIENT'
PROXY_CLIENT_KWARGS = 'PROXY_CLIENT_KWARGS'

PROXY_CLIENTS = {
    'NEO4J': 'metadata_service.proxy.neo4j_proxy.Neo4jProxy',
    'ATLAS': 'metadata_service.proxy.atlas_proxy.AtlasProxy',
    'NEPTUNE': 'metadata_service.proxy.neptune_proxy.NeptuneGremlinProxy',
    'MYSQL': 'metadata_service.proxy.mysql_proxy.MySQLProxy'
}

PROXY_CLIS = {
    'MYSQL': 'metadata_service.cli.rds_command.rds_cli'
}

IS_STATSD_ON = 'IS_STATSD_ON'
USER_OTHER_KEYS = 'USER_OTHER_KEYS'


class Config:
    LOG_FORMAT = '%(asctime)s.%(msecs)03d [%(levelname)s] %(module)s.%(funcName)s:%(lineno)d (%(process)d:' \
                 '%(threadName)s) - %(message)s'
    LOG_DATE_FORMAT = '%Y-%m-%dT%H:%M:%S%z'
    LOG_LEVEL = 'INFO'

    # Path to the logging configuration file to be used by `fileConfig()` method
    # https://docs.python.org/3.7/library/logging.config.html#logging.config.fileConfig
    # LOG_CONFIG_FILE = 'metadata_service/logging.conf'
    LOG_CONFIG_FILE = None

    PROXY_USER = os.environ.get('CREDENTIALS_PROXY_USER', 'neo4j')
    PROXY_PASSWORD = os.environ.get('CREDENTIALS_PROXY_PASSWORD', 'test')

    PROXY_ENCRYPTED = True
    """Whether the connection to the proxy should use SSL/TLS encryption."""

    # Prior to enable PROXY_VALIDATE_SSL, you need to configure SSL.
    # https://neo4j.com/docs/operations-manual/current/security/ssl-framework/
    PROXY_VALIDATE_SSL = False
    """Whether the SSL/TLS certificate presented by the user should be validated against the system's trusted CAs."""

    IS_STATSD_ON = False

    # Configurable dictionary to influence format of column statistics displayed in UI
    STATISTICS_FORMAT_SPEC: Dict[str, Dict] = {}

    # whitelist badges
    WHITELIST_BADGES: List[Badge] = []

    SWAGGER_ENABLED = os.environ.get('SWAGGER_ENABLED', False)

    USER_DETAIL_METHOD = None   # type: Optional[function]

    RESOURCE_REPORT_CLIENT = None  # type: Optional[function]

    # On User detail method, these keys will be added into amundsen_common.models.user.User.other_key_values
    USER_OTHER_KEYS = {'mode_user_id'}  # type: Set[str]

    # DEPRECATED (since version 3.6.0): Please use `POPULAR_RESOURCES_MINIMUM_READER_COUNT`
    # Number of minimum reader count to qualify for popular resources
    POPULAR_TABLE_MINIMUM_READER_COUNT = None
    POPULAR_RESOURCES_MINIMUM_READER_COUNT = 10  # type: int

    # List of regexes which will exclude certain parameters from appearing as Programmatic Descriptions
    PROGRAMMATIC_DESCRIPTIONS_EXCLUDE_FILTERS = []  # type: list

    # Custom kwargs that will be passed to proxy client. Can be used to fine-tune parameters like timeout
    # or num of retries
    PROXY_CLIENT_KWARGS: Dict = dict()

    # Initialize custom flask extensions and routes
    INIT_CUSTOM_EXT_AND_ROUTES = None  # type: Callable[[Flask], None]

    SWAGGER_TEMPLATE_PATH = os.path.join('api', 'swagger_doc', 'template.yml')
    SWAGGER = {
        'openapi': '3.0.2',
        'title': 'Metadata Service',
        'uiversion': 3
    }


class LocalConfig(Config):
    DEBUG = True
    TESTING = False
    LOG_LEVEL = 'DEBUG'
    LOCAL_HOST = '0.0.0.0'

    PROXY_HOST = os.environ.get('PROXY_HOST', f'bolt://{LOCAL_HOST}')
    PROXY_PORT = os.environ.get('PROXY_PORT', 7687)
    PROXY_CLIENT = PROXY_CLIENTS[os.environ.get('PROXY_CLIENT', 'NEO4J')]
    PROXY_ENCRYPTED = bool(distutils.util.strtobool(os.environ.get(PROXY_ENCRYPTED, 'True')))
    PROXY_VALIDATE_SSL = bool(distutils.util.strtobool(os.environ.get(PROXY_VALIDATE_SSL, 'False')))

    IS_STATSD_ON = bool(distutils.util.strtobool(os.environ.get(IS_STATSD_ON, 'False')))

    SWAGGER_ENABLED = True


class AtlasConfig(LocalConfig):
    PROXY_HOST = os.environ.get('PROXY_HOST', 'localhost')
    PROXY_PORT = os.environ.get('PROXY_PORT', '21000')
    PROXY_CLIENT = PROXY_CLIENTS['ATLAS']

    # List of accepted date formats for AtlasProxy Watermarks. With this we allow more than one datetime partition
    # format to be used in tables
    WATERMARK_DATE_FORMATS = ['%Y%m%d']


class GremlinConfig(LocalGremlinConfig, LocalConfig):
    JANUS_GRAPH_URL = None


class NeptuneConfig(LocalGremlinConfig, LocalConfig):
    DEBUG = False
    LOG_LEVEL = 'INFO'

    # PROXY_HOST FORMAT: wss://<NEPTUNE_URL>:<NEPTUNE_PORT>/gremlin
    PROXY_HOST = os.environ.get('PROXY_HOST', 'localhost')
    PROXY_PORT = None  # type: ignore

    PROXY_CLIENT = PROXY_CLIENTS['NEPTUNE']
    PROXY_PASSWORD = boto3.session.Session(region_name=os.environ.get('AWS_REGION', 'us-east-1'))

    PROXY_CLIENT_KWARGS = {
        'neptune_bulk_loader_s3_bucket_name': os.environ.get('S3_BUCKET_NAME'),
        'ignore_neptune_shard': distutils.util.strtobool(os.environ.get('IGNORE_NEPTUNE_SHARD', 'True'))
    }

    JANUS_GRAPH_URL = None


class MySQLConfig(LocalConfig):
    PROXY_CLIENT = PROXY_CLIENTS['MYSQL']
    PROXY_CLI = PROXY_CLIS['MYSQL']

    PROXY_HOST = None   # type: ignore
    PROXY_PORT = None   # type: ignore
    PROXY_USER = None   # type: ignore
    PROXY_PASSWORD = None   # type: ignore

    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI', 'mysql://user:password@127.0.0.1:3306/amundsen')
    PROXY_CLIENT_KWARGS: Dict[str, Any] = {
        'echo': bool(distutils.util.strtobool(os.environ.get('ECHO', 'False'))),
        'pool_size': os.environ.get('POOL_SIZE', 5),
        'max_overflow': os.environ.get('MAX_OVERFLOW', 10),
        'connect_args': dict()
    }
