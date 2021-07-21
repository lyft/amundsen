# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from http import HTTPStatus

from amundsen_common.entity.resource_type import ResourceType

from metadata_service.exception import NotFoundException
from tests.unit.api.feature.feature_test_case import FeatureTestCase

FEATURE_URI = 'test_feature_uri'
TAG = 'underage_wizards'


class TestFeatureTagAPI(FeatureTestCase):

    def test_should_update_tag(self) -> None:
        response = self.app.test_client().put(f'/feature/{FEATURE_URI}/tag/{TAG}')

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.mock_proxy.add_tag.assert_called_with(id=FEATURE_URI,
                                                   tag=TAG,
                                                   tag_type='default',
                                                   resource_type=ResourceType.Feature)

    def test_should_fail_to_update_tag_when_feature_not_found(self) -> None:
        self.mock_proxy.add_tag.side_effect = NotFoundException(message='cannot find feature')

        response = self.app.test_client().put(f'/feature/{FEATURE_URI}/tag/{TAG}')

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_should_delete_tag(self) -> None:
        response = self.app.test_client().delete(f'/feature/{FEATURE_URI}/tag/{TAG}')

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.mock_proxy.delete_tag.assert_called_with(id=FEATURE_URI,
                                                      tag=TAG,
                                                      tag_type='default',
                                                      resource_type=ResourceType.Feature)

    def test_should_fail_to_delete_tag_when_feature_not_found(self) -> None:
        self.mock_proxy.delete_tag.side_effect = NotFoundException(message='cannot find feature')

        response = self.app.test_client().delete(f'/feature/{FEATURE_URI}/tag/{TAG}')

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
