# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import logging
import json

from http import HTTPStatus

from typing import Any, Dict  # noqa: F401

from flask import Response, jsonify, make_response, request
from flask import current_app as app
from flask.blueprints import Blueprint

from amundsen_application.log.action_log import action_logging
from amundsen_application.api.utils.metadata_utils import marshall_dashboard_partial
from amundsen_application.api.utils.request_utils import get_query_param, request_search
from amundsen_application.api.utils.search_utils import generate_query_json, has_filters, \
    map_feature_result, map_table_result, transform_filters
from amundsen_application.models.user import load_user, dump_user

LOGGER = logging.getLogger(__name__)

REQUEST_SESSION_TIMEOUT_SEC = 3

search_blueprint = Blueprint('search', __name__, url_prefix='/api/search/v0')

SEARCH_DASHBOARD_ENDPOINT = '/search_dashboard'
SEARCH_DASHBOARD_FILTER_ENDPOINT = '/search_dashboard_filter'
SEARCH_TABLE_ENDPOINT = '/search'
SEARCH_TABLE_FILTER_ENDPOINT = '/search_table'
SEARCH_FEATURE_ENDPOINT = '/search_feature'
SEARCH_FEATURE_FILTER_ENDPOINT = '/search_feature_filter'
SEARCH_USER_ENDPOINT = '/search_user'


@search_blueprint.route('/table', methods=['POST'])
def search_table() -> Response:
    """
    Parse the request arguments and call the helper method to execute a table search
    :return: a Response created with the results from the helper method
    """
    results_dict = {}
    try:
        request_json = request.get_json()

        search_term = get_query_param(request_json, 'term', '"term" parameter expected in request data')
        page_index = get_query_param(request_json, 'pageIndex', '"pageIndex" parameter expected in request data')

        search_type = request_json.get('searchType')

        transformed_filters = transform_filters(filters=request_json.get('filters', {}), resource='table')

        results_dict = _search_table(filters=transformed_filters,
                                     search_term=search_term,
                                     page_index=page_index,
                                     search_type=search_type)
        return make_response(jsonify(results_dict), results_dict.get('status_code', HTTPStatus.INTERNAL_SERVER_ERROR))
    except Exception as e:
        message = 'Encountered exception: ' + str(e)
        logging.exception(message)
        return make_response(jsonify(results_dict), HTTPStatus.INTERNAL_SERVER_ERROR)


@action_logging
def _search_table(*, search_term: str, page_index: int, filters: Dict, search_type: str) -> Dict[str, Any]:
    """
    Call the search service endpoint and return matching results
    Search service logic defined here:
    https://github.com/lyft/amundsensearchlibrary/blob/master/search_service/api/table.py

    :return: a json output containing search results array as 'results'
    """
    # Default results
    tables = {
        'page_index': int(page_index),
        'results': [],
        'total_results': 0,
    }

    results_dict = {
        'search_term': search_term,
        'msg': '',
        'tables': tables,
    }

    try:
        if has_filters(filters=filters, resource='table'):
            query_json = generate_query_json(filters=filters, page_index=page_index, search_term=search_term)
            url_base = app.config['SEARCHSERVICE_BASE'] + SEARCH_TABLE_FILTER_ENDPOINT
            response = request_search(url=url_base,
                                      headers={'Content-Type': 'application/json'},
                                      method='POST',
                                      data=json.dumps(query_json))
        else:
            url_base = app.config['SEARCHSERVICE_BASE'] + SEARCH_TABLE_ENDPOINT
            url = f'{url_base}?query_term={search_term}&page_index={page_index}'
            response = request_search(url=url)

        status_code = response.status_code
        if status_code == HTTPStatus.OK:
            results_dict['msg'] = 'Success'
            results = response.json().get('results')
            tables['results'] = [map_table_result(result) for result in results]
            tables['total_results'] = response.json().get('total_results')
        else:
            message = 'Encountered error: Search request failed'
            results_dict['msg'] = message
            logging.error(message)

        results_dict['status_code'] = status_code
        return results_dict
    except Exception as e:
        message = 'Encountered exception: ' + str(e)
        results_dict['msg'] = message
        logging.exception(message)
        return results_dict


