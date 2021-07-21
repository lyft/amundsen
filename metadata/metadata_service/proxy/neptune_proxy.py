# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0import json

import json
import logging
from typing import Any, Dict, Mapping, Optional, Type, Union
from urllib.parse import urlsplit, urlunsplit

import boto3
import gremlin_python.driver.protocol
import requests
from amundsen_gremlin.gremlin_model import WellKnownProperties
from amundsen_gremlin.neptune_bulk_loader.api import (
    NeptuneBulkLoaderApi, get_neptune_graph_traversal_source_factory)
from amundsen_gremlin.script_translator import ScriptTranslatorTargetNeptune
from amundsen_gremlin.test_and_development_shard import get_shard
from for_requests.assume_role_aws4auth import AssumeRoleAWS4Auth
from for_requests.aws4auth_compatible import to_aws4_request_compatible_host
from for_requests.host_header_ssl import HostHeaderSSLAdapter
from gremlin_python.process.traversal import TextP
from neptune_python_utils.endpoints import (Endpoint, Endpoints,
                                            RequestParameters)
from overrides import overrides
from ssl_override_server_hostname.ssl_context import \
    OverrideServerHostnameSSLContext
from tornado import httpclient

from .gremlin_proxy import (AbstractGremlinProxy, FromResultSet,
                            _parse_gremlin_server_error)

LOGGER = logging.getLogger(__name__)


def _is_neptune_retryable_exception(exception: Exception) -> bool:
    if not isinstance(exception, gremlin_python.driver.protocol.GremlinServerError):
        return False
    # TODO: maybe revert InternalFailureException retries later?
    # TODO: only retry the 500 in staging? One origin of 500 has nothing to do with an actual HTTP 500 but rather a
    # disconnection from the server
    return _parse_gremlin_server_error(exception).get('code') in (
        'ConcurrentModificationException', 'InternalFailureException', 500)


