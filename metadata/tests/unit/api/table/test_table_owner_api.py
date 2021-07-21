# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from http import HTTPStatus

from tests.unit.api.table.table_test_case import TableTestCase

TABLE_URI = 'wizards'
OWNER = 'harry'


class TestTableOwnerAPI(TableTestCase):

    def test_should_update_table_owner(self) -> None:
        response = self.app.test_client().put(f'/table/{TABLE_URI}/owner/{OWNER}')

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.mock_proxy.add_owner.assert_called_with(table_uri=TABLE_URI, owner=OWNER)

    def test_should_fail_when_owner_update_fails(self) -> None:
        self.mock_proxy.add_owner.side_effect = RuntimeError()

        response = self.app.test_client().put(f'/table/{TABLE_URI}/owner/{OWNER}')

        self.assertEqual(response.status_code, HTTPStatus.INTERNAL_SERVER_ERROR)

    def test_should_delete_table_owner(self) -> None:
        response = self.app.test_client().delete(f'/table/{TABLE_URI}/owner/{OWNER}')

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.mock_proxy.delete_owner.assert_called_with(table_uri=TABLE_URI, owner=OWNER)

    def test_should_fail_when_delete_owner_fails(self) -> None:
        self.mock_proxy.delete_owner.side_effect = RuntimeError()

        response = self.app.test_client().delete(f'/table/{TABLE_URI}/owner/{OWNER}')

        self.assertEqual(response.status_code, HTTPStatus.INTERNAL_SERVER_ERROR)