@search_blueprint.route('/user', methods=['GET'])
def search_user() -> Response:
    """
    Parse the request arguments and call the helper method to execute a user search
    :return: a Response created with the results from the helper method
    """
    results_dict = {}
    try:
        search_term = get_query_param(request.args, 'query', 'Endpoint takes a "query" parameter')
        page_index = get_query_param(request.args, 'page_index', 'Endpoint takes a "page_index" parameter')
        search_type = request.args.get('search_type')

        results_dict = _search_user(search_term=search_term, page_index=int(page_index), search_type=search_type)

        return make_response(jsonify(results_dict), results_dict.get('status_code', HTTPStatus.INTERNAL_SERVER_ERROR))
    except Exception as e:
        message = 'Encountered exception: ' + str(e)
        logging.exception(message)
        return make_response(jsonify(results_dict), HTTPStatus.INTERNAL_SERVER_ERROR)


@action_logging
def _search_user(*, search_term: str, page_index: int, search_type: str) -> Dict[str, Any]:
    """
    Call the search service endpoint and return matching results
    Search service logic defined here:
    https://github.com/lyft/amundsensearchlibrary/blob/master/search_service/api/user.py

    :return: a json output containing search results array as 'results'
    """

    def _map_user_result(result: Dict) -> Dict:
        user_result = dump_user(load_user(result))
        user_result['type'] = 'user'
        return user_result

    users = {
        'page_index': page_index,
        'results': [],
        'total_results': 0,
    }

    results_dict = {
        'search_term': search_term,
        'msg': 'Success',
        'status_code': HTTPStatus.OK,
        'users': users,
    }

    try:
        url_base = app.config['SEARCHSERVICE_BASE'] + SEARCH_USER_ENDPOINT
        url = f'{url_base}?query_term={search_term}&page_index={page_index}'

        response = request_search(url=url)
        status_code = response.status_code

        if status_code == HTTPStatus.OK:
            results_dict['msg'] = 'Success'
            results = response.json().get('results', list())
            users['results'] = [_map_user_result(result) for result in results]
            users['total_results'] = response.json().get('total_results', 0)
        else:
            message = 'Encountered error: Search request failed'
            results_dict['msg'] = message
            logging.error(message)

        results_dict['status_code'] = status_code
        return results_dict
    except Exception as e:
        message = 'Encountered exception: ' + str(e)
        results_dict['msg'] = message
        results_dict['status_code'] = HTTPStatus.INTERNAL_SERVER_ERROR
        logging.exception(message)
        return results_dict


@search_blueprint.route('/dashboard', methods=['POST'])
def search_dashboard() -> Response:
    """
    Parse the request arguments and call the helper method to execute a dashboard search
    :return: a Response created with the results from the helper method
    """
    results_dict = {}
    try:
        request_json = request.get_json()

        search_term = get_query_param(request_json, 'term', '"term" parameter expected in request data')
        page_index = get_query_param(request_json, 'pageIndex', '"pageIndex" parameter expected in request data')
        search_type = request_json.get('searchType')
        transformed_filters = transform_filters(filters=request_json.get('filters', {}), resource='dashboard')

        results_dict = _search_dashboard(filters=transformed_filters,
                                         search_term=search_term,
                                         page_index=page_index,
                                         search_type=search_type)

        return make_response(jsonify(results_dict), results_dict.get('status_code', HTTPStatus.INTERNAL_SERVER_ERROR))
    except Exception as e:
        message = 'Encountered exception: ' + str(e)
        logging.exception(message)
        return make_response(jsonify(results_dict), HTTPStatus.INTERNAL_SERVER_ERROR)


