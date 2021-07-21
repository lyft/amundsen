# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import unittest

from mock import MagicMock, patch
from pyhocon import ConfigFactory

from databuilder.extractor.snowflake_table_last_updated_extractor import SnowflakeTableLastUpdatedExtractor
from databuilder.extractor.sql_alchemy_extractor import SQLAlchemyExtractor
from databuilder.models.table_last_updated import TableLastUpdated


class TestSnowflakeTableLastUpdatedExtractor(unittest.TestCase):
    def setUp(self) -> None:
        config_dict = {
            f'extractor.sqlalchemy.{SQLAlchemyExtractor.CONN_STRING}':
                'TEST_CONNECTION',
            f'extractor.snowflake_table_last_updated.{SnowflakeTableLastUpdatedExtractor.CLUSTER_KEY}':
                'MY_CLUSTER',
            f'extractor.snowflake_table_last_updated.{SnowflakeTableLastUpdatedExtractor.USE_CATALOG_AS_CLUSTER_NAME}':
                False,
            f'extractor.snowflake_table_last_updated.{SnowflakeTableLastUpdatedExtractor.SNOWFLAKE_DATABASE_KEY}':
                'prod'
        }
        self.conf = ConfigFactory.from_dict(config_dict)

    def test_extraction_with_empty_query_result(self) -> None:
        """
        Test Extraction with empty result from query
        """
        with patch.object(SQLAlchemyExtractor, '_get_connection'):
            extractor = SnowflakeTableLastUpdatedExtractor()
            extractor.init(self.conf)

            results = extractor.extract()
            self.assertIsNone(results)

    def test_extraction_with_single_result(self) -> None:
        """
        Test Extraction with default cluster and database and with one table as result
        """
        with patch.object(SQLAlchemyExtractor, '_get_connection') as mock_connection:
            connection = MagicMock()
            mock_connection.return_value = connection
            sql_execute = MagicMock()
            connection.execute = sql_execute
            sql_execute.return_value = [
                {'schema': 'test_schema',
                 'table_name': 'test_table',
                 'last_updated_time': 1000,
                 'cluster': self.conf[
                     f'extractor.snowflake_table_last_updated.{SnowflakeTableLastUpdatedExtractor.CLUSTER_KEY}'],
                 }
            ]

            extractor = SnowflakeTableLastUpdatedExtractor()
            extractor.init(self.conf)
            actual = extractor.extract()

            expected = TableLastUpdated(schema='test_schema', table_name='test_table',
                                        last_updated_time_epoch=1000,
                                        db='snowflake', cluster='MY_CLUSTER')
            self.assertEqual(expected.__repr__(), actual.__repr__())
            self.assertIsNone(extractor.extract())

    def test_extraction_with_multiple_result(self) -> None:
        """
        Test Extraction with default cluster and database and with multiple tables as result
        """
        with patch.object(SQLAlchemyExtractor, '_get_connection') as mock_connection:
            connection = MagicMock()
            mock_connection.return_value = connection
            sql_execute = MagicMock()
            connection.execute = sql_execute

            default_cluster = self.conf[
                f'extractor.snowflake_table_last_updated.{SnowflakeTableLastUpdatedExtractor.CLUSTER_KEY}']

            table = {'schema': 'test_schema1',
                     'table_name': 'test_table1',
                     'last_updated_time': 1000,
                     'cluster': default_cluster
                     }

            table1 = {'schema': 'test_schema1',
                      'table_name': 'test_table2',
                      'last_updated_time': 2000,
                      'cluster': default_cluster
                      }

            table2 = {'schema': 'test_schema2',
                      'table_name': 'test_table3',
                      'last_updated_time': 3000,
                      'cluster': default_cluster
                      }

            sql_execute.return_value = [table, table1, table2]

            extractor = SnowflakeTableLastUpdatedExtractor()
            extractor.init(self.conf)

            expected = TableLastUpdated(schema='test_schema1', table_name='test_table1',
                                        last_updated_time_epoch=1000,
                                        db='snowflake', cluster='MY_CLUSTER')
            self.assertEqual(expected.__repr__(), extractor.extract().__repr__())

            expected = TableLastUpdated(schema='test_schema1', table_name='test_table2',
                                        last_updated_time_epoch=2000,
                                        db='snowflake', cluster='MY_CLUSTER')
            self.assertEqual(expected.__repr__(), extractor.extract().__repr__())

            expected = TableLastUpdated(schema='test_schema2', table_name='test_table3',
                                        last_updated_time_epoch=3000,
                                        db='snowflake', cluster='MY_CLUSTER')
            self.assertEqual(expected.__repr__(), extractor.extract().__repr__())

            self.assertIsNone(extractor.extract())


