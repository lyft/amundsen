# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import json
import unittest
from http import HTTPStatus
from unittest.mock import patch

from tests.unit.test_basics import BasicTestCase


class RedshiftCommentEditDisableTest(BasicTestCase):

    def test_table_comment_edit(self) -> None:
        with patch('metadata_service.api.table.get_proxy_client'):
            table_uri = 'hive://gold.test_schema/test_table'
            url = '/table/' + table_uri + '/description'
            response = self.app.test_client().put(url, data=json.dumps({'description': 'test table'}))
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_column_comment_edit(self) -> None:
        with patch('metadata_service.api.column.get_proxy_client'):
            table_uri = 'hive://gold.test_schema/test_table'
            column_name = 'foo'
            url = '/table/' + table_uri + '/column/' + column_name + '/description'
            response = self.app.test_client().put(url, data=json.dumps({'description': 'test column'}))
            self.assertEqual(response.status_code, HTTPStatus.OK)


if __name__ == '__main__':
    unittest.main()