@action_logging
def _search_dashboard(*, search_term: str, page_index: int, filters: Dict, search_type: str) -> Dict[str, Any]:
    """
    Call the search service endpoint and return matching results
    Search service logic defined here:
    https://github.com/lyft/amundsensearchlibrary/blob/master/search_service/api/dashboard.py

    :return: a json output containing search results array as 'results'
    """
    # Default results
    dashboards = {
        'page_index': page_index,
        'results': [],
        'total_results': 0,
    }

    results_dict = {
        'search_term': search_term,
        'msg': '',
        'dashboards': dashboards,
    }

    try:
        if has_filters(filters=filters, resource='dashboard'):
            query_json = generate_query_json(filters=filters, page_index=page_index, search_term=search_term)
            url_base = app.config['SEARCHSERVICE_BASE'] + SEARCH_DASHBOARD_FILTER_ENDPOINT
            response = request_search(url=url_base,
                                      headers={'Content-Type': 'application/json'},
                                      method='POST',
                                      data=json.dumps(query_json))
        else:
            url_base = app.config['SEARCHSERVICE_BASE'] + SEARCH_DASHBOARD_ENDPOINT
            url = f'{url_base}?query_term={search_term}&page_index={page_index}'
            response = request_search(url=url)

        status_code = response.status_code
        if status_code == HTTPStatus.OK:
            results_dict['msg'] = 'Success'
            results = response.json().get('results')
            dashboards['results'] = [marshall_dashboard_partial(result) for result in results]
            dashboards['total_results'] = response.json().get('total_results')
        else:
            message = 'Encountered error: Search request failed'
            results_dict['msg'] = message
            logging.error(message)

        results_dict['status_code'] = status_code
        return results_dict
    except Exception as e:
        message = 'Encountered exception: ' + str(e)
        results_dict['msg'] = message
        logging.exception(message)
        return results_dict


@search_blueprint.route('/feature', methods=['POST'])
def search_feature() -> Response:
    """
    Parse the request arguments and call the helper method to execute a feature search
    :return: a Response created with the results from the helper method
    """
    results_dict = {}
    try:
        request_json = request.get_json()

        search_term = get_query_param(request_json, 'term', '"term" parameter expected in request data')
        page_index = get_query_param(request_json, 'pageIndex', '"pageIndex" parameter expected in request data')

        search_type = request_json.get('searchType')

        transformed_filters = transform_filters(filters=request_json.get('filters', {}), resource='feature')

        results_dict = _search_feature(filters=transformed_filters,
                                       search_term=search_term,
                                       page_index=page_index,
                                       search_type=search_type)
        return make_response(jsonify(results_dict), results_dict.get('status_code', HTTPStatus.OK))
    except Exception as e:
        message = 'Encountered exception: ' + str(e)
        logging.exception(message)
        return make_response(jsonify(results_dict), HTTPStatus.INTERNAL_SERVER_ERROR)


@action_logging
def _search_feature(*, search_term: str, page_index: int, filters: Dict, search_type: str) -> Dict[str, Any]:
    """
    Call the search service endpoint and return matching results
    Search service logic defined here:
    TODO put URL to search API file here

    :return: a json output containing search results array as 'results'
    """
    # Default results
    features = {
        'page_index': page_index,
        'results': [],
        'total_results': 0,
    }

    results_dict = {
        'search_term': search_term,
        'msg': 'Success',
        'features': features,
    }

    try:
        if has_filters(filters=filters, resource='feature'):
            query_json = generate_query_json(filters=filters, page_index=page_index, search_term=search_term)
            url_base = app.config['SEARCHSERVICE_BASE'] + SEARCH_FEATURE_FILTER_ENDPOINT
            response = request_search(url=url_base,
                                      headers={'Content-Type': 'application/json'},
                                      method='POST',
                                      data=json.dumps(query_json))
        else:
            url_base = app.config['SEARCHSERVICE_BASE'] + SEARCH_FEATURE_ENDPOINT
            url = f'{url_base}?query_term={search_term}&page_index={page_index}'
            response = request_search(url=url)

        status_code = response.status_code
        if status_code == HTTPStatus.OK:
            results_dict['msg'] = 'Success'
            results = response.json().get('results')
            features['results'] = [map_feature_result(result) for result in results]
            features['total_results'] = response.json().get('total_results')
        else:
            message = 'Encountered error: Search request failed'
            results_dict['msg'] = message
            logging.error(message)

        results_dict['status_code'] = status_code
        return results_dict
    except Exception as e:
        message = 'Encountered exception: ' + str(e)
        results_dict['msg'] = message
        logging.exception(message)
        return results_dict
