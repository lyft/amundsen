# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from http import HTTPStatus

from amundsen_common.entity.resource_type import ResourceType

from metadata_service.entity.description import Description
from metadata_service.exception import NotFoundException
from tests.unit.api.feature.feature_test_case import FeatureTestCase

FEATURE_URI = 'test_feature_uri'
DESCRIPTION = 'magical people'


class TestFeatureDescriptionAPI(FeatureTestCase):
    def test_should_get_feature_description(self) -> None:
        self.mock_proxy.get_resource_description.return_value = Description(description=DESCRIPTION)

        response = self.app.test_client().get(f'/feature/{FEATURE_URI}/description')

        self.assertEqual(response.json, {'description': DESCRIPTION})
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.mock_proxy.get_resource_description.assert_called_with(resource_type=ResourceType.Feature,
                                                                    uri=FEATURE_URI)

    def test_should_fail_when_cannot_get_description(self) -> None:
        self.mock_proxy.get_resource_description.side_effect = RuntimeError()

        response = self.app.test_client().get(f'/feature/{FEATURE_URI}/description')

        self.assertEqual(response.status_code, HTTPStatus.INTERNAL_SERVER_ERROR)

    def test_should_fail_when_cannot_find_feature(self) -> None:
        self.mock_proxy.get_resource_description.side_effect = NotFoundException(message='cannot find feature')

        response = self.app.test_client().get(f'/feature/{FEATURE_URI}/description')

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_should_update_feature_description(self) -> None:
        response = self.app.test_client().put(f'/feature/{FEATURE_URI}/description',
                                              json={'description': DESCRIPTION})

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.mock_proxy.put_resource_description.assert_called_with(resource_type=ResourceType.Feature,
                                                                    uri=FEATURE_URI, description=DESCRIPTION)

    def test_should_fail_to_update_description_when_feature_not_found(self) -> None:
        self.mock_proxy.put_resource_description.side_effect = NotFoundException(message='cannot find feature')

        response = self.app.test_client().put(f'/feature/{FEATURE_URI}/description', json={'description': DESCRIPTION})

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