class TestSnowflakeTableLastUpdatedExtractorWithWhereClause(unittest.TestCase):
    """
    Test 'where_clause' config key in extractor
    """

    def setUp(self) -> None:
        self.where_clause_suffix = """
        where table_schema in ('public') and table_name = 'movies'
        """

        config_dict = {
            SnowflakeTableLastUpdatedExtractor.WHERE_CLAUSE_SUFFIX_KEY: self.where_clause_suffix,
            f'extractor.sqlalchemy.{SQLAlchemyExtractor.CONN_STRING}': 'TEST_CONNECTION'
        }
        self.conf = ConfigFactory.from_dict(config_dict)

    def test_sql_statement(self) -> None:
        """
        test where clause in extractor sql statement
        """
        with patch.object(SQLAlchemyExtractor, '_get_connection'):
            extractor = SnowflakeTableLastUpdatedExtractor()
            extractor.init(self.conf)
            self.assertTrue(self.where_clause_suffix in extractor.sql_stmt)


class TestSnowflakeTableLastUpdatedExtractorClusterKeyNoTableCatalog(unittest.TestCase):
    """
    Test with 'USE_CATALOG_AS_CLUSTER_NAME' is false and 'CLUSTER_KEY' is specified
    """

    def setUp(self) -> None:
        self.cluster_key = "not_master"

        config_dict = {
            SnowflakeTableLastUpdatedExtractor.CLUSTER_KEY: self.cluster_key,
            f'extractor.sqlalchemy.{SQLAlchemyExtractor.CONN_STRING}':
                'TEST_CONNECTION',
            SnowflakeTableLastUpdatedExtractor.USE_CATALOG_AS_CLUSTER_NAME: False
        }
        self.conf = ConfigFactory.from_dict(config_dict)

    def test_sql_statement(self) -> None:
        """
        Test cluster_key in extractor sql stmt
        """
        with patch.object(SQLAlchemyExtractor, '_get_connection'):
            extractor = SnowflakeTableLastUpdatedExtractor()
            extractor.init(self.conf)
            self.assertTrue(self.cluster_key in extractor.sql_stmt)


class TestSnowflakeTableLastUpdatedExtractorDefaultSnowflakeDatabaseKey(unittest.TestCase):
    """
    Test with SNOWFLAKE_DATABASE_KEY config specified
    """

    def setUp(self) -> None:
        self.snowflake_database_key = "not_prod"

        config_dict = {
            SnowflakeTableLastUpdatedExtractor.SNOWFLAKE_DATABASE_KEY: self.snowflake_database_key,
            f'extractor.sqlalchemy.{SQLAlchemyExtractor.CONN_STRING}': 'TEST_CONNECTION'
        }
        self.conf = ConfigFactory.from_dict(config_dict)

    def test_sql_statement(self) -> None:
        """
        Test SNOWFLAKE_DATABASE_KEY in extractor sql stmt
        """
        with patch.object(SQLAlchemyExtractor, '_get_connection'):
            extractor = SnowflakeTableLastUpdatedExtractor()
            extractor.init(self.conf)
            self.assertTrue(self.snowflake_database_key in extractor.sql_stmt)


