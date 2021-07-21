# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import base64
import json
import logging
import unittest

from mock import MagicMock, patch
from pyhocon import ConfigFactory

from databuilder.extractor.presto_view_metadata_extractor import PrestoViewMetadataExtractor
from databuilder.extractor.sql_alchemy_extractor import SQLAlchemyExtractor
from databuilder.models.table_metadata import ColumnMetadata, TableMetadata


class TestPrestoViewMetadataExtractor(unittest.TestCase):
    def setUp(self) -> None:
        logging.basicConfig(level=logging.INFO)

        config_dict = {
            f'extractor.sqlalchemy.{SQLAlchemyExtractor.CONN_STRING}': 'TEST_CONNECTION'
        }
        self.conf = ConfigFactory.from_dict(config_dict)

    def test_extraction_with_empty_result(self) -> None:
        """
        Test Extraction with empty result from query
        """
        with patch.object(SQLAlchemyExtractor, '_get_connection'):
            extractor = PrestoViewMetadataExtractor()
            extractor.init(self.conf)

            results = extractor.extract()
            self.assertEqual(results, None)

    def test_extraction_with_multiple_views(self) -> None:
        with patch.object(SQLAlchemyExtractor, '_get_connection') as mock_connection:
            connection = MagicMock()
            mock_connection.return_value = connection
            sql_execute = MagicMock()
            connection.execute = sql_execute

            columns1 = {'columns': [{'name': 'xyz', 'type': 'varchar'},
                                    {'name': 'xyy', 'type': 'double'},
                                    {'name': 'aaa', 'type': 'int'},
                                    {'name': 'ab', 'type': 'varchar'}]}

            columns2 = {'columns': [{'name': 'xyy', 'type': 'varchar'},
                                    {'name': 'ab', 'type': 'double'},
                                    {'name': 'aaa', 'type': 'int'},
                                    {'name': 'xyz', 'type': 'varchar'}]}

            sql_execute.return_value = [
                {'tbl_id': 2,
                 'schema': 'test_schema2',
                 'name': 'test_view2',
                 'tbl_type': 'virtual_view',
                 'view_original_text': base64.b64encode(json.dumps(columns2).encode()).decode("utf-8")},
                {'tbl_id': 1,
                 'schema': 'test_schema1',
                 'name': 'test_view1',
                 'tbl_type': 'virtual_view',
                 'view_original_text': base64.b64encode(json.dumps(columns1).encode()).decode("utf-8")},
            ]

            extractor = PrestoViewMetadataExtractor()
            extractor.init(self.conf)
            actual_first_view = extractor.extract()
            expected_first_view = TableMetadata('presto', 'gold', 'test_schema2', 'test_view2', None,
                                                [ColumnMetadata(u'xyy', None, u'varchar', 0),
                                                 ColumnMetadata(u'ab', None, u'double', 1),
                                                 ColumnMetadata(u'aaa', None, u'int', 2),
                                                 ColumnMetadata(u'xyz', None, u'varchar', 3)],
                                                True)
            self.assertEqual(expected_first_view.__repr__(), actual_first_view.__repr__())

            actual_second_view = extractor.extract()
            expected_second_view = TableMetadata('presto', 'gold', 'test_schema1', 'test_view1', None,
                                                 [ColumnMetadata(u'xyz', None, u'varchar', 0),
                                                  ColumnMetadata(u'xyy', None, u'double', 1),
                                                  ColumnMetadata(u'aaa', None, u'int', 2),
                                                  ColumnMetadata(u'ab', None, u'varchar', 3)],
                                                 True)
            self.assertEqual(expected_second_view.__repr__(), actual_second_view.__repr__())

            self.assertIsNone(extractor.extract())


if __name__ == '__main__':
    unittest.main()
