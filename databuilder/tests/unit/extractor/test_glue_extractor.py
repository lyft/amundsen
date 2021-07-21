# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import logging
import unittest

from mock import patch
from pyhocon import ConfigFactory

from databuilder.extractor.glue_extractor import GlueExtractor
from databuilder.models.table_metadata import ColumnMetadata, TableMetadata


# patch whole class to avoid actually calling for boto3.client during tests
@patch('databuilder.extractor.glue_extractor.boto3.client', lambda x: None)
class TestGlueExtractor(unittest.TestCase):
    def setUp(self) -> None:
        logging.basicConfig(level=logging.INFO)

        self.conf = ConfigFactory.from_dict({})

    def test_extraction_with_empty_query_result(self) -> None:
        """
        Test Extraction with empty result from query
        """
        with patch.object(GlueExtractor, '_search_tables'):
            extractor = GlueExtractor()
            extractor.init(self.conf)

            results = extractor.extract()
            self.assertEqual(results, None)

    def test_extraction_with_single_result(self) -> None:
        with patch.object(GlueExtractor, '_search_tables') as mock_search:
            mock_search.return_value = [
                {
                    'Name': 'test_table',
                    'DatabaseName': 'test_schema',
                    'Description': 'a table for testing',
                    'StorageDescriptor': {
                        'Columns': [
                            {
                                'Name': 'col_id1',
                                'Type': 'bigint',
                                'Comment': 'description of id1'
                            },
                            {
                                'Name': 'col_id2',
                                'Type': 'bigint',
                                'Comment': 'description of id2'
                            },
                            {
                                'Name': 'is_active',
                                'Type': 'boolean'
                            },
                            {
                                'Name': 'source',
                                'Type': 'varchar',
                                'Comment': 'description of source'
                            },
                            {
                                'Name': 'etl_created_at',
                                'Type': 'timestamp',
                                'Comment': 'description of etl_created_at'
                            },
                            {
                                'Name': 'ds',
                                'Type': 'varchar'
                            }
                        ]
                    },
                    'PartitionKeys': [
                        {
                            'Name': 'partition_key1',
                            'Type': 'string',
                            'Comment': 'description of partition_key1'
                        },
                    ],
                    'TableType': 'EXTERNAL_TABLE',
                }
            ]

            extractor = GlueExtractor()
            extractor.init(self.conf)
            actual = extractor.extract()
            expected = TableMetadata('glue', 'gold', 'test_schema', 'test_table', 'a table for testing',
                                     [ColumnMetadata('col_id1', 'description of id1', 'bigint', 0),
                                      ColumnMetadata('col_id2', 'description of id2', 'bigint', 1),
                                      ColumnMetadata('is_active', None, 'boolean', 2),
                                      ColumnMetadata('source', 'description of source', 'varchar', 3),
                                      ColumnMetadata('etl_created_at', 'description of etl_created_at', 'timestamp', 4),
                                      ColumnMetadata('ds', None, 'varchar', 5),
                                      ColumnMetadata('partition_key1', 'description of partition_key1', 'string', 6),
                                      ], False)
            self.assertEqual(expected.__repr__(), actual.__repr__())
            self.assertIsNone(extractor.extract())

    def test_extraction_with_multiple_result(self) -> None:
        with patch.object(GlueExtractor, '_search_tables') as mock_search:
            mock_search.return_value = [
                {
                    'Name': 'test_table1',
                    'DatabaseName': 'test_schema1',
                    'Description': 'test table 1',
                    'StorageDescriptor': {
                        'Columns': [
                            {
                                'Name': 'col_id1',
                                'Type': 'bigint',
                                'Comment': 'description of col_id1'
                            },
                            {
                                'Name': 'col_id2',
                                'Type': 'bigint',
                                'Comment': 'description of col_id2'
                            },
                            {
                                'Name': 'is_active',
                                'Type': 'boolean'
                            },
                            {
                                'Name': 'source',
                                'Type': 'varchar',
                                'Comment': 'description of source'
                            },
                            {
                                'Name': 'etl_created_at',
                                'Type': 'timestamp',
                                'Comment': 'description of etl_created_at'
                            },
                            {
                                'Name': 'ds',
                                'Type': 'varchar'
                            }
                        ]
                    },
                    'PartitionKeys': [
                        {
                            'Name': 'partition_key1',
                            'Type': 'string',
                            'Comment': 'description of partition_key1'
                        },
                    ],
                    'TableType': 'EXTERNAL_TABLE',
                },
                {
                    'Name': 'test_table2',
                    'DatabaseName': 'test_schema1',
                    'Description': 'test table 2',
                    'StorageDescriptor': {
                        'Columns': [
                            {
                                'Name': 'col_name',
                                'Type': 'varchar',
                                'Comment': 'description of col_name'
                            },
                            {
                                'Name': 'col_name2',
                                'Type': 'varchar',
                                'Comment': 'description of col_name2'
                            }
                        ]
                    },
                    'TableType': 'EXTERNAL_TABLE',
                },
                {
                    'Name': 'test_table3',
                    'DatabaseName': 'test_schema2',
                    'StorageDescriptor': {
                        'Columns': [
                            {
                                'Name': 'col_id3',
                                'Type': 'varchar',
                                'Comment': 'description of col_id3'
                            },
                            {
                                'Name': 'col_name3',
                                'Type': 'varchar',
                                'Comment': 'description of col_name3'
                            }
                        ]
                    },
                    'Parameters': {'comment': 'description of test table 3 from comment'},
                    'TableType': 'EXTERNAL_TABLE',
                },
                {
                    'Name': 'test_view1',
                    'DatabaseName': 'test_schema1',
                    'Description': 'test view 1',
                    'StorageDescriptor': {
                        'Columns': [
                            {
                                'Name': 'col_id3',
                                'Type': 'varchar',
                                'Comment': 'description of col_id3'
                            },
                            {
                                'Name': 'col_name3',
                                'Type': 'varchar',
                                'Comment': 'description of col_name3'
                            }
                        ]
                    },
                    'TableType': 'VIRTUAL_VIEW',
                },
            ]

            extractor = GlueExtractor()
            extractor.init(self.conf)

            expected = TableMetadata('glue', 'gold', 'test_schema1', 'test_table1', 'test table 1',
                                     [ColumnMetadata('col_id1', 'description of col_id1', 'bigint', 0),
                                      ColumnMetadata('col_id2', 'description of col_id2', 'bigint', 1),
                                      ColumnMetadata('is_active', None, 'boolean', 2),
                                      ColumnMetadata('source', 'description of source', 'varchar', 3),
                                      ColumnMetadata('etl_created_at', 'description of etl_created_at', 'timestamp', 4),
                                      ColumnMetadata('ds', None, 'varchar', 5),
                                      ColumnMetadata('partition_key1', 'description of partition_key1', 'string', 6),
                                      ], False)
            self.assertEqual(expected.__repr__(), extractor.extract().__repr__())

            expected = TableMetadata('glue', 'gold', 'test_schema1', 'test_table2', 'test table 2',
                                     [ColumnMetadata('col_name', 'description of col_name', 'varchar', 0),
                                      ColumnMetadata('col_name2', 'description of col_name2', 'varchar', 1)], False)
            self.assertEqual(expected.__repr__(), extractor.extract().__repr__())

            expected = TableMetadata('glue', 'gold', 'test_schema2', 'test_table3',
                                     'description of test table 3 from comment',
                                     [ColumnMetadata('col_id3', 'description of col_id3', 'varchar', 0),
                                      ColumnMetadata('col_name3', 'description of col_name3',
                                                     'varchar', 1)], False)
            self.assertEqual(expected.__repr__(), extractor.extract().__repr__())

            expected = TableMetadata('glue', 'gold', 'test_schema1', 'test_view1', 'test view 1',
                                     [ColumnMetadata('col_id3', 'description of col_id3', 'varchar', 0),
                                      ColumnMetadata('col_name3', 'description of col_name3',
                                                     'varchar', 1)], True)
            self.assertEqual(expected.__repr__(), extractor.extract().__repr__())

            self.assertIsNone(extractor.extract())
            self.assertIsNone(extractor.extract())


if __name__ == '__main__':
    unittest.main()
