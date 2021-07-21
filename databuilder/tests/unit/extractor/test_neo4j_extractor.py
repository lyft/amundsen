# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import unittest
from typing import Any

from mock import patch
from pyhocon import ConfigFactory

from databuilder import Scoped
from databuilder.extractor.neo4j_extractor import Neo4jExtractor
from databuilder.models.table_elasticsearch_document import TableESDocument


class TestNeo4jExtractor(unittest.TestCase):

    def setUp(self) -> None:
        config_dict = {
            f'extractor.neo4j.{Neo4jExtractor.GRAPH_URL_CONFIG_KEY}': 'TEST_GRAPH_URL',
            f'extractor.neo4j.{Neo4jExtractor.CYPHER_QUERY_CONFIG_KEY}': 'TEST_QUERY',
            f'extractor.neo4j.{Neo4jExtractor.NEO4J_AUTH_USER}': 'TEST_USER',
            f'extractor.neo4j.{Neo4jExtractor.NEO4J_AUTH_PW}': 'TEST_PW'
        }

        self.conf = ConfigFactory.from_dict(config_dict)

    def text_extraction_with_empty_query_result(self: Any) -> None:
        """
        Test Extraction with empty results from query
        """
        with patch.object(Neo4jExtractor, '_get_driver'):
            extractor = Neo4jExtractor()
            extractor.init(Scoped.get_scoped_conf(conf=self.conf,
                                                  scope=extractor.get_scope()))

            extractor.results = ['']
            result = extractor.extract()
            self.assertIsNone(result)

    def test_extraction_with_single_query_result(self: Any) -> None:
        """
        Test Extraction with single result from query
        """
        with patch.object(Neo4jExtractor, '_get_driver'):
            extractor = Neo4jExtractor()
            extractor.init(Scoped.get_scoped_conf(conf=self.conf,
                                                  scope=extractor.get_scope()))

            extractor.results = ['test_result']
            result = extractor.extract()
            self.assertEqual(result, 'test_result')

            # Ensure second result is None
            result = extractor.extract()
            self.assertIsNone(result)

    def test_extraction_with_multiple_query_result(self: Any) -> None:
        """
        Test Extraction with multiple result from query
        """
        with patch.object(Neo4jExtractor, '_get_driver'):
            extractor = Neo4jExtractor()
            extractor.init(Scoped.get_scoped_conf(conf=self.conf,
                                                  scope=extractor.get_scope()))

            extractor.results = ['test_result1', 'test_result2', 'test_result3']

            result = extractor.extract()
            self.assertEqual(result, 'test_result1')

            result = extractor.extract()
            self.assertEqual(result, 'test_result2')

            result = extractor.extract()
            self.assertEqual(result, 'test_result3')

            # Ensure next result is None
            result = extractor.extract()
            self.assertIsNone(result)

    def test_extraction_with_model_class(self: Any) -> None:
        """
        Test Extraction using model class
        """
        config_dict = {
            f'extractor.neo4j.{Neo4jExtractor.GRAPH_URL_CONFIG_KEY}': 'TEST_GRAPH_URL',
            f'extractor.neo4j.{Neo4jExtractor.CYPHER_QUERY_CONFIG_KEY}': 'TEST_QUERY',
            f'extractor.neo4j.{Neo4jExtractor.NEO4J_AUTH_USER}': 'TEST_USER',
            f'extractor.neo4j.{Neo4jExtractor.NEO4J_AUTH_PW}': 'TEST_PW',
            f'extractor.neo4j.{Neo4jExtractor.MODEL_CLASS_CONFIG_KEY}':
                'databuilder.models.table_elasticsearch_document.TableESDocument'
        }

        self.conf = ConfigFactory.from_dict(config_dict)

        with patch.object(Neo4jExtractor, '_get_driver'):
            extractor = Neo4jExtractor()
            extractor.init(Scoped.get_scoped_conf(conf=self.conf,
                                                  scope=extractor.get_scope()))

            result_dict = dict(database='test_database',
                               cluster='test_cluster',
                               schema='test_schema',
                               name='test_table_name',
                               display_name='test_schema.test_table_name',
                               key='test_table_key',
                               description='test_table_description',
                               last_updated_timestamp=123456789,
                               column_names=['test_col1', 'test_col2', 'test_col3'],
                               column_descriptions=['test_description1', 'test_description2', ''],
                               total_usage=100,
                               unique_usage=5,
                               tags=['hive'],
                               badges=['badge1'],
                               schema_description='schema_description',
                               programmatic_descriptions=['TEST'])

            extractor.results = [result_dict]
            result_obj = extractor.extract()

            self.assertIsInstance(result_obj, TableESDocument)
            self.assertDictEqual(vars(result_obj), result_dict)
