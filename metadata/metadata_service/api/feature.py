import json
import logging
from http import HTTPStatus
from typing import Any, Iterable, Mapping, Union

from amundsen_common.entity.resource_type import ResourceType
from amundsen_common.models.feature import FeatureSchema
from amundsen_common.models.generation_code import GenerationCodeSchema
from amundsen_common.models.lineage import LineageSchema
from flasgger import swag_from
from flask import request
from flask_restful import Resource, reqparse

from metadata_service.api.badge import BadgeCommon
from metadata_service.api.tag import TagCommon
from metadata_service.exception import NotFoundException
from metadata_service.proxy import get_proxy_client

LOGGER = logging.getLogger(__name__)


class FeatureDetailAPI(Resource):
    """
    FeatureDetail API
    """

    def __init__(self) -> None:
        self.client = get_proxy_client()

    @swag_from('swagger_doc/feature/detail_get.yml')
    def get(self, feature_uri: str) -> Iterable[Union[Mapping, int, None]]:
        try:
            feature = self.client.get_feature(feature_uri=feature_uri)
            schema = FeatureSchema()
            return schema.dump(feature), HTTPStatus.OK
        except NotFoundException:
            LOGGER.error(f'NotFoundException: feature_uri {feature_uri} does not exist')
            return {'message': f'feature_uri {feature_uri} does not exist'}, HTTPStatus.NOT_FOUND
        except Exception as e:
            LOGGER.error(f'Internal server error occurred when getting feature details: {e}')
            return {'message': f'Internal server error: {e}'}, HTTPStatus.INTERNAL_SERVER_ERROR


class FeatureLineageAPI(Resource):

    def __init__(self) -> None:
        self.client = get_proxy_client()
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('direction', type=str, required=False, default="both")
        self.parser.add_argument('depth', type=int, required=False, default=1)

    @swag_from('swagger_doc/feature/lineage_get.yml')
    def get(self, id: str) -> Iterable[Union[Mapping, int, None]]:
        args = self.parser.parse_args()
        direction = args.get('direction')
        depth = args.get('depth')
        try:
            lineage = self.client.get_lineage(id=id,
                                              resource_type=ResourceType.Feature,
                                              direction=direction,
                                              depth=depth)
            schema = LineageSchema()
            return schema.dump(lineage), HTTPStatus.OK
        except NotFoundException:
            LOGGER.error(f'NotFoundException: feature_uri {id} lineage does not exist')
            return {'message': f'feature_uri {id} lineage does not exist'}, HTTPStatus.NOT_FOUND
        except Exception as e:
            LOGGER.error(f'Internal server error occurred when getting feature lineage: {e}')
            return {'message': f'Exception raised when getting lineage: {e}'}, HTTPStatus.INTERNAL_SERVER_ERROR


class FeatureStatsAPI(Resource):

    # TODO integrate stats source for FE
    def __init__(self) -> None:
        self.client = get_proxy_client()

    @swag_from('swagger_doc/feature/detail_get.yml')
    def get(self, feature_uri: str) -> Iterable[Union[Mapping, int, None]]:
        pass


class FeatureGenerationCodeAPI(Resource):

    def __init__(self) -> None:
        self.client = get_proxy_client()

    @swag_from('swagger_doc/feature/detail_get.yml')
    def get(self, feature_uri: str) -> Iterable[Union[Mapping, int, None]]:
        try:
            generation_code = self.client.get_resource_generation_code(uri=feature_uri,
                                                                       resource_type=ResourceType.Feature)
            schema = GenerationCodeSchema()
            return schema.dump(generation_code), HTTPStatus.OK

        except NotFoundException:
            LOGGER.error(f'NotFoundException: feature_uri {feature_uri} does not exist')
            return {'message': f'feature_uri {feature_uri} does not exist'}, HTTPStatus.NOT_FOUND

        except Exception as e:
            LOGGER.info(f'Internal server error when getting feature generation code: {e}')
            return {'message': 'Internal Server Error'}, HTTPStatus.INTERNAL_SERVER_ERROR


class FeatureSampleAPI(Resource):

    # TODO use DataSample common model
    def __init__(self) -> None:
        self.client = get_proxy_client()

    @swag_from('swagger_doc/feature/detail_get.yml')
    def get(self, feature_uri: str) -> Iterable[Union[Mapping, int, None]]:
        pass


class FeatureOwnerAPI(Resource):

    def __init__(self) -> None:
        self.client = get_proxy_client()

    @swag_from('swagger_doc/feature/owner_put.yml')
    def put(self, feature_uri: str, owner: str) -> Iterable[Union[Mapping, int, None]]:
        try:
            self.client.add_resource_owner(uri=feature_uri, resource_type=ResourceType.Feature, owner=owner)
            return {'message': f'The owner {owner} for feature_uri {feature_uri} '
                               'was added successfully'}, HTTPStatus.OK
        except Exception as e:
            LOGGER.error(f'Internal server error occurred when adding owner: {e}')
            return {'message': f'The owner {owner} for feature_uri {feature_uri} was '
                               f'not added successfully. Message: {e}'}, HTTPStatus.INTERNAL_SERVER_ERROR

    @swag_from('swagger_doc/feature/owner_delete.yml')
    def delete(self, feature_uri: str, owner: str) -> Iterable[Union[Mapping, int, None]]:
        try:
            self.client.delete_resource_owner(uri=feature_uri, resource_type=ResourceType.Feature, owner=owner)
            return {'message': f'The owner {owner} for feature_uri {feature_uri} '
                               'was deleted successfully'}, HTTPStatus.OK
        except Exception as e:
            LOGGER.error(f'Internal server error occurred when deleting owner: {e}')
            return {'message': f'The owner {owner} for feature_uri {feature_uri} '
                               f'was not deleted successfully. Message: {e}'}, HTTPStatus.INTERNAL_SERVER_ERROR


