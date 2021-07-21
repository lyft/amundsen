# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import json
import unittest

from databuilder.models.table_elasticsearch_document import TableESDocument


class TestTableElasticsearchDocument(unittest.TestCase):

    def test_to_json(self) -> None:
        """
        Test string generated from to_json method
        """
        test_obj = TableESDocument(database='test_database',
                                   cluster='test_cluster',
                                   schema='test_schema',
                                   name='test_table',
                                   key='test_table_key',
                                   last_updated_timestamp=123456789,
                                   description='test_table_description',
                                   column_names=['test_col1', 'test_col2'],
                                   column_descriptions=['test_description1', 'test_description2'],
                                   total_usage=100,
                                   unique_usage=10,
                                   tags=['test'],
                                   programmatic_descriptions=['test'],
                                   badges=['badge1'],
                                   schema_description='schema description')

        expected_document_dict = {"database": "test_database",
                                  "cluster": "test_cluster",
                                  "schema": "test_schema",
                                  "name": "test_table",
                                  "display_name": "test_schema.test_table",
                                  "key": "test_table_key",
                                  "last_updated_timestamp": 123456789,
                                  "description": "test_table_description",
                                  "column_names": ["test_col1", "test_col2"],
                                  "column_descriptions": ["test_description1", "test_description2"],
                                  "total_usage": 100,
                                  "unique_usage": 10,
                                  "tags": ["test"],
                                  "programmatic_descriptions": ['test'],
                                  "badges": ["badge1"],
                                  'schema_description': 'schema description'
                                  }

        result = test_obj.to_json()
        results = result.split("\n")

        # verify two new line characters in result
        self.assertEqual(len(results), 2, "Result from to_json() function doesn't have a newline!")
        self.assertDictEqual(json.loads(results[0]), expected_document_dict)
