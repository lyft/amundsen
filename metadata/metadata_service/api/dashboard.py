# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import json
from http import HTTPStatus
from typing import Iterable, Mapping, Optional, Union

from amundsen_common.entity.resource_type import ResourceType
from flasgger import swag_from
from flask import request
from flask_restful import Resource, reqparse

from metadata_service.api import BaseAPI
from metadata_service.api.badge import BadgeCommon
from metadata_service.api.tag import TagCommon
from metadata_service.entity.dashboard_detail import DashboardSchema
from metadata_service.entity.description import DescriptionSchema
from metadata_service.exception import NotFoundException
from metadata_service.proxy import get_proxy_client


class DashboardDetailAPI(BaseAPI):
    """
    Dashboard detail API
    """

    def __init__(self) -> None:
        self.client = get_proxy_client()
        super().__init__(DashboardSchema, 'dashboard', self.client)

    @swag_from('swagger_doc/dashboard/detail_get.yml')
    def get(self, *, id: Optional[str] = None) -> Iterable[Union[Mapping, int, None]]:
        try:
            return super().get(id=id)
        except NotFoundException:
            return {'message': 'dashboard_id {} does not exist'.format(id)}, HTTPStatus.NOT_FOUND


class DashboardDescriptionAPI(BaseAPI):
    """
    DashboardDescriptionAPI supports PUT and GET operation to upsert table description
    """

    def __init__(self) -> None:
        self.client = get_proxy_client()
        super().__init__(DescriptionSchema, 'dashboard_description', self.client)

    @swag_from('swagger_doc/common/description_get.yml')
    def get(self, *, id: Optional[str] = None) -> Iterable[Union[Mapping, int, None]]:
        """
        Returns description
        """
        try:
            return super().get(id=id)

        except NotFoundException:
            return {'message': 'Dashboard {} does not exist'.format(id)}, HTTPStatus.NOT_FOUND

        except Exception:
            return {'message': 'Internal server error!'}, HTTPStatus.INTERNAL_SERVER_ERROR

    @swag_from('swagger_doc/common/description_put.yml')
    def put(self, id: str) -> Iterable[Union[Mapping, int, None]]:
        """
        Updates Dashboard description (passed as a request body)
        :param id:
        :return:
        """
        try:
            description = json.loads(request.data).get('description')
            self.client.put_dashboard_description(id=id, description=description)
            return None, HTTPStatus.OK

        except NotFoundException:
            return {'message': 'id {} does not exist'.format(id)}, HTTPStatus.NOT_FOUND


class DashboardBadgeAPI(Resource):
    """
    DashboardBadgeAPI that supports PUT and DELETE operation to add or delete badges
    on Dashboard
    """
    def __init__(self) -> None:
        self.client = get_proxy_client()
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('category', type=str, required=True)
        super(DashboardBadgeAPI, self).__init__()

        self._badge_common = BadgeCommon(client=self.client)

    @swag_from('swagger_doc/badge/badge_put.yml')
    def put(self, id: str, badge: str) -> Iterable[Union[Mapping, int, None]]:
        args = self.parser.parse_args()

        category = args.get('category', '')

        return self._badge_common.put(id=id,
                                      resource_type=ResourceType.Dashboard,
                                      badge_name=badge,
                                      category=category)

    @swag_from('swagger_doc/badge/badge_delete.yml')
    def delete(self, id: str, badge: str) -> Iterable[Union[Mapping, int, None]]:
        args = self.parser.parse_args()
        category = args.get('category', '')

        return self._badge_common.delete(id=id,
                                         resource_type=ResourceType.Dashboard,
                                         badge_name=badge,
                                         category=category)


class DashboardTagAPI(Resource):
    """
    DashboardTagAPI that supports PUT and DELETE operation to add or delete tag
    on Dashboard
    """

    def __init__(self) -> None:
        self.client = get_proxy_client()
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('tag_type', type=str, required=False, default='default')
        super(DashboardTagAPI, self).__init__()

        self._tag_common = TagCommon(client=self.client)

    @swag_from('swagger_doc/tag/tag_put.yml')
    def put(self, id: str, tag: str) -> Iterable[Union[Mapping, int, None]]:
        """
        API to add a tag to existing Dashboard.

        :param table_uri:
        :param tag:
        :return:
        """
        args = self.parser.parse_args()
        tag_type = args.get('tag_type', 'default')

        return self._tag_common.put(id=id,
                                    resource_type=ResourceType.Dashboard,
                                    tag=tag,
                                    tag_type=tag_type)

    @swag_from('swagger_doc/tag/tag_delete.yml')
    def delete(self, id: str, tag: str) -> Iterable[Union[Mapping, int, None]]:
        """
        API to remove a association between a given tag and a Dashboard.

        :param table_uri:
        :param tag:
        :return:
        """
        args = self.parser.parse_args()
        tag_type = args.get('tag_type', 'default')

        return self._tag_common.delete(id=id,
                                       resource_type=ResourceType.Dashboard,
                                       tag=tag,
                                       tag_type=tag_type)