class FeatureDescriptionAPI(Resource):

    def __init__(self) -> None:
        self.client = get_proxy_client()

    @swag_from('swagger_doc/common/description_get.yml')
    def get(self, id: str) -> Iterable[Any]:
        """
        Returns description from proxy
        """
        try:
            description = self.client.get_resource_description(resource_type=ResourceType.Feature,
                                                               uri=id).description
            return {'description': description}, HTTPStatus.OK

        except NotFoundException:
            LOGGER.error(f'NotFoundException: feature_uri {id} does not exist')
            return {'message': f'feature_uri {id} does not exist'}, HTTPStatus.NOT_FOUND

        except Exception as e:
            LOGGER.error(f'Internal server error occurred when getting description: {e}')
            return {'message': f'Internal server error: {e}'}, HTTPStatus.INTERNAL_SERVER_ERROR

    @swag_from('swagger_doc/common/description_put.yml')
    def put(self, id: str) -> Iterable[Any]:
        """
        Updates feature description (passed as a request body)
        """
        try:
            description = json.loads(request.data).get('description')
            self.client.put_resource_description(resource_type=ResourceType.Feature,
                                                 uri=id, description=description)
            return None, HTTPStatus.OK

        except NotFoundException:
            LOGGER.error(f'NotFoundException: feature_uri {id} does not exist')
            return {'message': 'feature_uri {} does not exist'.format(id)}, HTTPStatus.NOT_FOUND

        except Exception as e:
            LOGGER.error(f'Internal server error occurred when adding description: {e}')
            return {'message': f'Internal server error: {e}'}, HTTPStatus.INTERNAL_SERVER_ERROR


class FeatureTagAPI(Resource):
    """
    Only for user tags not owner tags
    """

    def __init__(self) -> None:
        self.client = get_proxy_client()
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('tag_type', type=str, required=False, default='default')

        self._tag_common = TagCommon(client=self.client)

    @swag_from('swagger_doc/tag/tag_put.yml')
    def put(self, id: str, tag: str) -> Iterable[Union[Mapping, int, None]]:
        args = self.parser.parse_args()
        # use tag_type to distinguish between tag and badge
        tag_type = args.get('tag_type', 'default')

        if tag_type == 'owner':
            LOGGER.error(f'Invalid attempt to add owner tag')
            return \
                {'message': f'The tag {tag} for id {id} with type {tag_type} '
                            f'and resource_type {ResourceType.Feature.name} is '
                            'not added successfully because owner tags are not editable'}, \
                HTTPStatus.CONFLICT

        return self._tag_common.put(id=id,
                                    resource_type=ResourceType.Feature,
                                    tag=tag,
                                    tag_type=tag_type)

    @swag_from('swagger_doc/tag/tag_delete.yml')
    def delete(self, id: str, tag: str) -> Iterable[Union[Mapping, int, None]]:
        args = self.parser.parse_args()
        tag_type = args.get('tag_type', 'default')
        if tag_type == 'owner':
            LOGGER.error(f'Invalid attempt to delete owner tag')
            return \
                {'message': f'The tag {tag} for id {id} with type {tag_type} '
                            f'and resource_type {ResourceType.Feature.name} is '
                            'not deleted because owner tags are not editable'}, \
                HTTPStatus.CONFLICT

        return self._tag_common.delete(id=id,
                                       resource_type=ResourceType.Feature,
                                       tag=tag,
                                       tag_type=tag_type)


class FeatureBadgeAPI(Resource):

    def __init__(self) -> None:
        self.client = get_proxy_client()
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('category', type=str, required=True)

        self._badge_common = BadgeCommon(client=self.client)

    @swag_from('swagger_doc/badge/badge_put.yml')
    def put(self, id: str, badge: str) -> Iterable[Union[Mapping, int, None]]:
        args = self.parser.parse_args()
        category = args.get('category', '')

        return self._badge_common.put(id=id,
                                      resource_type=ResourceType.Feature,
                                      badge_name=badge,
                                      category=category)

    @swag_from('swagger_doc/badge/badge_delete.yml')
    def delete(self, id: str, badge: str) -> Iterable[Union[Mapping, int, None]]:
        args = self.parser.parse_args()
        category = args.get('category', '')

        return self._badge_common.delete(id=id,
                                         resource_type=ResourceType.Feature,
                                         badge_name=badge,
                                         category=category)