class TestSnowflakeTableLastUpdatedExtractorDefaultDatabaseKey(unittest.TestCase):
    """
    Test with DATABASE_KEY config specified
    """

    def setUp(self) -> None:
        self.database_key = 'not_snowflake'

        config_dict = {
            SnowflakeTableLastUpdatedExtractor.DATABASE_KEY: self.database_key,
            f'extractor.sqlalchemy.{SQLAlchemyExtractor.CONN_STRING}': 'TEST_CONNECTION'
        }
        self.conf = ConfigFactory.from_dict(config_dict)

    def test_sql_statement(self) -> None:
        """
        Test DATABASE_KEY in extractor sql stmt
        """
        with patch.object(SQLAlchemyExtractor, '_get_connection'):
            extractor = SnowflakeTableLastUpdatedExtractor()
            extractor.init(self.conf)
            self.assertFalse(self.database_key in extractor.sql_stmt)

    def test_extraction_with_database_specified(self) -> None:
        """
        Test DATABASE_KEY in extractor result
        """
        with patch.object(SQLAlchemyExtractor, '_get_connection') as mock_connection:
            connection = MagicMock()
            mock_connection.return_value = connection
            sql_execute = MagicMock()
            connection.execute = sql_execute

            sql_execute.return_value = [
                {'schema': 'test_schema',
                 'table_name': 'test_table',
                 'last_updated_time': 1000,
                 'cluster': 'MY_CLUSTER',
                 }
            ]

            extractor = SnowflakeTableLastUpdatedExtractor()
            extractor.init(self.conf)
            actual = extractor.extract()
            expected = TableLastUpdated(schema='test_schema', table_name='test_table',
                                        last_updated_time_epoch=1000,
                                        db=self.database_key, cluster='MY_CLUSTER')
            self.assertEqual(expected.__repr__(), actual.__repr__())
            self.assertIsNone(extractor.extract())


class TestSnowflakeTableLastUpdatedExtractorNoClusterKeyNoTableCatalog(unittest.TestCase):
    """
    Test when USE_CATALOG_AS_CLUSTER_NAME is false and CLUSTER_KEY is NOT specified
    """

    def setUp(self) -> None:
        config_dict = {
            f'extractor.sqlalchemy.{SQLAlchemyExtractor.CONN_STRING}': 'TEST_CONNECTION',
            SnowflakeTableLastUpdatedExtractor.USE_CATALOG_AS_CLUSTER_NAME: False
        }
        self.conf = ConfigFactory.from_dict(config_dict)

    def test_sql_statement(self) -> None:
        """
        Test cluster name in extract sql stmt
        """
        with patch.object(SQLAlchemyExtractor, '_get_connection'):
            extractor = SnowflakeTableLastUpdatedExtractor()
            extractor.init(self.conf)
            self.assertTrue(SnowflakeTableLastUpdatedExtractor.DEFAULT_CLUSTER_NAME in extractor.sql_stmt)


class TestSnowflakeTableLastUpdatedExtractorTableCatalogEnabled(unittest.TestCase):
    """
    Test when USE_CATALOG_AS_CLUSTER_NAME is true (CLUSTER_KEY should be ignored)
    """

    def setUp(self) -> None:
        self.cluster_key = "not_master"

        config_dict = {
            SnowflakeTableLastUpdatedExtractor.CLUSTER_KEY: self.cluster_key,
            f'extractor.sqlalchemy.{SQLAlchemyExtractor.CONN_STRING}': 'TEST_CONNECTION',
            SnowflakeTableLastUpdatedExtractor.USE_CATALOG_AS_CLUSTER_NAME: True
        }
        self.conf = ConfigFactory.from_dict(config_dict)

    def test_sql_statement(self) -> None:
        """
        Ensure catalog is used as cluster in extract sql stmt
        """
        with patch.object(SQLAlchemyExtractor, '_get_connection'):
            extractor = SnowflakeTableLastUpdatedExtractor()
            extractor.init(self.conf)
            self.assertTrue('table_catalog' in extractor.sql_stmt)
            self.assertFalse(self.cluster_key in extractor.sql_stmt)


if __name__ == '__main__':
    unittest.main()
