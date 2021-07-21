# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import os

ELASTICSEARCH_INDEX_KEY = 'ELASTICSEARCH_INDEX'
SEARCH_PAGE_SIZE_KEY = 'SEARCH_PAGE_SIZE'
STATS_FEATURE_KEY = 'STATS'

PROXY_ENDPOINT = 'PROXY_ENDPOINT'
PROXY_USER = 'PROXY_USER'
PROXY_PASSWORD = 'PROXY_PASSWORD'
PROXY_CLIENT = 'PROXY_CLIENT'
PROXY_CLIENT_KEY = 'PROXY_CLIENT_KEY'
PROXY_CLIENTS = {
    'ELASTICSEARCH': 'search_service.proxy.elasticsearch.ElasticsearchProxy',
    'ATLAS': 'search_service.proxy.atlas.AtlasProxy'
}


class Config:
    LOG_FORMAT = '%(asctime)s.%(msecs)03d [%(levelname)s] %(module)s.%(funcName)s:%(lineno)d (%(process)d:'\
                 '%(threadName)s) - %(message)s'
    LOG_DATE_FORMAT = '%Y-%m-%dT%H:%M:%S%z'
    LOG_LEVEL = 'INFO'

    # Path to the logging configuration file to be used by `fileConfig()` method
    # https://docs.python.org/3.7/library/logging.config.html#logging.config.fileConfig
    # LOG_CONFIG_FILE = 'search_service/logging.conf'
    LOG_CONFIG_FILE = None

    # Config used by ElastichSearch
    ELASTICSEARCH_INDEX = 'table_search_index'

    SWAGGER_ENABLED = os.environ.get('SWAGGER_ENABLED', False)


class LocalConfig(Config):
    DEBUG = False
    TESTING = False
    STATS = False
    LOCAL_HOST = '0.0.0.0'
    PROXY_PORT = '9200'
    PROXY_ENDPOINT = os.environ.get('PROXY_ENDPOINT',
                                    'http://{LOCAL_HOST}:{PORT}'.format(
                                        LOCAL_HOST=LOCAL_HOST,
                                        PORT=PROXY_PORT)
                                    )
    PROXY_CLIENT = PROXY_CLIENTS[os.environ.get('PROXY_CLIENT', 'ELASTICSEARCH')]
    PROXY_CLIENT_KEY = os.environ.get('PROXY_CLIENT_KEY')
    PROXY_USER = os.environ.get('CREDENTIALS_PROXY_USER', 'elastic')
    PROXY_PASSWORD = os.environ.get('CREDENTIALS_PROXY_PASSWORD', 'elastic')

    SWAGGER_ENABLED = True
    SWAGGER_TEMPLATE_PATH = os.path.join('api', 'swagger_doc', 'template.yml')
    SWAGGER = {
        'openapi': '3.0.2',
        'title': 'Search Service',
        'uiversion': 3
    }


class AwsSearchConfig(LocalConfig):
    """
    Class sets up special case of Elasticsearch client with AWS token-based authentication,
    to enable usage of AWS Elasticsearch Service as a Elasticsearch Proxy backend.

    To connect to AWS Elasticsearch domain set environmental variable PROXY_ENDPOINT
    to domain's VPC endpoint, without the leading protol part (i.e. https://).
    Also, you need to set environmental variable AWS_REGION to the region in which your
    AWS Elasticsearch domain is running.

    To assess AWS Elasticsearch domain correctly you need to setup AWS credentials with
    a role that enables reading and writting to Elasticsearch Service domain;
    see the sample CloudFormation IAM policy below::

        {
            "Version": "2012-10-17",
            "Statement": [
                {
                "Effect": "Allow",
                "Principal": {
                    "AWS": [
                    "arn:aws:iam::123456789012:user/test-user"
                    ]
                },
                "Action": [
                    "es:ESHttpGet",
                    "es:ESHttpPut"
                ],
                "Resource": "arn:aws:es:us-west-1:987654321098:domain/test-domain/test-index/_search"
                }
            ]
        }

    If you run Amundsen on Kubernetes use IAM roles for service accounts
    (https://docs.aws.amazon.com/eks/latest/userguide/iam-roles-for-service-accounts.html).
    """
    import boto3
    from elasticsearch import Elasticsearch, RequestsHttpConnection
    from requests_aws4auth import AWS4Auth

    service = 'es'

    host = os.environ.get('PROXY_ENDPOINT')
    port = 443
    use_ssl = True
    verify_certs = True
    region = os.environ.get('AWS_REGION')
    credentials = boto3.Session().get_credentials()

    if all([host, region, credentials]):
        aws_auth = AWS4Auth(region=region, service=service, refreshable_credentials=credentials)

        client = Elasticsearch(
            hosts=[{'host': host, 'port': port}],
            http_auth=aws_auth,
            use_ssl=use_ssl,
            verify_certs=verify_certs,
            connection_class=RequestsHttpConnection
        )

        PROXY_CLIENT_KEY = client
