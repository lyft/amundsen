# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from typing import Dict

import requests
from flask import current_app as app


def get_query_param(args: Dict, param: str, error_msg: str = None) -> str:
    value = args.get(param)
    if value is None:
        msg = 'A {0} parameter must be provided'.format(param) if error_msg is None else error_msg
        raise Exception(msg)
    return value


def request_metadata(*,     # type: ignore
                     url: str,
                     method: str = 'GET',
                     headers=None,
                     timeout_sec: int = 0,
                     data=None,
                     json=None):
    """
    Helper function to make a request to metadata service.
    Sets the client and header information based on the configuration
    :param headers: Optional headers for the request, e.g. specifying Content-Type
    :param method: DELETE | GET | POST | PUT
    :param url: The request URL
    :param timeout_sec: Number of seconds before timeout is triggered.
    :param data: Optional request payload
    :return:
    """
    if headers is None:
        headers = {}

    if app.config['REQUEST_HEADERS_METHOD']:
        headers.update(app.config['REQUEST_HEADERS_METHOD'](app))
    elif app.config['METADATASERVICE_REQUEST_HEADERS']:
        headers.update(app.config['METADATASERVICE_REQUEST_HEADERS'])
    return request_wrapper(method=method,
                           url=url,
                           client=app.config['METADATASERVICE_REQUEST_CLIENT'],
                           headers=headers,
                           timeout_sec=timeout_sec,
                           data=data,
                           json=json)


def request_search(*,     # type: ignore
                   url: str,
                   method: str = 'GET',
                   headers=None,
                   timeout_sec: int = 0,
                   data=None,
                   json=None):
    """
    Helper function to make a request to search service.
    Sets the client and header information based on the configuration
    :param headers: Optional headers for the request, e.g. specifying Content-Type
    :param method: DELETE | GET | POST | PUT
    :param url: The request URL
    :param timeout_sec: Number of seconds before timeout is triggered.
    :param data: Optional request payload
    :return:
    """
    if headers is None:
        headers = {}

    if app.config['REQUEST_HEADERS_METHOD']:
        headers.update(app.config['REQUEST_HEADERS_METHOD'](app))
    elif app.config['SEARCHSERVICE_REQUEST_HEADERS']:
        headers.update(app.config['SEARCHSERVICE_REQUEST_HEADERS'])

    return request_wrapper(method=method,
                           url=url,
                           client=app.config['SEARCHSERVICE_REQUEST_CLIENT'],
                           headers=headers,
                           timeout_sec=timeout_sec,
                           data=data,
                           json=json)


# TODO: Define an interface for envoy_client
def request_wrapper(method: str, url: str, client, headers, timeout_sec: int, data=None, json=None):  # type: ignore
    """
    Wraps a request to use Envoy client and headers, if available
    :param method: DELETE | GET | POST | PUT
    :param url: The request URL
    :param client: Optional Envoy client
    :param headers: Optional Envoy request headers
    :param timeout_sec: Number of seconds before timeout is triggered. Not used with Envoy
    :param data: Optional request payload
    :return:
    """
    # If no timeout specified, use the one from the configurations.
    timeout_sec = timeout_sec or app.config['REQUEST_SESSION_TIMEOUT_SEC']

    if client is not None:
        if method == 'DELETE':
            return client.delete(url, headers=headers, raw_response=True)
        elif method == 'GET':
            return client.get(url, headers=headers, raw_response=True)
        elif method == 'POST':
            return client.post(url, headers=headers, raw_response=True, raw_request=True, data=data, json=json)
        elif method == 'PUT':
            return client.put(url, headers=headers, raw_response=True, raw_request=True, data=data, json=json)
        else:
            raise Exception('Method not allowed: {}'.format(method))
    else:
        with build_session() as s:
            if method == 'DELETE':
                return s.delete(url, headers=headers, timeout=timeout_sec)
            elif method == 'GET':
                return s.get(url, headers=headers, timeout=timeout_sec)
            elif method == 'POST':
                return s.post(url, headers=headers, timeout=timeout_sec, data=data, json=json)
            elif method == 'PUT':
                return s.put(url, headers=headers, timeout=timeout_sec, data=data, json=json)
            else:
                raise Exception('Method not allowed: {}'.format(method))


def build_session() -> requests.Session:
    session = requests.Session()

    cert = app.config.get('MTLS_CLIENT_CERT')
    key = app.config.get('MTLS_CLIENT_KEY')
    if cert is not None and key is not None:
        session.cert = (cert, key)

    return session
