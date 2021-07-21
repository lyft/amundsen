# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from http import HTTPStatus

from metadata_service.exception import NotFoundException
from tests.unit.api.feature.feature_test_case import FeatureTestCase

FEATURE_URI = 'test_feature_group/test_feature_name/1.2.3'

BASE = {
    'key': 'test_feature_group/test_feature_name/1.2.3',
    'name': 'test_feature_name',
    'version': '1.2.3',
    'data_type': 'bigint',
    'tags': [{'tag_type': 'default', 'tag_name': 'test'}],
    'badges': [{'badge_name': 'pii', 'category': 'data'}],
    'owners': [{'email': 'mmcgonagall@hogwarts.com', 'first_name': None, 'last_name': None}],
    'watermarks': [],
    'last_updated_timestamp': 1570581861,
}

QUERY_RESPONSE = {
    **BASE,  # type: ignore
    'description': 'test feature description',
    'programmatic_descriptions': []
}

API_RESPONSE = {
    **BASE,  # type: ignore
    'description': 'test feature description',
    'programmatic_descriptions': []
}


class TestFeatureDetailAPI(FeatureTestCase):
    def test_get_feature_details(self) -> None:
        self.mock_proxy.get_feature.return_value = QUERY_RESPONSE

        response = self.app.test_client().get(f'/feature/{FEATURE_URI}')

        self.assertEqual(response.json, API_RESPONSE)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.mock_proxy.get_feature.assert_called_with(feature_uri=FEATURE_URI)

    def test_fail_to_get_details_when_feature_not_found(self) -> None:
        self.mock_proxy.get_feature.side_effect = NotFoundException(message='feature not found')

        response = self.app.test_client().get(f'/feature/{FEATURE_URI}')

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