class NeptuneGremlinProxy(AbstractGremlinProxy):
    """
    A proxy to a Neptune using the Gremlin protocol.

    See also https://docs.aws.amazon.com/neptune/latest/userguide/access-graph-gremlin-differences.html
    See also https://docs.aws.amazon.com/neptune/latest/userguide/access-graph-gremlin-sessions.html

    TODO: HTTP proxy support.  This does *NOT* support HTTP proxies as-is. Why? The default transport factory in
    gremlin_python is tornado.websocket, which is hardcoded to use simple_httpclient (look at
    WebSocketClientConnection).  But, even if that could be made to use curl_httpclient, curl_httpclient requires pycurl
    which requires libcurl and other native libraries which is a pain to install.
    """

    def __init__(self, *, host: str, port: Optional[int] = None, user: str = None,
                 password: Optional[Union[str, boto3.session.Session]] = None,
                 driver_remote_connection_options: Mapping[str, Any] = {},
                 client_kwargs: Dict = dict(),
                 **kwargs: dict) -> None:

        driver_remote_connection_options = dict(driver_remote_connection_options)
        # port should be part of that url
        if port is not None:
            raise NotImplementedError(f'port is not allowed! port={port}')

        # for IAM auth, we need the triplet or a Session which is more general
        if isinstance(password, boto3.session.Session):
            session = password
            self.aws_auth = AssumeRoleAWS4Auth(session.get_credentials(), session.region_name, 'neptune-db')
        else:
            raise NotImplementedError(f'to use authentication, pass a boto3.session.Session!)')

        if isinstance(host, str):
            # usually a wss URI
            url = urlsplit(host)
            assert url.scheme in ('wss', 'ws') and url.path == '/gremlin' and not url.query and not url.fragment, \
                f'url is not a Neptune ws url?: {host}'

            self.endpoints = Endpoints(
                neptune_endpoint=url.hostname, neptune_port=url.port,
                region_name=session.region_name, credentials=session.get_credentials())
            self.override_uri = None
        elif isinstance(host, Mapping):
            # ...but development is a little complicated
            assert all(k in host for k in ('neptune_endpoint', 'neptune_port', 'uri')), \
                f'pass a dict with neptune_endpoint, neptune_port, and uri not: {host}'

            self.endpoints = Endpoints(
                neptune_endpoint=host['neptune_endpoint'], neptune_port=int(host['neptune_port']),
                region_name=session.region_name, credentials=session.get_credentials())
            uri = urlsplit(host['uri'])
            assert uri.scheme in ('wss', 'ws') and uri.path == '/gremlin' and not uri.query and not uri.fragment, \
                f'''url is not a Neptune ws url?: {host['uri']}'''
            self.override_uri = uri
        else:
            raise NotImplementedError(f'to use authentication, pass a Mapping with aws_access_key_id, '
                                      f'aws_secret_access_key, service_region!')

        # always g for Neptune
        driver_remote_connection_options.update(traversal_source='g')

        try:
            s3_bucket_name = client_kwargs['neptune_bulk_loader_s3_bucket_name']  # noqa: E731
        except Exception:
            raise NotImplementedError(f'Cannot find s3 bucket name!')

        # Instantiate bulk loader and graph traversal factory
        bulk_loader_config: Dict[str, Any] = dict(NEPTUNE_SESSION=password, NEPTUNE_URL=host,
                                                  NEPTUNE_BULK_LOADER_S3_BUCKET_NAME=s3_bucket_name)
        self.neptune_bulk_loader_api = NeptuneBulkLoaderApi.create_from_config(bulk_loader_config)
        self.neptune_graph_traversal_source_factory = get_neptune_graph_traversal_source_factory(session=password,
                                                                                                 neptune_url=host)

        AbstractGremlinProxy.__init__(self, key_property_name='key',
                                      driver_remote_connection_options=driver_remote_connection_options)

    @classmethod
    @overrides
    def script_translator(cls) -> Type[ScriptTranslatorTargetNeptune]:
        return ScriptTranslatorTargetNeptune

    def override_prepared_request_parameters(
            self, request_parameters: RequestParameters, *, method: Optional[str] = None,
            data: Optional[str] = None) -> httpclient.HTTPRequest:
        http_request_param: Dict[str, Any] = dict(url=request_parameters.uri, headers=request_parameters.headers)
        if method is not None:
            http_request_param['method'] = method
        if data is not None:
            http_request_param['body'] = data
        if self.override_uri:
            # we override the URI slightly (because the instance thinks it's a different host than we're connecting to)
            uri = urlsplit(request_parameters.uri)
            http_request_param['headers'] = dict(request_parameters.headers)
            http_request_param['headers']['Host'] = uri.netloc
            http_request_param['ssl_options'] = OverrideServerHostnameSSLContext(server_hostname=uri.hostname)
            http_request_param['url'] = urlunsplit(
                (uri.scheme, self.override_uri.netloc, uri.path, uri.query, uri.fragment))
        return httpclient.HTTPRequest(**http_request_param)

    @overrides
    def possibly_signed_ws_client_request_or_url(self) -> Union[httpclient.HTTPRequest, str]:
        return self.override_prepared_request_parameters(self.endpoints.gremlin_endpoint().prepare_request())

    @classmethod
    @overrides
    def _is_retryable_exception(cls, *, method_name: str, exception: Exception) -> bool:
        # any method
        return _is_neptune_retryable_exception(exception) or isinstance(exception, ConnectionError)

    def is_healthy(self) -> None:
        signed_request = self.override_prepared_request_parameters(self.endpoints.status_endpoint().prepare_request())
        http_client = httpclient.HTTPClient()
        # this will throw if the instance is really borked or we can't connect or we're not allowed (see
        # https://docs.aws.amazon.com/neptune/latest/userguide/access-graph-status.html )
        response = http_client.fetch(signed_request)
        status = json.loads(response.body, encoding='utf-8')

        if status.get('status') == 'healthy' and status.get('role') == 'writer':
            LOGGER.debug(f'status is healthy: {status}')
        else:
            # we'll log in healthcheck
            raise RuntimeError(f'status is unhealthy: {status}')

    def _non_standard_endpoint(self, scheme: str, path: str) -> Endpoint:
        return self.endpoints._Endpoints__endpoint(
            scheme, self.endpoints.neptune_endpoint, self.endpoints.neptune_port, path)

    def _gremlin_status(self, query_id: Optional[str] = None, include_waiting: bool = False) -> str:
        """
        https://docs.aws.amazon.com/neptune/latest/userguide/gremlin-api-status.html
        """
        endpoint = self._non_standard_endpoint('https', 'gremlin/status')

        query_parameters = {}
        if query_id is not None:
            query_parameters['queryId'] = query_id
        if include_waiting:
            query_parameters['includeWaiting'] = 'true'

        signed_request = self.override_prepared_request_parameters(
            endpoint.prepare_request(querystring=query_parameters))
        http_client = httpclient.HTTPClient()
        response = http_client.fetch(signed_request)
        return json.loads(response.body, encoding='utf-8')

    def _sparql_status(self, query_id: Optional[str] = None) -> str:
        """
        https://docs.aws.amazon.com/neptune/latest/userguide/sparql-api-status.html
        """
        endpoint = self._non_standard_endpoint('https', 'sparql/status')

        query_parameters = {}
        if query_id is not None:
            query_parameters['queryId'] = query_id

        signed_request = self.override_prepared_request_parameters(
            endpoint.prepare_request(querystring=query_parameters))
        http_client = httpclient.HTTPClient()
        response = http_client.fetch(signed_request)
        return json.loads(response.body, encoding='utf-8')

    def _explain(self, gremlin_query: str) -> str:
        """
        return the Neptune specific explaination of the query
        see https://docs.aws.amazon.com/neptune/latest/userguide/gremlin-explain-api.html
        see https://docs.aws.amazon.com/neptune/latest/userguide/gremlin-explain-background.html
        """
        # why not use endpoints? Despite the fact that it accepts a method and payload, it doesn't *actually* generate
        # sufficient headers so we'll use requests for these since we can
        url = urlsplit(self.endpoints.gremlin_endpoint().prepare_request().uri)
        assert url.scheme in ('wss', 'ws') and url.path == '/gremlin' and not url.query and not url.fragment, \
            f'url is not a Neptune ws url?: {url}'
        _explain_url = urlunsplit(
            ('https' if url.scheme == 'wss' else 'http', url.netloc, url.path + '/explain', '', ''))
        host = to_aws4_request_compatible_host(_explain_url)
        if self.override_uri:
            _explain_url = urlunsplit(
                ('https' if url.scheme == 'wss' else 'http', self.override_uri.netloc, url.path + '/explain', '', ''))
        s = requests.Session()
        s.mount('https://', HostHeaderSSLAdapter())
        response = s.post(_explain_url, auth=self.aws_auth,
                          data=json.dumps(dict(gremlin=gremlin_query)).encode('utf-8'),
                          # include Host header
                          headers=dict(Host=host))
        return response.content.decode('utf-8')

    def _profile(self, gremlin_query: str) -> str:
        """
        return the Neptune specific explaination of the RUNNING query.  Now it can't return the result set, so the
        utility is limited to cases where you can re-run this, or are running as a one off from console, or as a last
        resort
        see https://docs.aws.amazon.com/neptune/latest/userguide/gremlin-profile-api.htlm
        see https://docs.aws.amazon.com/neptune/latest/userguide/gremlin-explain-background.html
        """
        # why not use endpoints? Despite the fact that it accepts a method and payload, it doesn't *actually* generate
        # sufficient headers so we'll use requests for these since we can
        url = urlsplit(self.endpoints.gremlin_endpoint().prepare_request().uri)
        assert url.scheme in ('wss', 'ws') and url.path == '/gremlin' and not url.query and not url.fragment, \
            f'url is not a Neptune ws url?: {url}'
        _profile_url = urlunsplit(
            ('https' if url.scheme == 'wss' else 'http', url.netloc, url.path + '/profile', '', ''))
        host = to_aws4_request_compatible_host(_profile_url)
        if self.override_uri:
            _profile_url = urlunsplit(
                ('https' if url.scheme == 'wss' else 'http', self.override_uri.netloc, url.path + '/profile', '', ''))
        s = requests.Session()
        s.mount('https://', HostHeaderSSLAdapter())
        response = s.post(_profile_url, auth=self.aws_auth,
                          data=json.dumps(dict(gremlin=gremlin_query)).encode('utf-8'),
                          # include Host header
                          headers=dict(Host=host))
        return response.content.decode('utf-8')

    @overrides
    def drop(self) -> None:
        test_shard = get_shard()
        g = self.g.V()
        if test_shard:
            g = g.has(WellKnownProperties.TestShard.value.name, test_shard)
        g = g.drop()
        LOGGER.warning('DROPPING ALL NODES')
        self.query_executor()(query=g, get=FromResultSet.iterate)
        # we seem to mess this up easily
        leftover = self.query_executor()(query=self.g.V().hasId(TextP.startingWith(test_shard)).id(),
                                         get=FromResultSet.toList)
        self.query_executor()(query=self.g.V().hasId(TextP.startingWith(test_shard)).drop(),
                              get=FromResultSet.iterate)
        assert not leftover, f'we have some leftover: {leftover}'
        LOGGER.warning('COMPLETED DROP OF ALL NODES')
