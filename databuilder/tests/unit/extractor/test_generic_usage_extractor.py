# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import logging
import unittest

from mock import MagicMock, patch
from pyhocon import ConfigFactory

from databuilder.extractor.generic_usage_extractor import GenericUsageExtractor
from databuilder.extractor.sql_alchemy_extractor import SQLAlchemyExtractor
from databuilder.models.table_column_usage import ColumnReader, TableColumnUsage


class TestGenericUsageExtractor(unittest.TestCase):
    def setUp(self) -> None:
        logging.basicConfig(level=logging.INFO)

        config_dict = {
            f'extractor.sqlalchemy.{SQLAlchemyExtractor.CONN_STRING}': 'TEST_CONNECTION',
            f'extractor.generic_usage.{GenericUsageExtractor.POPULARITY_TABLE_DATABASE}': 'WhateverNameOfYourDb',
            f'extractor.generic_usage.{GenericUsageExtractor.POPULARTIY_TABLE_SCHEMA}': 'WhateverNameOfYourSchema',
            f'extractor.generic_usage.{GenericUsageExtractor.POPULARITY_TABLE_NAME}': 'WhateverNameOfYourTable',
        }
        self.conf = ConfigFactory.from_dict(config_dict)

    def test_extraction_with_empty_query_result(self) -> None:
        """
        Test Extraction with empty result from query
        """
        with patch.object(SQLAlchemyExtractor, '_get_connection'):
            extractor = GenericUsageExtractor()
            extractor.init(self.conf)

            results = extractor.extract()
            self.assertEqual(results, None)

    def test_extraction(self) -> None:
        with patch.object(SQLAlchemyExtractor, '_get_connection') as mock_connection:
            connection = MagicMock()
            mock_connection.return_value = connection
            sql_execute = MagicMock()
            connection.execute = sql_execute

            sql_execute.return_value = [{
                'database': 'gold',
                'schema': 'scm',
                'name': 'foo',
                'user_email': 'john@example.com',
                'read_count': 1
            }]

            expected = TableColumnUsage(
                col_readers=[
                    ColumnReader(
                        database='snowflake',
                        cluster='gold',
                        schema='scm',
                        table='foo',
                        column='*',
                        user_email='john@example.com',
                        read_count=1
                    )
                ]
            )

            extractor = GenericUsageExtractor()
            extractor.init(self.conf)
            actual = extractor.extract()
            self.assertEqual(expected.__repr__(), actual.__repr__())
            self.assertIsNone(extractor.extract())


class TestGenericUsageExtractorWithWhereClause(unittest.TestCase):
    def setUp(self) -> None:
        logging.basicConfig(level=logging.INFO)
        self.where_clause_suffix = """
        where user_email != 'wrong_user@email.com'
        """

        config_dict = {
            GenericUsageExtractor.WHERE_CLAUSE_SUFFIX_KEY: self.where_clause_suffix,
            f'extractor.sqlalchemy.{SQLAlchemyExtractor.CONN_STRING}':
                'TEST_CONNECTION'
        }
        self.conf = ConfigFactory.from_dict(config_dict)

    def test_sql_statement(self) -> None:
        """
        Test Extraction with empty result from query
        """
        with patch.object(SQLAlchemyExtractor, '_get_connection'):
            extractor = GenericUsageExtractor()
            extractor.init(self.conf)
            self.assertTrue(self.where_clause_suffix in extractor.sql_stmt)


if __name__ == '__main__':
    unittest.main()
