# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import logging
import unittest
from typing import (
    Any, Dict, List,
)
from unittest.mock import MagicMock, patch

from pyhocon import ConfigFactory

from databuilder.extractor.dremio_metadata_extractor import DremioMetadataExtractor
from databuilder.models.table_metadata import ColumnMetadata, TableMetadata


class TestDremioMetadataExtractor(unittest.TestCase):

    def setUp(self) -> None:
        logging.basicConfig(level=logging.INFO)

        config_dict: Dict[str, str] = {}

        self.conf = ConfigFactory.from_dict(config_dict)

    @patch('databuilder.extractor.dremio_metadata_extractor.connect')
    def test_extraction_with_empty_query_result(self, mock_connect: MagicMock) -> None:
        """
        Test Extraction with empty result from query
        """
        mock_connection = MagicMock()
        mock_connect.return_value = mock_connection

        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor

        extractor = DremioMetadataExtractor()
        extractor.init(self.conf)

        results = extractor.extract()
        self.assertEqual(results, None)

    @patch('databuilder.extractor.dremio_metadata_extractor.connect')
    def test_extraction_with_single_result(self, mock_connect: MagicMock) -> None:
        """
        Test Extraction with single table result from query
        """
        mock_connection = MagicMock()
        mock_connect.return_value = mock_connection

        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor

        mock_execute = MagicMock()
        mock_cursor.execute = mock_execute

        mock_cursor.description = [
            ['col_name'],
            ['col_description'],
            ['col_type'],
            ['col_sort_order'],
            ['database'],
            ['cluster'],
            ['schema'],
            ['name'],
            ['description'],
            ['is_view']
        ]

        # Pass flake8 Unsupported operand types for + error
        table: List[Any] = [
            'DREMIO',
            'Production',
            'test_schema',
            'test_table',
            'a table for testing',
            'false'
        ]

        # Pass flake8 Unsupported operand types for + error
        expected_input: List[List[Any]] = [
            ['col_id1', 'description of id1', 'number', 0] + table,
            ['col_id2', 'description of id2', 'number', 1] + table,
            ['is_active', None, 'boolean', 2] + table,
            ['source', 'description of source', 'varchar', 3] + table,
            ['etl_created_at', 'description of etl_created_at', 'timestamp_ltz', 4] + table,
            ['ds', None, 'varchar', 5] + table
        ]

        mock_cursor.execute.return_value = expected_input

        extractor = DremioMetadataExtractor()
        extractor.init(self.conf)

        actual = extractor.extract()
        expected = TableMetadata('DREMIO', 'Production', 'test_schema', 'test_table', 'a table for testing',
                                 [ColumnMetadata('col_id1', 'description of id1', 'number', 0),
                                  ColumnMetadata('col_id2', 'description of id2', 'number', 1),
                                  ColumnMetadata('is_active', None, 'boolean', 2),
                                  ColumnMetadata('source', 'description of source', 'varchar', 3),
                                  ColumnMetadata('etl_created_at', 'description of etl_created_at',
                                                 'timestamp_ltz', 4),
                                  ColumnMetadata('ds', None, 'varchar', 5)])

        self.assertEqual(expected.__repr__(), actual.__repr__())
        self.assertIsNone(extractor.extract())


if __name__ == '__main__':
    unittest.main()
