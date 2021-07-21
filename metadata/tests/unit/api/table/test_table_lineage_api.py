# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from http import HTTPStatus

from amundsen_common.entity.resource_type import ResourceType

from metadata_service.exception import NotFoundException
from tests.unit.api.table.table_test_case import TableTestCase

TABLE_URI = "db://cluster.schema/test_table_1"

API_RESPONSE = {
    "key": "db://cluster.schema/test_table_1",
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
    "downstream_entities": [
        {
            "level": 1,
            "badges": [],
            "source": "db",
            "usage": 567,
            "key": "db://cluster.schema/down_table_1"
        },
        {
            "level": 1,
            "badges": [],
            "source": "hive",
            "usage": 54,
            "key": "hive://cluster.schema/down_table_2"
        },
        {
            "level": 2,
            "badges": [],
            "source": "hive",
            "usage": 17,
            "key": "hive://cluster.schema/down_table_3"
        },
    ]
}

LINEAGE_RESPONSE = API_RESPONSE


class TestTableLineageAPI(TableTestCase):
    def setUp(self) -> None:
        super().setUp()

    def tearDown(self) -> None:
        super().tearDown()

    def test_should_return_response(self) -> None:
        self.mock_proxy.get_lineage.return_value = LINEAGE_RESPONSE
        response = self.app.test_client().get(f'/table/{TABLE_URI}/lineage')
        self.assertEqual(response.json, API_RESPONSE)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.mock_proxy.get_lineage.assert_called_with(id=TABLE_URI,
                                                       resource_type=ResourceType.Table,
                                                       depth=1,
                                                       direction="both")

    def test_should_fail_when_table_doesnt_exist(self) -> None:
        self.mock_proxy.get_lineage.side_effect = NotFoundException(message='table not found')

        response = self.app.test_client().get(f'/table/{TABLE_URI}/lineage')

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
