# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import logging
import unittest
from collections import OrderedDict
from typing import Any

from cassandra.metadata import ColumnMetadata as CassandraColumnMetadata
from mock import patch
from pyhocon import ConfigFactory

from databuilder.extractor.cassandra_extractor import CassandraExtractor
from databuilder.models.table_metadata import ColumnMetadata, TableMetadata


# patch whole class to avoid actually calling for boto3.client during tests
@patch('cassandra.cluster.Cluster.connect', lambda x: None)
class TestCassandraExtractor(unittest.TestCase):
    def setUp(self) -> None:
        logging.basicConfig(level=logging.INFO)

        self.default_conf = ConfigFactory.from_dict({})

    def test_extraction_with_empty_query_result(self) -> None:
        """
        Test Extraction with empty result from query
        """
        extractor = CassandraExtractor()
        extractor.init(self.default_conf)

        results = extractor.extract()
        self.assertEqual(results, None)

    @patch('databuilder.extractor.cassandra_extractor.CassandraExtractor._get_keyspaces')
    @patch('databuilder.extractor.cassandra_extractor.CassandraExtractor._get_tables')
    @patch('databuilder.extractor.cassandra_extractor.CassandraExtractor._get_columns')
    def test_extraction_with_default_conf(self,
                                          mock_columns: Any,
                                          mock_tables: Any,
                                          mock_keyspaces: Any
                                          ) -> None:
        mock_keyspaces.return_value = {'test_schema': None}
        mock_tables.return_value = {'test_table': None}
        columns_dict = OrderedDict()
        columns_dict['id'] = CassandraColumnMetadata(None, 'id', 'int')
        columns_dict['txt'] = CassandraColumnMetadata(None, 'txt', 'text')
        mock_columns.return_value = columns_dict

        extractor = CassandraExtractor()
        extractor.init(self.default_conf)
        actual = extractor.extract()
        expected = TableMetadata('cassandra', 'gold', 'test_schema', 'test_table', None,
                                 [ColumnMetadata('id', None, 'int', 0),
                                  ColumnMetadata('txt', None, 'text', 1)])
        self.assertEqual(expected.__repr__(), actual.__repr__())
        self.assertIsNone(extractor.extract())

    @patch('databuilder.extractor.cassandra_extractor.CassandraExtractor._get_keyspaces')
    @patch('databuilder.extractor.cassandra_extractor.CassandraExtractor._get_tables')
    @patch('databuilder.extractor.cassandra_extractor.CassandraExtractor._get_columns')
    def test_extraction_with_filter_conf(self,
                                         mock_columns: Any,
                                         mock_tables: Any,
                                         mock_keyspaces: Any
                                         ) -> None:
        mock_keyspaces.return_value = {'test_schema': None}
        mock_tables.return_value = {'test_table': None}
        columns_dict = OrderedDict()
        columns_dict['id'] = CassandraColumnMetadata(None, 'id', 'int')
        columns_dict['txt'] = CassandraColumnMetadata(None, 'txt', 'text')
        mock_columns.return_value = columns_dict

        def filter_function(k: str, t: str) -> bool:
            return False if 'test' in k or 'test' in t else False

        conf = ConfigFactory.from_dict({
            CassandraExtractor.FILTER_FUNCTION_KEY: filter_function
        })

        extractor = CassandraExtractor()
        extractor.init(conf)
        self.assertIsNone(extractor.extract())


if __name__ == '__main__':
    unittest.main()
