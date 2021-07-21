# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from http import HTTPStatus

from amundsen_common.entity.resource_type import ResourceType

from tests.unit.api.feature.feature_test_case import FeatureTestCase

FEATURE_URI = 'test_feature_uri'
OWNER = 'harry'


class TestFeatureOwnerAPI(FeatureTestCase):

    def test_should_update_feature_owner(self) -> None:
        response = self.app.test_client().put(f'/feature/{FEATURE_URI}/owner/{OWNER}')

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.mock_proxy.add_resource_owner.assert_called_with(uri=FEATURE_URI,
                                                              resource_type=ResourceType.Feature,
                                                              owner=OWNER)

    def test_should_fail_when_owner_update_fails(self) -> None:
        self.mock_proxy.add_resource_owner.side_effect = RuntimeError()

        response = self.app.test_client().put(f'/feature/{FEATURE_URI}/owner/{OWNER}')

        self.assertEqual(response.status_code, HTTPStatus.INTERNAL_SERVER_ERROR)

    def test_should_delete_feature_owner(self) -> None:
        response = self.app.test_client().delete(f'/feature/{FEATURE_URI}/owner/{OWNER}')

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.mock_proxy.delete_resource_owner.assert_called_with(uri=FEATURE_URI,
                                                                 resource_type=ResourceType.Feature,
                                                                 owner=OWNER)

    def test_should_fail_when_delete_owner_fails(self) -> None:
        self.mock_proxy.delete_resource_owner.side_effect = RuntimeError()

        response = self.app.test_client().delete(f'/feature/{FEATURE_URI}/owner/{OWNER}')

        self.assertEqual(response.status_code, HTTPStatus.INTERNAL_SERVER_ERROR)
