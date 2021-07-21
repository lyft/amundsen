# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from http import HTTPStatus
from unittest.mock import Mock, patch

from metadata_service.exception import NotFoundException
from tests.unit.test_basics import BasicTestCase

DESCRIPTION = 'This is the name of the spell.'
COLUMN_NAME = 'spell'
TABLE_NAME = 'magic'


class TestColumnDescriptionAPI(BasicTestCase):
    def setUp(self) -> None:
        super().setUp()

        self.mock_client = patch('metadata_service.api.column.get_proxy_client')
        self.mock_proxy = self.mock_client.start().return_value = Mock()

    def tearDown(self) -> None:
        super().tearDown()

        self.mock_client.stop()

    def test_should_update_column_description(self) -> None:

        response = self.app.test_client().put(f'/table/{TABLE_NAME}/column/{COLUMN_NAME}/description',
                                              json={"description": DESCRIPTION})

        self.assertEqual(response.json, None)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.mock_proxy.put_column_description.assert_called_with(table_uri=TABLE_NAME, column_name=COLUMN_NAME,
                                                                  description=DESCRIPTION)

    def test_should_fail_to_update_column_description_when_table_does_not_exist(self) -> None:
        self.mock_proxy.put_column_description.side_effect = NotFoundException(message="table does not exist")

        response = self.app.test_client().put(f'/table/{TABLE_NAME}/column/{COLUMN_NAME}/description',
                                              json={"description": DESCRIPTION})

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_should_get_column_description(self) -> None:
        self.mock_proxy.get_column_description.return_value = DESCRIPTION

        response = self.app.test_client().get(f'/table/{TABLE_NAME}/column/{COLUMN_NAME}/description')

        self.assertEqual(response.json, {'description': DESCRIPTION})
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.mock_proxy.get_column_description.assert_called_with(table_uri=TABLE_NAME, column_name=COLUMN_NAME)

    def test_should_fail_to_get_column_description_when_table_is_not_found(self) -> None:
        self.mock_proxy.get_column_description.side_effect = NotFoundException(message="table does not exist")

        response = self.app.test_client().get(f'/table/{TABLE_NAME}/column/{COLUMN_NAME}/description')

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_should_fail_to_get_column_description(self) -> None:
        self.mock_proxy.get_column_description.side_effect = RuntimeError

        response = self.app.test_client().get(f'/table/{TABLE_NAME}/column/{COLUMN_NAME}/description')

        self.assertEqual(response.status_code, HTTPStatus.INTERNAL_SERVER_ERROR)
