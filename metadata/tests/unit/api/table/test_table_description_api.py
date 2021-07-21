# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from http import HTTPStatus

from metadata_service.exception import NotFoundException
from tests.unit.api.table.table_test_case import TableTestCase

TABLE_URI = 'wizards'
DESCRIPTION = 'magical people'


class TestTableDescriptionAPI(TableTestCase):
    def test_should_get_table_description(self) -> None:
        self.mock_proxy.get_table_description.return_value = DESCRIPTION

        response = self.app.test_client().get(f'/table/{TABLE_URI}/description')

        self.assertEqual(response.json, {'description': DESCRIPTION})
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.mock_proxy.get_table_description.assert_called_with(table_uri=TABLE_URI)

    def test_should_fail_when_cannot_get_description(self) -> None:
        self.mock_proxy.get_table_description.side_effect = RuntimeError()

        response = self.app.test_client().get(f'/table/{TABLE_URI}/description')

        self.assertEqual(response.status_code, HTTPStatus.INTERNAL_SERVER_ERROR)

    def test_should_fail_when_cannot_find_table(self) -> None:
        self.mock_proxy.get_table_description.side_effect = NotFoundException(message='cannot find table')

        response = self.app.test_client().get(f'/table/{TABLE_URI}/description')

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_should_update_table_description(self) -> None:
        response = self.app.test_client().put(f'/table/{TABLE_URI}/description',
                                              json={'description': DESCRIPTION})

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.mock_proxy.put_table_description.assert_called_with(table_uri=TABLE_URI, description=DESCRIPTION)

    def test_should_fail_to_update_description_when_table_not_found(self) -> None:
        self.mock_proxy.put_table_description.side_effect = NotFoundException(message='cannot find table')

        response = self.app.test_client().put(f'/table/{TABLE_URI}/description', json={'description': DESCRIPTION})

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
