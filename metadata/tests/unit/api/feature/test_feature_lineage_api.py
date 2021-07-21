# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from http import HTTPStatus

from amundsen_common.entity.resource_type import ResourceType

from metadata_service.exception import NotFoundException
from tests.unit.api.feature.feature_test_case import FeatureTestCase

FEATURE_URI = "test_feature_group_name/test_feature_name/1.2.0"

API_RESPONSE = {
    "key": "test_feature_group_name/test_feature_name/1.2.0",
    "direction": "both",
    "depth": 1,
    "upstream_entities": [
        {
            "level": 1,
            "badges": [],
            "source": "db",
            "usage": 257,
            "key": "db://cluster.schema/up_table_1"
        },
        {
            "level": 1,
            "badges": [],
            "source": "hive",
            "usage": 164,
            "key": "hive://cluster.schema/up_table_2"
        },
        {
            "level": 1,
            "badges": [],
            "source": "hive",
            "usage": 94,
            "key": "hive://cluster.schema/up_table_3"
        },
    ],
    "downstream_entities": []
}

LINEAGE_RESPONSE = API_RESPONSE


class TestFeatureLineageAPI(FeatureTestCase):
    def setUp(self) -> None:
        super().setUp()

    def tearDown(self) -> None:
        super().tearDown()

    def test_should_return_response(self) -> None:
        self.mock_proxy.get_lineage.return_value = LINEAGE_RESPONSE
        response = self.app.test_client().get(f'/feature/{FEATURE_URI}/lineage')

        self.mock_proxy.get_lineage.assert_called_with(id=FEATURE_URI,
                                                       resource_type=ResourceType.Feature,
                                                       depth=1,
                                                       direction="both")
        self.assertEqual(response.json, API_RESPONSE)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_should_fail_when_feature_doesnt_exist(self) -> None:
        self.mock_proxy.get_lineage.side_effect = NotFoundException(message='feature not found')

        response = self.app.test_client().get(f'/feature/{FEATURE_URI}/lineage')

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
