# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import unittest
from typing import Any, Dict

from mock import patch
from pyhocon import ConfigFactory

from databuilder import Scoped
from databuilder.extractor.sql_alchemy_extractor import SQLAlchemyExtractor


class TestSqlAlchemyExtractor(unittest.TestCase):

    def setUp(self) -> None:
        config_dict = {
            'extractor.sqlalchemy.conn_string': 'TEST_CONNECTION',
            'extractor.sqlalchemy.extract_sql': 'SELECT 1 FROM TEST_TABLE;'
        }
        self.conf = ConfigFactory.from_dict(config_dict)

    @patch.object(SQLAlchemyExtractor, '_get_connection')
    def test_extraction_with_empty_query_result(self: Any,
                                                mock_method: Any) -> None:
        """
        Test Extraction with empty result from query
        """
        extractor = SQLAlchemyExtractor()
        extractor.results = ['']
        extractor.init(Scoped.get_scoped_conf(conf=self.conf,
                                              scope=extractor.get_scope()))

        results = extractor.extract()
        self.assertEqual(results, '')

    @patch.object(SQLAlchemyExtractor, '_get_connection')
    def test_extraction_with_single_query_result(self: Any,
                                                 mock_method: Any) -> None:
        """
        Test Extraction from single result from query
        """
        extractor = SQLAlchemyExtractor()
        extractor.results = [('test_result')]
        extractor.init(Scoped.get_scoped_conf(conf=self.conf,
                                              scope=extractor.get_scope()))
        results = extractor.extract()
        self.assertEqual(results, 'test_result')

    @patch.object(SQLAlchemyExtractor, '_get_connection')
    def test_extraction_with_multiple_query_result(self: Any,
                                                   mock_method: Any) -> None:
        """
        Test Extraction from list of results from query
        """
        extractor = SQLAlchemyExtractor()
        extractor.results = ['test_result', 'test_result2', 'test_result3']
        extractor.init(Scoped.get_scoped_conf(conf=self.conf,
                                              scope=extractor.get_scope()))
        result = [extractor.extract() for _ in range(3)]

        self.assertEqual(len(result), 3)
        self.assertEqual(result,
                         ['test_result', 'test_result2', 'test_result3'])

    @patch.object(SQLAlchemyExtractor, '_get_connection')
    def test_extraction_with_model_class(self: Any, mock_method: Any) -> None:
        """
        Test Extraction using model class
        """
        config_dict = {
            'extractor.sqlalchemy.conn_string': 'TEST_CONNECTION',
            'extractor.sqlalchemy.extract_sql': 'SELECT 1 FROM TEST_TABLE;',
            'extractor.sqlalchemy.model_class':
                'tests.unit.extractor.test_sql_alchemy_extractor.TableMetadataResult'
        }
        self.conf = ConfigFactory.from_dict(config_dict)

        extractor = SQLAlchemyExtractor()
        extractor.results = [dict(database='test_database',
                                  schema='test_schema',
                                  name='test_table',
                                  description='test_description',
                                  column_name='test_column_name',
                                  column_type='test_column_type',
                                  column_comment='test_column_comment',
                                  owner='test_owner')]

        extractor.init(Scoped.get_scoped_conf(conf=self.conf,
                                              scope=extractor.get_scope()))

        result = extractor.extract()

        self.assertIsInstance(result, TableMetadataResult)
        self.assertEqual(result.name, 'test_table')

    @patch('databuilder.extractor.sql_alchemy_extractor.create_engine')
    def test_get_connection(self: Any, mock_method: Any) -> None:
        """
        Test that configs are passed through correctly to the _get_connection method
        """
        extractor = SQLAlchemyExtractor()
        config_dict: Dict[str, Any] = {
            'extractor.sqlalchemy.conn_string': 'TEST_CONNECTION',
            'extractor.sqlalchemy.extract_sql': 'SELECT 1 FROM TEST_TABLE;'
        }
        conf = ConfigFactory.from_dict(config_dict)
        extractor.init(Scoped.get_scoped_conf(conf=conf,
                                              scope=extractor.get_scope()))
        extractor._get_connection()
        mock_method.assert_called_with('TEST_CONNECTION', connect_args={})

        extractor = SQLAlchemyExtractor()
        config_dict = {
            'extractor.sqlalchemy.conn_string': 'TEST_CONNECTION',
            'extractor.sqlalchemy.extract_sql': 'SELECT 1 FROM TEST_TABLE;',
            'extractor.sqlalchemy.connect_args': {"protocol": "https"},
        }
        conf = ConfigFactory.from_dict(config_dict)
        extractor.init(Scoped.get_scoped_conf(conf=conf,
                                              scope=extractor.get_scope()))
        extractor._get_connection()
        mock_method.assert_called_with('TEST_CONNECTION', connect_args={"protocol": "https"})


class TableMetadataResult:
    """
    Table metadata result model.
    SQL result has one row per column
    """

    def __init__(self,
                 database: str,
                 schema: str,
                 name: str,
                 description: str,
                 column_name: str,
                 column_type: str,
                 column_comment: str,
                 owner: str
                 ) -> None:
        self.database = database
        self.schema = schema
        self.name = name
        self.description = description
        self.column_name = column_name
        self.column_type = column_type
        self.column_comment = column_comment
        self.owner = owner
