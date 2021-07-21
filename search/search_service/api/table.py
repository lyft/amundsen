# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from http import HTTPStatus
from typing import Any, Iterable  # noqa: F401

from flasgger import swag_from
from flask_restful import Resource, reqparse

from search_service.api.base import BaseFilterAPI
from search_service.models.table import SearchTableResultSchema
from search_service.proxy import get_proxy_client

TABLE_INDEX = 'table_search_index'


class SearchTableAPI(Resource):
    """
    Search Table API
    """

    def __init__(self) -> None:
        self.proxy = get_proxy_client()

        self.parser = reqparse.RequestParser(bundle_errors=True)

        self.parser.add_argument('query_term', required=True, type=str)
        self.parser.add_argument('page_index', required=False, default=0, type=int)
        self.parser.add_argument('index', required=False, default=TABLE_INDEX, type=str)

        super(SearchTableAPI, self).__init__()

    @swag_from('swagger_doc/table/search_table.yml')
    def get(self) -> Iterable[Any]:
        """
        Fetch search results based on query_term.

        :return: list of table results. List can be empty if query
        doesn't match any tables
        """
        args = self.parser.parse_args(strict=True)

        try:

            results = self.proxy.fetch_table_search_results(
                query_term=args.get('query_term'),
                page_index=args.get('page_index'),
                index=args.get('index')
            )

            return SearchTableResultSchema().dump(results), HTTPStatus.OK

        except RuntimeError:

            err_msg = 'Exception encountered while processing search request'
            return {'message': err_msg}, HTTPStatus.INTERNAL_SERVER_ERROR


class SearchTableFilterAPI(BaseFilterAPI):
    """
    Search Filter for table
    """

    def __init__(self) -> None:
        super().__init__(schema=SearchTableResultSchema,
                         index=TABLE_INDEX)

    @swag_from('swagger_doc/table/search_table_filter.yml')
    def post(self) -> Iterable[Any]:
        try:
            return super().post()
        except RuntimeError:
            err_msg = 'Exception encountered while processing search request'
            return {'message': err_msg}, HTTPStatus.INTERNAL_SERVER_ERROR
