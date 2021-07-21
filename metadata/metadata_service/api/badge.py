# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from http import HTTPStatus
from typing import Any, Iterable, Mapping, Tuple, Union

from amundsen_common.entity.resource_type import ResourceType
from flasgger import swag_from
from flask import current_app as app
from flask_restful import Resource, fields, marshal

from metadata_service.entity.badge import Badge
from metadata_service.exception import NotFoundException
from metadata_service.proxy import get_proxy_client
from metadata_service.proxy.base_proxy import BaseProxy

badge_fields = {
    'badge_name': fields.String,
    'category': fields.String,
}

badges_fields = {
    'badges': fields.List(fields.Nested(badge_fields))
}


class BadgeAPI(Resource):
    def __init__(self) -> None:
        self.client = get_proxy_client()
        super(BadgeAPI, self).__init__()

    @swag_from('swagger_doc/badge/badge_get.yml')
    def get(self) -> Iterable[Union[Mapping, int, None]]:
        """
        API to get all existing badges
        """
        badges = self.client.get_badges()
        return marshal({'badges': badges}, badges_fields), HTTPStatus.OK


class BadgeCommon:
    def __init__(self, client: BaseProxy) -> None:
        self.client = client

    def put(self, id: str, resource_type: ResourceType,
            badge_name: str,
            category: str = '') -> Tuple[Any, HTTPStatus]:

        if category == '':
            return \
                {'message': f'The badge {badge_name} for resource id {id} is not added successfully because '
                            f'category `{category}` parameter is required '
                            'for badges'}, \
                HTTPStatus.NOT_FOUND

        # TODO check resource type is column when adding a badge of category column after
        # implementing column level badges
        whitelist_badges = app.config.get('WHITELIST_BADGES', [])
        incomimg_badge = Badge(badge_name=badge_name,
                               category=category)
        # need to check whether the badge combination is part of the whitelist:

        in_whitelist = False
        for badge in whitelist_badges:
            if incomimg_badge.badge_name == badge.badge_name and incomimg_badge.category == badge.category:
                in_whitelist = True
        if not in_whitelist:
            return \
                {'message': f'The badge {badge_name} with category {category} for resource '
                            f'id {id} and resource_type {resource_type.name} is not added successfully because '
                            'this combination of values is not part of the whitelist'}, \
                HTTPStatus.NOT_FOUND

        try:
            self.client.add_badge(id=id,
                                  badge_name=badge_name,
                                  category=category,
                                  resource_type=resource_type)
            return {'message': f'The badge {badge_name} with category {category} was '
                               f'added successfully to resource with id {id}'}, HTTPStatus.OK
        except Exception as e:
            return {'message': f'The badge {badge_name} with category {category} '
                               f'for resource id {id} and resource_type {resource_type.name} failed to '
                               'be added'}, \
                HTTPStatus.NOT_FOUND

    def delete(self, id: str, badge_name: str,
               category: str,
               resource_type: ResourceType) -> Tuple[Any, HTTPStatus]:
        try:
            self.client.delete_badge(id=id,
                                     resource_type=resource_type,
                                     badge_name=badge_name,
                                     category=category)
            return \
                {'message': f'The badge {badge_name} with category {category} for resource '
                            f'id {id} and resource_type {resource_type.name} was deleted successfully'}, \
                HTTPStatus.OK
        except NotFoundException:
            return \
                {'message': f'The badge {badge_name} with category {category} for resource '
                            f'id {id} and resource_type {resource_type.name} was not deleted successfully'}, \
                HTTPStatus.NOT_FOUND
