# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import logging
import unittest
from typing import Any, Dict

from mock import MagicMock, patch
from pyhocon import ConfigFactory

from databuilder.extractor.mssql_metadata_extractor import MSSQLMetadataExtractor
from databuilder.extractor.sql_alchemy_extractor import SQLAlchemyExtractor
from databuilder.models.table_metadata import ColumnMetadata, TableMetadata


class TestMSSQLMetadataExtractor(unittest.TestCase):
    def setUp(self) -> None:
        logging.basicConfig(level=logging.INFO)

        config_dict = {
            f'extractor.sqlalchemy.{SQLAlchemyExtractor.CONN_STRING}': 'TEST_CONNECTION',
            f'extractor.mssql_metadata.{MSSQLMetadataExtractor.CLUSTER_KEY}': 'MY_CLUSTER',
            f'extractor.mssql_metadata.{MSSQLMetadataExtractor.USE_CATALOG_AS_CLUSTER_NAME}': False,
            f'extractor.mssql_metadata.{MSSQLMetadataExtractor.DATABASE_KEY}': 'mssql',
            f'extractor.mssql_metadata.{MSSQLMetadataExtractor.WHERE_CLAUSE_SUFFIX_KEY}': ''
        }
        self.conf = ConfigFactory.from_dict(config_dict)

    def test_extraction_with_empty_query_result(self) -> None:
        """
        Test Extraction with empty result from query
        """
        with patch.object(SQLAlchemyExtractor, '_get_connection'):
            extractor = MSSQLMetadataExtractor()
            extractor.init(self.conf)

            results = extractor.extract()
            self.assertEqual(results, None)

    def test_extraction_with_single_result(self) -> None:
        with patch.object(SQLAlchemyExtractor, '_get_connection') as mock_connection:
            connection = MagicMock()
            mock_connection.return_value = connection
            sql_execute = MagicMock()
            connection.execute = sql_execute
            table = {'schema_name': 'test_schema',
                     'name': 'test_table',
                     'description': 'a table for testing',
                     'cluster':
                         self.conf[f'extractor.mssql_metadata.{MSSQLMetadataExtractor.CLUSTER_KEY}']
                     }

            sql_execute.return_value = [
                self._union(
                    {'col_name': 'col_id1',
                     'col_type': 'bigint',
                     'col_description': 'description of id1',
                     'col_sort_order': 0}, table),
                self._union(
                    {'col_name': 'col_id2',
                     'col_type': 'bigint',
                     'col_description': 'description of id2',
                     'col_sort_order': 1}, table),
                self._union(
                    {'col_name': 'is_active',
                     'col_type': 'boolean',
                     'col_description': None,
                     'col_sort_order': 2}, table),
                self._union(
                    {'col_name': 'source',
                     'col_type': 'varchar',
                     'col_description': 'description of source',
                     'col_sort_order': 3}, table),
                self._union(
                    {'col_name': 'etl_created_at',
                     'col_type': 'timestamp',
                     'col_description': 'description of etl_created_at',
                     'col_sort_order': 4}, table),
                self._union(
                    {'col_name': 'ds',
                     'col_type': 'varchar',
                     'col_description': None,
                     'col_sort_order': 5}, table)
            ]

            extractor = MSSQLMetadataExtractor()
            extractor.init(self.conf)
            actual = extractor.extract()
            expected = TableMetadata('mssql', 'MY_CLUSTER', 'test_schema', 'test_table', 'a table for testing',
                                     [ColumnMetadata('col_id1', 'description of id1', 'bigint', 0),
                                      ColumnMetadata('col_id2', 'description of id2', 'bigint', 1),
                                      ColumnMetadata('is_active', None, 'boolean', 2),
                                      ColumnMetadata('source', 'description of source', 'varchar', 3),
                                      ColumnMetadata('etl_created_at', 'description of etl_created_at', 'timestamp', 4),
                                      ColumnMetadata('ds', None, 'varchar', 5)], tags='test_schema')

            self.assertEqual(expected.__repr__(), actual.__repr__())
            self.assertIsNone(extractor.extract())

    def test_extraction_with_multiple_result(self) -> None:
        with patch.object(SQLAlchemyExtractor, '_get_connection') as mock_connection:
            connection = MagicMock()
            mock_connection.return_value = connection
            sql_execute = MagicMock()
            connection.execute = sql_execute
            table = {'schema_name': 'test_schema1',
                     'name': 'test_table1',
                     'description': 'test table 1',
                     'cluster':
                         self.conf[f'extractor.mssql_metadata.{MSSQLMetadataExtractor.CLUSTER_KEY}']
                     }

            table1 = {'schema_name': 'test_schema1',
                      'name': 'test_table2',
                      'description': 'test table 2',
                      'cluster':
                          self.conf[f'extractor.mssql_metadata.{MSSQLMetadataExtractor.CLUSTER_KEY}']
                      }

            table2 = {'schema_name': 'test_schema2',
                      'name': 'test_table3',
                      'description': 'test table 3',
                      'cluster':
                          self.conf[f'extractor.mssql_metadata.{MSSQLMetadataExtractor.CLUSTER_KEY}']
                      }

            sql_execute.return_value = [
                self._union(
                    {'col_name': 'col_id1',
                     'col_type': 'bigint',
                     'col_description': 'description of col_id1',
                     'col_sort_order': 0}, table),
                self._union(
                    {'col_name': 'col_id2',
                     'col_type': 'bigint',
                     'col_description': 'description of col_id2',
                     'col_sort_order': 1}, table),
                self._union(
                    {'col_name': 'is_active',
                     'col_type': 'boolean',
                     'col_description': None,
                     'col_sort_order': 2}, table),
                self._union(
                    {'col_name': 'source',
                     'col_type': 'varchar',
                     'col_description': 'description of source',
                     'col_sort_order': 3}, table),
                self._union(
                    {'col_name': 'etl_created_at',
                     'col_type': 'timestamp',
                     'col_description': 'description of etl_created_at',
                     'col_sort_order': 4}, table),
                self._union(
                    {'col_name': 'ds',
                     'col_type': 'varchar',
                     'col_description': None,
                     'col_sort_order': 5}, table),
                self._union(
                    {'col_name': 'col_name',
                     'col_type': 'varchar',
                     'col_description': 'description of col_name',
                     'col_sort_order': 0}, table1),
                self._union(
                    {'col_name': 'col_name2',
                     'col_type': 'varchar',
                     'col_description': 'description of col_name2',
                     'col_sort_order': 1}, table1),
                self._union(
                    {'col_name': 'col_id3',
                     'col_type': 'varchar',
                     'col_description': 'description of col_id3',
                     'col_sort_order': 0}, table2),
                self._union(
                    {'col_name': 'col_name3',
                     'col_type': 'varchar',
                     'col_description': 'description of col_name3',
                     'col_sort_order': 1}, table2)
            ]

            extractor = MSSQLMetadataExtractor()
            extractor.init(self.conf)

            expected = TableMetadata('mssql',
                                     self.conf[f'extractor.mssql_metadata.{MSSQLMetadataExtractor.CLUSTER_KEY}'],
                                     'test_schema1', 'test_table1', 'test table 1',
                                     [ColumnMetadata('col_id1', 'description of col_id1', 'bigint', 0),
                                      ColumnMetadata('col_id2', 'description of col_id2', 'bigint', 1),
                                      ColumnMetadata('is_active', None, 'boolean', 2),
                                      ColumnMetadata('source', 'description of source', 'varchar', 3),
                                      ColumnMetadata('etl_created_at', 'description of etl_created_at', 'timestamp', 4),
                                      ColumnMetadata('ds', None, 'varchar', 5)], tags='test_schema1')
            self.assertEqual(expected.__repr__(), extractor.extract().__repr__())

            expected = TableMetadata('mssql',
                                     self.conf[f'extractor.mssql_metadata.{MSSQLMetadataExtractor.CLUSTER_KEY}'],
                                     'test_schema1', 'test_table2', 'test table 2',
                                     [ColumnMetadata('col_name', 'description of col_name', 'varchar', 0),
                                      ColumnMetadata('col_name2', 'description of col_name2', 'varchar', 1)],
                                     tags='test_schema1')
            self.assertEqual(expected.__repr__(), extractor.extract().__repr__())

            expected = TableMetadata('mssql',
                                     self.conf[f'extractor.mssql_metadata.{MSSQLMetadataExtractor.CLUSTER_KEY}'],
                                     'test_schema2', 'test_table3', 'test table 3',
                                     [ColumnMetadata('col_id3', 'description of col_id3', 'varchar', 0),
                                      ColumnMetadata('col_name3', 'description of col_name3',
                                                     'varchar', 1)], tags='test_schema2')
            self.assertEqual(expected.__repr__(), extractor.extract().__repr__())

            self.assertIsNone(extractor.extract())
            self.assertIsNone(extractor.extract())

    def _union(self,
               target: Dict[Any, Any],
               extra: Dict[Any, Any]) -> Dict[Any, Any]:
        target.update(extra)
        return target


