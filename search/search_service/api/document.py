# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import logging
from ast import literal_eval
from http import HTTPStatus
from typing import Any, Tuple

from flasgger import swag_from
from flask_restful import Resource, reqparse
from marshmallow.exceptions import ValidationError

from search_service.api.feature import FEATURE_INDEX
from search_service.api.table import TABLE_INDEX
from search_service.api.user import USER_INDEX
from search_service.models.feature import FeatureSchema
from search_service.models.table import TableSchema
from search_service.models.user import UserSchema
from search_service.proxy import get_proxy_client
from search_service.proxy.base import BaseProxy

LOGGER = logging.getLogger(__name__)


class BaseDocumentAPI(Resource):
    def __init__(self, schema: Any, proxy: BaseProxy) -> None:
        self.schema = schema
        self.proxy = proxy
        self.parser = reqparse.RequestParser(bundle_errors=True)
        super(BaseDocumentAPI, self).__init__()

    def delete(self, *, document_id: str) -> Tuple[Any, int]:
        """
        Uses the Elasticsearch bulk API to delete existing documents by id

        :param document_id: document id for document to be deleted
        :return:
        """
        args = self.parser.parse_args()

        try:
            self.proxy.delete_document(data=[document_id], index=args.get('index'))
            return {}, HTTPStatus.OK
        except RuntimeError as e:
            err_msg = 'Exception encountered while deleting document '
            LOGGER.error(err_msg + str(e))
            return {'message': err_msg}, HTTPStatus.INTERNAL_SERVER_ERROR


class BaseDocumentsAPI(Resource):
    def __init__(self, schema: Any, proxy: BaseProxy) -> None:
        self.schema = schema
        self.proxy = proxy
        self.parser = reqparse.RequestParser(bundle_errors=True)
        super(BaseDocumentsAPI, self).__init__()

    def post(self) -> Tuple[Any, int]:
        """
         Uses the Elasticsearch bulk API to load data from JSON. Uses Elasticsearch
         index actions to create or update documents by id

         :param data: list of data objects to be indexed in Elasticsearch
         :return: name of new index
         """
        self.parser.add_argument('data', required=True, action='append')
        args = self.parser.parse_args()

        try:
            data_list = [literal_eval(item) for item in args.get('data')]
            try:
                data = self.schema(many=True).load(data_list)
            except ValidationError as e:
                logging.warning("Invalid input: %s", e.messages)
                raise ValidationError("Invalid input")

            results = self.proxy.create_document(data=data, index=args.get('index'))
            return results, HTTPStatus.OK
        except RuntimeError as e:
            err_msg = 'Exception encountered while updating documents '
            LOGGER.error(err_msg + str(e))
            return {'message': err_msg}, HTTPStatus.INTERNAL_SERVER_ERROR

    def put(self) -> Tuple[Any, int]:
        """
        Uses the Elasticsearch bulk API to update existing documents by id. Will
        ignore ids it doesn't recognize (ids are defined in models)

        :param data: list of data objects to be indexed in Elasticsearch
        :return: name of index
        """
        self.parser.add_argument('data', required=True, action='append')
        args = self.parser.parse_args()

        try:
            data_list = [literal_eval(item) for item in args.get('data')]
            try:
                data = self.schema(many=True).load(data_list)
            except ValidationError as e:
                logging.warning("Invalid input: %s", e.messages)

                raise ValidationError("Invalid input")

            results = self.proxy.update_document(data=data, index=args.get('index'))
            return results, HTTPStatus.OK
        except RuntimeError as e:
            err_msg = 'Exception encountered while updating documents '
            LOGGER.error(err_msg + str(e))
            return {'message': err_msg}, HTTPStatus.INTERNAL_SERVER_ERROR


class DocumentTableAPI(BaseDocumentAPI):

    def __init__(self) -> None:
        super().__init__(schema=TableSchema, proxy=get_proxy_client())
        self.parser.add_argument('index', required=False, default=TABLE_INDEX, type=str)

    @swag_from('swagger_doc/document/table_delete.yml')
    def delete(self, *, document_id: str) -> Tuple[Any, int]:
        return super().delete(document_id=document_id)


class DocumentTablesAPI(BaseDocumentsAPI):

    def __init__(self) -> None:
        super().__init__(schema=TableSchema, proxy=get_proxy_client())
        self.parser.add_argument('index', required=False, default=TABLE_INDEX, type=str)

    @swag_from('swagger_doc/document/table_post.yml')
    def post(self) -> Tuple[Any, int]:
        return super().post()

    @swag_from('swagger_doc/document/table_put.yml')
    def put(self) -> Tuple[Any, int]:
        return super().put()


class DocumentUserAPI(BaseDocumentAPI):

    def __init__(self) -> None:
        super().__init__(schema=UserSchema, proxy=get_proxy_client())
        self.parser.add_argument('index', required=False, default=USER_INDEX, type=str)

    @swag_from('swagger_doc/document/user_delete.yml')
    def delete(self, *, document_id: str) -> Tuple[Any, int]:
        return super().delete(document_id=document_id)


class DocumentUsersAPI(BaseDocumentsAPI):

    def __init__(self) -> None:
        super().__init__(schema=UserSchema, proxy=get_proxy_client())
        self.parser.add_argument('index', required=False, default=USER_INDEX, type=str)

    @swag_from('swagger_doc/document/user_post.yml')
    def post(self) -> Tuple[Any, int]:
        return super().post()

    @swag_from('swagger_doc/document/user_put.yml')
    def put(self) -> Tuple[Any, int]:
        return super().put()


class DocumentFeatureAPI(BaseDocumentAPI):

    def __init__(self) -> None:
        super().__init__(schema=FeatureSchema, proxy=get_proxy_client())
        self.parser.add_argument('index', required=False, default=FEATURE_INDEX, type=str)

    @swag_from('swagger_doc/document/feature_delete.yml')
    def delete(self, *, document_id: str) -> Tuple[Any, int]:
        return super().delete(document_id=document_id)


class DocumentFeaturesAPI(BaseDocumentsAPI):

    def __init__(self) -> None:
        super().__init__(schema=FeatureSchema, proxy=get_proxy_client())
        self.parser.add_argument('index', required=False, default=FEATURE_INDEX, type=str)

    @swag_from('swagger_doc/document/feature_post.yml')
    def post(self) -> Tuple[Any, int]:
        return super().post()

    @swag_from('swagger_doc/document/feature_put.yml')
    def put(self) -> Tuple[Any, int]:
        return super().put()
