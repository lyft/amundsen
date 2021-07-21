# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import logging
import unittest
from typing import Any, Dict

from mock import MagicMock, patch
from pyhocon import ConfigFactory

from databuilder.extractor.athena_metadata_extractor import AthenaMetadataExtractor
from databuilder.extractor.sql_alchemy_extractor import SQLAlchemyExtractor
from databuilder.models.table_metadata import ColumnMetadata, TableMetadata


class TestAthenaMetadataExtractor(unittest.TestCase):
    def setUp(self) -> None:
        logging.basicConfig(level=logging.INFO)

        config_dict = {
            f'extractor.sqlalchemy.{SQLAlchemyExtractor.CONN_STRING}': 'TEST_CONNECTION',
            f'extractor.athena_metadata.{AthenaMetadataExtractor.CATALOG_KEY}': 'MY_CATALOG'
        }
        self.conf = ConfigFactory.from_dict(config_dict)

    def test_extraction_with_empty_query_result(self) -> None:
        """
        Test Extraction with empty result from query
        """
        with patch.object(SQLAlchemyExtractor, '_get_connection'):
            extractor = AthenaMetadataExtractor()
            extractor.init(self.conf)

            results = extractor.extract()
            self.assertEqual(results, None)

    def test_extraction_with_single_result(self) -> None:
        with patch.object(SQLAlchemyExtractor, '_get_connection') as mock_connection:
            connection = MagicMock()
            mock_connection.return_value = connection
            sql_execute = MagicMock()
            connection.execute = sql_execute
            table = {
                'schema': 'test_schema',
                'name': 'test_table',
                'description': '',
                'cluster': self.conf[f'extractor.athena_metadata.{AthenaMetadataExtractor.CATALOG_KEY}'],
            }

            sql_execute.return_value = [
                self._union({
                    'col_name': 'col_id1',
                    'col_type': 'bigint',
                    'col_description': 'description of id1',
                    'col_sort_order': 0,
                    'extras': None
                }, table),
                self._union({
                    'col_name': 'col_id2',
                    'col_type': 'bigint',
                    'col_description': 'description of id2',
                    'col_sort_order': 1,
                    'extras': None
                }, table),
                self._union({
                    'col_name': 'is_active',
                    'col_type': 'boolean',
                    'col_description': None,
                    'col_sort_order': 2,
                    'extras': None
                }, table),
                self._union({
                    'col_name': 'source',
                    'col_type': 'varchar',
                    'col_description': 'description of source',
                    'col_sort_order': 3,
                    'extras': None
                }, table),
                self._union({
                    'col_name': 'etl_created_at',
                    'col_type': 'timestamp',
                    'col_description': None,
                    'col_sort_order': 4,
                    'extras': 'partition key'
                }, table),
                self._union({
                    'col_name': 'ds',
                    'col_type': 'varchar',
                    'col_description': None,
                    'col_sort_order': 5,
                    'extras': None
                }, table)
            ]

            extractor = AthenaMetadataExtractor()
            extractor.init(self.conf)
            actual = extractor.extract()
            expected = TableMetadata('athena',
                                     self.conf[f'extractor.athena_metadata.{AthenaMetadataExtractor.CATALOG_KEY}'],
                                     'test_schema',
                                     'test_table', '',
                                     [ColumnMetadata('col_id1', 'description of id1', 'bigint', 0),
                                      ColumnMetadata('col_id2', 'description of id2', 'bigint', 1),
                                      ColumnMetadata('is_active', None, 'boolean', 2),
                                      ColumnMetadata('source', 'description of source', 'varchar', 3),
                                      ColumnMetadata('etl_created_at', 'partition key', 'timestamp', 4),
                                      ColumnMetadata('ds', None, 'varchar', 5)])
            self.assertEqual(expected.__repr__(), actual.__repr__())
            self.assertIsNone(extractor.extract())

    def test_extraction_with_multiple_result(self) -> None:
        with patch.object(SQLAlchemyExtractor, '_get_connection') as mock_connection:
            connection = MagicMock()
            mock_connection.return_value = connection
            sql_execute = MagicMock()
            connection.execute = sql_execute
            table = {'schema': 'test_schema1',
                     'name': 'test_table1',
                     'description': '',
                     'cluster': self.conf[f'extractor.athena_metadata.{AthenaMetadataExtractor.CATALOG_KEY}'],
                     }

            table1 = {'schema': 'test_schema1',
                      'name': 'test_table2',
                      'description': '',
                      'cluster': self.conf[f'extractor.athena_metadata.{AthenaMetadataExtractor.CATALOG_KEY}'],
                      }

            table2 = {'schema': 'test_schema2',
                      'name': 'test_table3',
                      'description': '',
                      'cluster': self.conf[f'extractor.athena_metadata.{AthenaMetadataExtractor.CATALOG_KEY}'],
                      }

            sql_execute.return_value = [
                self._union(
                    {'col_name': 'col_id1',
                     'col_type': 'bigint',
                     'col_description': 'description of col_id1',
                     'col_sort_order': 0,
                     'extras': None}, table),
                self._union(
                    {'col_name': 'col_id2',
                     'col_type': 'bigint',
                     'col_description': 'description of col_id2',
                     'col_sort_order': 1,
                     'extras': None}, table),
                self._union(
                    {'col_name': 'is_active',
                     'col_type': 'boolean',
                     'col_description': None,
                     'col_sort_order': 2,
                     'extras': None}, table),
                self._union(
                    {'col_name': 'source',
                     'col_type': 'varchar',
                     'col_description': 'description of source',
                     'col_sort_order': 3,
                     'extras': None}, table),
                self._union(
                    {'col_name': 'etl_created_at',
                     'col_type': 'timestamp',
                     'col_description': '',
                     'col_sort_order': 4,
                     'extras': 'partition key'}, table),
                self._union(
                    {'col_name': 'ds',
                     'col_type': 'varchar',
                     'col_description': None,
                     'col_sort_order': 5,
                     'extras': None}, table),
                self._union(
                    {'col_name': 'col_name',
                     'col_type': 'varchar',
                     'col_description': 'description of col_name',
                     'col_sort_order': 0,
                     'extras': None}, table1),
                self._union(
                    {'col_name': 'col_name2',
                     'col_type': 'varchar',
                     'col_description': 'description of col_name2',
                     'col_sort_order': 1,
                     'extras': None}, table1),
                self._union(
                    {'col_name': 'col_id3',
                     'col_type': 'varchar',
                     'col_description': 'description of col_id3',
                     'col_sort_order': 0,
                     'extras': None}, table2),
                self._union(
                    {'col_name': 'col_name3',
                     'col_type': 'varchar',
                     'col_description': 'description of col_name3',
                     'col_sort_order': 1,
                     'extras': None}, table2)
            ]

            extractor = AthenaMetadataExtractor()
            extractor.init(self.conf)

            expected = TableMetadata('athena',
                                     self.conf[f'extractor.athena_metadata.{AthenaMetadataExtractor.CATALOG_KEY}'],
                                     'test_schema1', 'test_table1', '',
                                     [ColumnMetadata('col_id1', 'description of col_id1', 'bigint', 0),
                                      ColumnMetadata('col_id2', 'description of col_id2', 'bigint', 1),
                                      ColumnMetadata('is_active', None, 'boolean', 2),
                                      ColumnMetadata('source', 'description of source', 'varchar', 3),
                                      ColumnMetadata('etl_created_at', 'partition key', 'timestamp', 4),
                                      ColumnMetadata('ds', None, 'varchar', 5)])
            self.assertEqual(expected.__repr__(), extractor.extract().__repr__())

            expected = TableMetadata('athena',
                                     self.conf[f'extractor.athena_metadata.{AthenaMetadataExtractor.CATALOG_KEY}'],
                                     'test_schema1', 'test_table2', '',
                                     [ColumnMetadata('col_name', 'description of col_name', 'varchar', 0),
                                      ColumnMetadata('col_name2', 'description of col_name2', 'varchar', 1)])
            self.assertEqual(expected.__repr__(), extractor.extract().__repr__())

            expected = TableMetadata('athena',
                                     self.conf[f'extractor.athena_metadata.{AthenaMetadataExtractor.CATALOG_KEY}'],
                                     'test_schema2', 'test_table3', '',
                                     [ColumnMetadata('col_id3', 'description of col_id3', 'varchar', 0),
                                      ColumnMetadata('col_name3', 'description of col_name3',
                                                     'varchar', 1)])
            self.assertEqual(expected.__repr__(), extractor.extract().__repr__())

            self.assertIsNone(extractor.extract())
            self.assertIsNone(extractor.extract())

    def _union(self,
               target: Dict[Any, Any],
               extra: Dict[Any, Any]) -> Dict[Any, Any]:
        target.update(extra)
        return target


class TestAthenaMetadataExtractorWithWhereClause(unittest.TestCase):
    def setUp(self) -> None:
        logging.basicConfig(level=logging.INFO)
        self.where_clause_suffix = """
        where table_schema in ('public') and table_name = 'movies'
        """
        config_dict = {
            AthenaMetadataExtractor.WHERE_CLAUSE_SUFFIX_KEY: self.where_clause_suffix,
            f'extractor.sqlalchemy.{SQLAlchemyExtractor.CONN_STRING}': 'TEST_CONNECTION'
        }
        self.conf = ConfigFactory.from_dict(config_dict)

    def test_sql_statement(self) -> None:
        """
        Test Extraction with empty result from query
        """
        with patch.object(SQLAlchemyExtractor, '_get_connection'):
            extractor = AthenaMetadataExtractor()
            extractor.init(self.conf)
            self.assertTrue(self.where_clause_suffix in extractor.sql_stmt)


if __name__ == '__main__':
    unittest.main()