class TestMSSQLMetadataExtractorWithWhereClause(unittest.TestCase):
    def setUp(self) -> None:
        logging.basicConfig(level=logging.INFO)
        self.where_clause_suffix = """
            ('dbo', 'sys')
        """

        config_dict = {
            MSSQLMetadataExtractor.WHERE_CLAUSE_SUFFIX_KEY: self.where_clause_suffix,
            f'extractor.sqlalchemy.{SQLAlchemyExtractor.CONN_STRING}': 'TEST_CONNECTION'
        }
        self.conf = ConfigFactory.from_dict(config_dict)

    def test_sql_statement(self) -> None:
        """
        Test Extraction with empty result from query
        """
        with patch.object(SQLAlchemyExtractor, '_get_connection'):
            extractor = MSSQLMetadataExtractor()
            extractor.init(self.conf)
            self.assertTrue(self.where_clause_suffix in extractor.sql_stmt)


class TestMSSQLMetadataExtractorClusterKeyNoTableCatalog(unittest.TestCase):
    # test when USE_CATALOG_AS_CLUSTER_NAME is false and CLUSTER_KEY is specified
    def setUp(self) -> None:
        logging.basicConfig(level=logging.INFO)
        self.cluster_key = "not_master"

        config_dict = {
            MSSQLMetadataExtractor.CLUSTER_KEY: self.cluster_key,
            f'extractor.sqlalchemy.{SQLAlchemyExtractor.CONN_STRING}': 'TEST_CONNECTION',
            MSSQLMetadataExtractor.USE_CATALOG_AS_CLUSTER_NAME: False
        }
        self.conf = ConfigFactory.from_dict(config_dict)

    def test_sql_statement(self) -> None:
        """
        Test Extraction with empty result from query
        """
        with patch.object(SQLAlchemyExtractor, '_get_connection'):
            extractor = MSSQLMetadataExtractor()
            extractor.init(self.conf)
            self.assertTrue(self.cluster_key in extractor.sql_stmt)


