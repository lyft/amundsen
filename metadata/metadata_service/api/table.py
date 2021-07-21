# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import json
from http import HTTPStatus
from typing import Any, Iterable, Mapping, Optional, Union

from amundsen_common.entity.resource_type import ResourceType
from amundsen_common.models.lineage import LineageSchema
from amundsen_common.models.table import TableSchema
from flasgger import swag_from
from flask import request
from flask_restful import Resource, reqparse

from metadata_service.api import BaseAPI
from metadata_service.api.badge import BadgeCommon
from metadata_service.api.tag import TagCommon
from metadata_service.entity.dashboard_summary import DashboardSummarySchema
from metadata_service.exception import NotFoundException
from metadata_service.proxy import get_proxy_client


class TableDetailAPI(Resource):
    """
    TableDetail API
    """

    def __init__(self) -> None:
        self.client = get_proxy_client()

    @swag_from('swagger_doc/table/detail_get.yml')
    def get(self, table_uri: str) -> Iterable[Union[Mapping, int, None]]:
        try:
            table = self.client.get_table(table_uri=table_uri)
            schema = TableSchema()
            return schema.dump(table), HTTPStatus.OK

        except NotFoundException:
            return {'message': 'table_uri {} does not exist'.format(table_uri)}, HTTPStatus.NOT_FOUND


class TableLineageAPI(Resource):
    def __init__(self) -> None:
        self.client = get_proxy_client()
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('direction', type=str, required=False, default="both")
        self.parser.add_argument('depth', type=int, required=False, default=1)
        super(TableLineageAPI, self).__init__()

    @swag_from('swagger_doc/table/lineage_get.yml')
    def get(self, id: str) -> Iterable[Union[Mapping, int, None]]:
        args = self.parser.parse_args()
        direction = args.get('direction')
        depth = args.get('depth')
        try:
            lineage = self.client.get_lineage(id=id,
                                              resource_type=ResourceType.Table,
                                              direction=direction,
                                              depth=depth)
            schema = LineageSchema()
            return schema.dump(lineage), HTTPStatus.OK
        except Exception as e:
            return {'message': f'Exception raised when getting lineage: {e}'}, HTTPStatus.NOT_FOUND


class TableOwnerAPI(Resource):
    """
    TableOwner API to add / delete owner info
    """

    def __init__(self) -> None:
        self.client = get_proxy_client()

    @swag_from('swagger_doc/table/owner_put.yml')
    def put(self, table_uri: str, owner: str) -> Iterable[Union[Mapping, int, None]]:
        try:
            self.client.add_owner(table_uri=table_uri, owner=owner)
            return {'message': 'The owner {} for table_uri {} '
                               'is added successfully'.format(owner,
                                                              table_uri)}, HTTPStatus.OK
        except Exception:
            return {'message': 'The owner {} for table_uri {} '
                               'is not added successfully'.format(owner,
                                                                  table_uri)}, HTTPStatus.INTERNAL_SERVER_ERROR

    @swag_from('swagger_doc/table/owner_delete.yml')
    def delete(self, table_uri: str, owner: str) -> Iterable[Union[Mapping, int, None]]:
        try:
            self.client.delete_owner(table_uri=table_uri, owner=owner)
            return {'message': 'The owner {} for table_uri {} '
                               'is deleted successfully'.format(owner,
                                                                table_uri)}, HTTPStatus.OK
        except Exception:
            return {'message': 'The owner {} for table_uri {} '
                               'is not deleted successfully'.format(owner,
                                                                    table_uri)}, HTTPStatus.INTERNAL_SERVER_ERROR


