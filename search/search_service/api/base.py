# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from http import HTTPStatus
from typing import (  # noqa: F401
    Any, Dict, Iterable,
)

from flask_restful import Resource, reqparse
from marshmallow3_annotations.ext.attrs import AttrsSchema

from search_service.proxy import get_proxy_client


class BaseFilterAPI(Resource):
    """
    Base Filter API for search filtering

    This API should be generic enough to support every search filter use case.
    """

    def __init__(self, *, schema: AttrsSchema, index: str) -> None:
        self.proxy = get_proxy_client()
        self.schema = schema
        self.index = index
        self.parser = reqparse.RequestParser(bundle_errors=True)

        self.parser.add_argument('page_index', required=False, default=0, type=int)
        self.parser.add_argument('query_term', required=False, type=str)
        self.parser.add_argument('search_request', type=dict)

        super(BaseFilterAPI, self).__init__()

    def post(self) -> Iterable[Any]:
        """
        Fetch search results based on the page_index, query_term, and
        search_request dictionary posted in the request JSON.
        :return: json payload of schema.
        doesn't match any tables
        """
        args = self.parser.parse_args(strict=True)
        page_index = args.get('page_index')  # type: int

        search_request = args.get('search_request')  # type: Dict
        if search_request is None:
            msg = 'The search request payload is not available in the request'
            return {'message': msg}, HTTPStatus.BAD_REQUEST

        query_term = args.get('query_term')  # type: str
        if ':' in query_term:
            msg = 'The query term contains an invalid character'
            return {'message': msg}, HTTPStatus.BAD_REQUEST

        try:
            results = self.proxy.fetch_search_results_with_filter(
                search_request=search_request,
                query_term=query_term,
                page_index=page_index,
                index=self.index
            )

            return self.schema().dump(results), HTTPStatus.OK
        except RuntimeError as e:
            raise e
