# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import logging
import unittest
from typing import Any, Dict

from mock import MagicMock, patch
from pyhocon import ConfigFactory

from databuilder.extractor.snowflake_metadata_extractor import SnowflakeMetadataExtractor
from databuilder.extractor.sql_alchemy_extractor import SQLAlchemyExtractor
from databuilder.models.table_metadata import ColumnMetadata, TableMetadata


class TestSnowflakeMetadataExtractor(unittest.TestCase):
    def setUp(self) -> None:
        logging.basicConfig(level=logging.INFO)

        config_dict = {
            f'extractor.sqlalchemy.{SQLAlchemyExtractor.CONN_STRING}': 'TEST_CONNECTION',
            f'extractor.snowflake_metadata.{SnowflakeMetadataExtractor.CLUSTER_KEY}': 'MY_CLUSTER',
            f'extractor.snowflake_metadata.{SnowflakeMetadataExtractor.USE_CATALOG_AS_CLUSTER_NAME}': False,
            f'extractor.snowflake_metadata.{SnowflakeMetadataExtractor.SNOWFLAKE_DATABASE_KEY}': 'prod'
        }
        self.conf = ConfigFactory.from_dict(config_dict)

    def test_extraction_with_empty_query_result(self) -> None:
        """
        Test Extraction with empty result from query
        """
        with patch.object(SQLAlchemyExtractor, '_get_connection'):
            extractor = SnowflakeMetadataExtractor()
            extractor.init(self.conf)

            results = extractor.extract()
            self.assertEqual(results, None)

    def test_extraction_with_single_result(self) -> None:
        with patch.object(SQLAlchemyExtractor, '_get_connection') as mock_connection:
            connection = MagicMock()
            mock_connection.return_value = connection
            sql_execute = MagicMock()
            connection.execute = sql_execute
            table = {'schema': 'test_schema',
                     'name': 'test_table',
                     'description': 'a table for testing',
                     'cluster': self.conf[f'extractor.snowflake_metadata.{SnowflakeMetadataExtractor.CLUSTER_KEY}'],
                     'is_view': 'false'
                     }

            sql_execute.return_value = [
                self._union(
                    {'col_name': 'col_id1',
                     'col_type': 'number',
                     'col_description': 'description of id1',
                     'col_sort_order': 0}, table),
                self._union(
                    {'col_name': 'col_id2',
                     'col_type': 'number',
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
                     'col_type': 'timestamp_ltz',
                     'col_description': 'description of etl_created_at',
                     'col_sort_order': 4}, table),
                self._union(
                    {'col_name': 'ds',
                     'col_type': 'varchar',
                     'col_description': None,
                     'col_sort_order': 5}, table)
            ]

            extractor = SnowflakeMetadataExtractor()
            extractor.init(self.conf)
            actual = extractor.extract()
            expected = TableMetadata('snowflake', 'MY_CLUSTER', 'test_schema', 'test_table', 'a table for testing',
                                     [ColumnMetadata('col_id1', 'description of id1', 'number', 0),
                                      ColumnMetadata('col_id2', 'description of id2', 'number', 1),
                                      ColumnMetadata('is_active', None, 'boolean', 2),
                                      ColumnMetadata('source', 'description of source', 'varchar', 3),
                                      ColumnMetadata('etl_created_at', 'description of etl_created_at',
                                                     'timestamp_ltz', 4),
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
                     'description': 'test table 1',
                     'cluster':
                         self.conf[f'extractor.snowflake_metadata.{SnowflakeMetadataExtractor.CLUSTER_KEY}'],
                     'is_view': 'nottrue'
                     }

            table1 = {'schema': 'test_schema1',
                      'name': 'test_table2',
                      'description': 'test table 2',
                      'cluster':
                          self.conf[f'extractor.snowflake_metadata.{SnowflakeMetadataExtractor.CLUSTER_KEY}'],
                      'is_view': 'false'
                      }

            table2 = {'schema': 'test_schema2',
                      'name': 'test_table3',
                      'description': 'test table 3',
                      'cluster':
                          self.conf[f'extractor.snowflake_metadata.{SnowflakeMetadataExtractor.CLUSTER_KEY}'],
                      'is_view': 'true'
                      }

            sql_execute.return_value = [
                self._union(
                    {'col_name': 'col_id1',
                     'col_type': 'number',
                     'col_description': 'description of col_id1',
                     'col_sort_order': 0}, table),
                self._union(
                    {'col_name': 'col_id2',
                     'col_type': 'number',
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
                     'col_type': 'timestamp_ltz',
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

            extractor = SnowflakeMetadataExtractor()
            extractor.init(self.conf)

            expected = TableMetadata('snowflake',
                                     self.conf[
                                         f'extractor.snowflake_metadata.{SnowflakeMetadataExtractor.CLUSTER_KEY}'],
                                     'test_schema1', 'test_table1', 'test table 1',
                                     [ColumnMetadata('col_id1', 'description of col_id1', 'number', 0),
                                      ColumnMetadata('col_id2', 'description of col_id2', 'number', 1),
                                      ColumnMetadata('is_active', None, 'boolean', 2),
                                      ColumnMetadata('source', 'description of source', 'varchar', 3),
                                      ColumnMetadata('etl_created_at', 'description of etl_created_at',
                                                     'timestamp_ltz', 4),
                                      ColumnMetadata('ds', None, 'varchar', 5)])
            self.assertEqual(expected.__repr__(), extractor.extract().__repr__())

            expected = TableMetadata('snowflake',
                                     self.conf[
                                         f'extractor.snowflake_metadata.{SnowflakeMetadataExtractor.CLUSTER_KEY}'],
                                     'test_schema1', 'test_table2', 'test table 2',
                                     [ColumnMetadata('col_name', 'description of col_name', 'varchar', 0),
                                      ColumnMetadata('col_name2', 'description of col_name2', 'varchar', 1)])
            self.assertEqual(expected.__repr__(), extractor.extract().__repr__())

            expected = TableMetadata('snowflake',
                                     self.conf[
                                         f'extractor.snowflake_metadata.{SnowflakeMetadataExtractor.CLUSTER_KEY}'],
                                     'test_schema2', 'test_table3', 'test table 3',
                                     [ColumnMetadata('col_id3', 'description of col_id3', 'varchar', 0),
                                      ColumnMetadata('col_name3', 'description of col_name3',
                                                     'varchar', 1)],
                                     True)
            self.assertEqual(expected.__repr__(), extractor.extract().__repr__())

            self.assertIsNone(extractor.extract())
            self.assertIsNone(extractor.extract())

    def _union(self,
               target: Dict[Any, Any],
               extra: Dict[Any, Any]) -> Dict[Any, Any]:
        target.update(extra)
        return target


class TestSnowflakeMetadataExtractorWithWhereClause(unittest.TestCase):
    def setUp(self) -> None:
        logging.basicConfig(level=logging.INFO)
        self.where_clause_suffix = """
        where table_schema in ('public') and table_name = 'movies'
        """

        config_dict = {
            SnowflakeMetadataExtractor.WHERE_CLAUSE_SUFFIX_KEY: self.where_clause_suffix,
            f'extractor.sqlalchemy.{SQLAlchemyExtractor.CONN_STRING}':
                'TEST_CONNECTION'
        }
        self.conf = ConfigFactory.from_dict(config_dict)

    def test_sql_statement(self) -> None:
        """
        Test Extraction with empty result from query
        """
        with patch.object(SQLAlchemyExtractor, '_get_connection'):
            extractor = SnowflakeMetadataExtractor()
            extractor.init(self.conf)
            self.assertTrue(self.where_clause_suffix in extractor.sql_stmt)


class TestSnowflakeMetadataExtractorClusterKeyNoTableCatalog(unittest.TestCase):
    # test when USE_CATALOG_AS_CLUSTER_NAME is false and CLUSTER_KEY is specified
    def setUp(self) -> None:
        logging.basicConfig(level=logging.INFO)
        self.cluster_key = "not_master"

        config_dict = {
            SnowflakeMetadataExtractor.CLUSTER_KEY: self.cluster_key,
            f'extractor.sqlalchemy.{SQLAlchemyExtractor.CONN_STRING}':
                'TEST_CONNECTION',
            SnowflakeMetadataExtractor.USE_CATALOG_AS_CLUSTER_NAME: False
        }
        self.conf = ConfigFactory.from_dict(config_dict)

    def test_sql_statement(self) -> None:
        """
        Test Extraction with empty result from query
        """
        with patch.object(SQLAlchemyExtractor, '_get_connection'):
            extractor = SnowflakeMetadataExtractor()
            extractor.init(self.conf)
            self.assertTrue(self.cluster_key in extractor.sql_stmt)


class TestSnowflakeMetadataExtractorDefaultSnowflakeDatabaseKey(unittest.TestCase):
    # test when SNOWFLAKE_DATABASE_KEY is specified
    def setUp(self) -> None:
        logging.basicConfig(level=logging.INFO)
        self.snowflake_database_key = "not_prod"

        config_dict = {
            SnowflakeMetadataExtractor.SNOWFLAKE_DATABASE_KEY: self.snowflake_database_key,
            f'extractor.sqlalchemy.{SQLAlchemyExtractor.CONN_STRING}':
                'TEST_CONNECTION'
        }
        self.conf = ConfigFactory.from_dict(config_dict)

    def test_sql_statement(self) -> None:
        """
        Test Extraction with empty result from query
        """
        with patch.object(SQLAlchemyExtractor, '_get_connection'):
            extractor = SnowflakeMetadataExtractor()
            extractor.init(self.conf)
            self.assertTrue(self.snowflake_database_key in extractor.sql_stmt)


class TestSnowflakeMetadataExtractorDefaultDatabaseKey(unittest.TestCase):
    # test when DATABASE_KEY is specified
    def setUp(self) -> None:
        logging.basicConfig(level=logging.INFO)
        self.database_key = 'not_snowflake'

        config_dict = {
            SnowflakeMetadataExtractor.DATABASE_KEY: self.database_key,
            f'extractor.sqlalchemy.{SQLAlchemyExtractor.CONN_STRING}':
                'TEST_CONNECTION'
        }
        self.conf = ConfigFactory.from_dict(config_dict)

    def test_sql_statement(self) -> None:
        """
        Test Extraction with empty result from query
        """
        with patch.object(SQLAlchemyExtractor, '_get_connection'):
            extractor = SnowflakeMetadataExtractor()
            extractor.init(self.conf)
            self.assertFalse(self.database_key in extractor.sql_stmt)

    def test_extraction_with_database_specified(self) -> None:
        with patch.object(SQLAlchemyExtractor, '_get_connection') as mock_connection:
            connection = MagicMock()
            mock_connection.return_value = connection
            sql_execute = MagicMock()
            connection.execute = sql_execute

            sql_execute.return_value = [
                {'schema': 'test_schema',
                 'name': 'test_table',
                 'description': 'a table for testing',
                 'cluster': 'MY_CLUSTER',
                 'is_view': 'false',
                 'col_name': 'ds',
                 'col_type': 'varchar',
                 'col_description': None,
                 'col_sort_order': 0}
            ]

            extractor = SnowflakeMetadataExtractor()
            extractor.init(self.conf)
            actual = extractor.extract()
            expected = TableMetadata(
                self.database_key, 'MY_CLUSTER', 'test_schema', 'test_table', 'a table for testing',
                [ColumnMetadata('ds', None, 'varchar', 0)]
            )

            self.assertEqual(expected.__repr__(), actual.__repr__())
            self.assertIsNone(extractor.extract())


class TestSnowflakeMetadataExtractorNoClusterKeyNoTableCatalog(unittest.TestCase):
    # test when USE_CATALOG_AS_CLUSTER_NAME is false and CLUSTER_KEY is NOT specified
    def setUp(self) -> None:
        logging.basicConfig(level=logging.INFO)

        config_dict = {
            f'extractor.sqlalchemy.{SQLAlchemyExtractor.CONN_STRING}':
                'TEST_CONNECTION',
            SnowflakeMetadataExtractor.USE_CATALOG_AS_CLUSTER_NAME: False
        }
        self.conf = ConfigFactory.from_dict(config_dict)

    def test_sql_statement(self) -> None:
        """
        Test Extraction with empty result from query
        """
        with patch.object(SQLAlchemyExtractor, '_get_connection'):
            extractor = SnowflakeMetadataExtractor()
            extractor.init(self.conf)
            self.assertTrue(SnowflakeMetadataExtractor.DEFAULT_CLUSTER_NAME in extractor.sql_stmt)


class TestSnowflakeMetadataExtractorTableCatalogEnabled(unittest.TestCase):
    # test when USE_CATALOG_AS_CLUSTER_NAME is true (CLUSTER_KEY should be ignored)
    def setUp(self) -> None:
        logging.basicConfig(level=logging.INFO)
        self.cluster_key = "not_master"

        config_dict = {
            SnowflakeMetadataExtractor.CLUSTER_KEY: self.cluster_key,
            f'extractor.sqlalchemy.{SQLAlchemyExtractor.CONN_STRING}':
                'TEST_CONNECTION',
            SnowflakeMetadataExtractor.USE_CATALOG_AS_CLUSTER_NAME: True
        }
        self.conf = ConfigFactory.from_dict(config_dict)

    def test_sql_statement(self) -> None:
        """
        Test Extraction with empty result from query
        """
        with patch.object(SQLAlchemyExtractor, '_get_connection'):
            extractor = SnowflakeMetadataExtractor()
            extractor.init(self.conf)
            self.assertTrue('table_catalog' in extractor.sql_stmt)
            self.assertFalse(self.cluster_key in extractor.sql_stmt)


if __name__ == '__main__':
    unittest.main()