class TableDescriptionAPI(Resource):
    """
    TableDescriptionAPI supports PUT and GET operation to upsert table description
    """

    def __init__(self) -> None:
        self.client = get_proxy_client()
        super(TableDescriptionAPI, self).__init__()

    @swag_from('swagger_doc/common/description_get.yml')
    def get(self, id: str) -> Iterable[Any]:
        """
        Returns description in Neo4j endpoint
        """
        try:
            description = self.client.get_table_description(table_uri=id)
            return {'description': description}, HTTPStatus.OK

        except NotFoundException:
            return {'message': 'table_uri {} does not exist'.format(id)}, HTTPStatus.NOT_FOUND

        except Exception:
            return {'message': 'Internal server error!'}, HTTPStatus.INTERNAL_SERVER_ERROR

    @swag_from('swagger_doc/common/description_put.yml')
    def put(self, id: str) -> Iterable[Any]:
        """
        Updates table description (passed as a request body)
        :param table_uri:
        :return:
        """
        try:
            description = json.loads(request.data).get('description')
            self.client.put_table_description(table_uri=id, description=description)
            return None, HTTPStatus.OK

        except NotFoundException:
            return {'message': 'table_uri {} does not exist'.format(id)}, HTTPStatus.NOT_FOUND


class TableTagAPI(Resource):
    """
    TableTagAPI that supports GET, PUT and DELETE operation to add or delete tag
    on table
    """

    def __init__(self) -> None:
        self.client = get_proxy_client()
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('tag_type', type=str, required=False, default='default')
        super(TableTagAPI, self).__init__()

        self._tag_common = TagCommon(client=self.client)

    @swag_from('swagger_doc/tag/tag_put.yml')
    def put(self, id: str, tag: str) -> Iterable[Union[Mapping, int, None]]:
        """
        API to add a tag to existing table uri.

        :param table_uri:
        :param tag:
        :return:
        """
        args = self.parser.parse_args()
        # use tag_type to distinguish between tag and badge
        tag_type = args.get('tag_type', 'default')

        return self._tag_common.put(id=id,
                                    resource_type=ResourceType.Table,
                                    tag=tag,
                                    tag_type=tag_type)

    @swag_from('swagger_doc/tag/tag_delete.yml')
    def delete(self, id: str, tag: str) -> Iterable[Union[Mapping, int, None]]:
        """
        API to remove a association between a given tag and a table.

        :param table_uri:
        :param tag:
        :return:
        """
        args = self.parser.parse_args()
        tag_type = args.get('tag_type', 'default')

        return self._tag_common.delete(id=id,
                                       resource_type=ResourceType.Table,
                                       tag=tag,
                                       tag_type=tag_type)


class TableBadgeAPI(Resource):
    def __init__(self) -> None:
        self.client = get_proxy_client()
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('category', type=str, required=True)
        super(TableBadgeAPI, self).__init__()

        self._badge_common = BadgeCommon(client=self.client)

    @swag_from('swagger_doc/badge/badge_put.yml')
    def put(self, id: str, badge: str) -> Iterable[Union[Mapping, int, None]]:
        args = self.parser.parse_args()
        category = args.get('category', '')

        return self._badge_common.put(id=id,
                                      resource_type=ResourceType.Table,
                                      badge_name=badge,
                                      category=category)

    @swag_from('swagger_doc/badge/badge_delete.yml')
    def delete(self, id: str, badge: str) -> Iterable[Union[Mapping, int, None]]:
        args = self.parser.parse_args()
        category = args.get('category', '')

        return self._badge_common.delete(id=id,
                                         resource_type=ResourceType.Table,
                                         badge_name=badge,
                                         category=category)


class TableDashboardAPI(BaseAPI):
    """
    TableDashboard API that supports GET operation providing list of Dashboards using a table.
    """

    def __init__(self) -> None:
        self.client = get_proxy_client()
        super().__init__(DashboardSummarySchema, 'resources_using_table', self.client)

    @swag_from('swagger_doc/table/dashboards_using_table_get.yml')
    def get(self, *, id: Optional[str] = None) -> Iterable[Union[Mapping, int, None]]:
        """
        Supports GET operation providing list of Dashboards using a table.
        :param id: Table URI
        :return: See Swagger doc for the schema. swagger_doc/table/dashboards_using_table_get.yml
        """
        try:
            return super().get_with_kwargs(id=id, resource_type=ResourceType.Dashboard)
        except NotFoundException:
            return {'message': 'table_id {} does not exist'.format(id)}, HTTPStatus.NOT_FOUND