class TestMSSQLMetadataExtractorNoClusterKeyNoTableCatalog(unittest.TestCase):
    # test when USE_CATALOG_AS_CLUSTER_NAME is false and CLUSTER_KEY is NOT specified
    def setUp(self) -> None:
        logging.basicConfig(level=logging.INFO)

        config_dict = {
            f'extractor.sqlalchemy.{SQLAlchemyExtractor.CONN_STRING}': 'TEST_CONNECTION',
            MSSQLMetadataExtractor.USE_CATALOG_AS_CLUSTER_NAME: False
        }
        self.conf = ConfigFactory.from_dict(config_dict)

    def test_sql_statement(self) -> None:
        """
        Test Extraction with empty result from query
        """
        with patch.object(SQLAlchemyExtractor, '_get_connection'):
            extractor = MSSQLMetadataExtractor()
            extractor.init(self.conf)
            self.assertTrue(MSSQLMetadataExtractor.DEFAULT_CLUSTER_NAME in extractor.sql_stmt)


class TestMSSQLMetadataExtractorTableCatalogEnabled(unittest.TestCase):
    # test when USE_CATALOG_AS_CLUSTER_NAME is true (CLUSTER_KEY should be ignored)
    def setUp(self) -> None:
        logging.basicConfig(level=logging.INFO)
        self.cluster_key = "not_master"

        config_dict = {
            MSSQLMetadataExtractor.CLUSTER_KEY: self.cluster_key,
            f'extractor.sqlalchemy.{SQLAlchemyExtractor.CONN_STRING}': 'TEST_CONNECTION',
            MSSQLMetadataExtractor.USE_CATALOG_AS_CLUSTER_NAME: True
        }
        self.conf = ConfigFactory.from_dict(config_dict)

    def test_sql_statement(self) -> None:
        """
        Test Extraction with empty result from query
        """
        with patch.object(SQLAlchemyExtractor, '_get_connection'):
            extractor = MSSQLMetadataExtractor()
            extractor.init(self.conf)
            self.assertTrue('DB_NAME()' in extractor.sql_stmt)
            self.assertFalse(self.cluster_key in extractor.sql_stmt)


if __name__ == '__main__':
    unittest.main()
