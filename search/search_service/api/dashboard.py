# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import logging
from http import HTTPStatus
from typing import Any, Iterable

from flasgger import swag_from
from flask_restful import Resource, reqparse  # noqa: I201

from search_service.api.base import BaseFilterAPI
from search_service.exception import NotFoundException
from search_service.models.dashboard import SearchDashboardResultSchema
from search_service.proxy import get_proxy_client

DASHBOARD_INDEX = 'dashboard_search_index'

LOGGING = logging.getLogger(__name__)


class SearchDashboardAPI(Resource):
    """
    Search Dashboard API
    """

    def __init__(self) -> None:
        self.proxy = get_proxy_client()

        self.parser = reqparse.RequestParser(bundle_errors=True)

        self.parser.add_argument('query_term', required=True, type=str)
        self.parser.add_argument('page_index', required=False, default=0, type=int)
        self.parser.add_argument('index', required=False, default=DASHBOARD_INDEX, type=str)

        super(SearchDashboardAPI, self).__init__()

    @swag_from('swagger_doc/dashboard/search_dashboard.yml')
    def get(self) -> Iterable[Any]:
        """
        Fetch dashboard search results based on query_term.

        :return: list of dashboard  results. List can be empty if query
        doesn't match any dashboards
        """
        args = self.parser.parse_args(strict=True)
        try:
            results = self.proxy.fetch_dashboard_search_results(
                query_term=args.get('query_term'),
                page_index=args['page_index'],
                index=args['index']
            )

            return SearchDashboardResultSchema().dump(results), HTTPStatus.OK

        except NotFoundException:
            return {'message': 'query_term does not exist'}, HTTPStatus.NOT_FOUND

        except Exception:

            err_msg = 'Exception encountered while processing search request'
            LOGGING.exception(err_msg)
            return {'message': err_msg}, HTTPStatus.INTERNAL_SERVER_ERROR


class SearchDashboardFilterAPI(BaseFilterAPI):
    """
    Search Filter for Dashboard
    """

    def __init__(self) -> None:
        super().__init__(schema=SearchDashboardResultSchema,
                         index=DASHBOARD_INDEX)

    @swag_from('swagger_doc/dashboard/search_dashboard_filter.yml')
    def post(self) -> Iterable[Any]:
        try:
            return super().post()
        except RuntimeError:
            err_msg = 'Exception encountered while processing search request'
            return {'message': err_msg}, HTTPStatus.INTERNAL_SERVER_ERROR
