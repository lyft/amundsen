# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import unittest

from pyhocon import ConfigFactory

from databuilder.extractor.bigquery_usage_extractor import TableColumnUsageTuple
from databuilder.models.table_column_usage import TableColumnUsage
from databuilder.transformer.bigquery_usage_transformer import BigqueryUsageTransformer


class TestBigQueryUsageTransform(unittest.TestCase):

    DATABASE = 'bigquery'
    CLUSTER = 'your-project-here'
    DATASET = 'dataset'
    TABLE = 'table'
    COLUMN = '*'
    EMAIL = 'your-user-here@test.com'
    READ_COUNT = 305
    TABLE_KEY = 'bigquery://your-project-here.dataset/table'

    def test_transform_function(self) -> None:
        config = ConfigFactory.from_dict({})

        transformer = BigqueryUsageTransformer()
        transformer.init(config)

        key = TableColumnUsageTuple(database=TestBigQueryUsageTransform.DATABASE,
                                    cluster=TestBigQueryUsageTransform.CLUSTER,
                                    schema=TestBigQueryUsageTransform.DATASET,
                                    table=TestBigQueryUsageTransform.TABLE,
                                    column=TestBigQueryUsageTransform.COLUMN,
                                    email=TestBigQueryUsageTransform.EMAIL)

        t1 = (key, TestBigQueryUsageTransform.READ_COUNT)
        xformed = transformer.transform(t1)

        assert xformed is not None
        self.assertIsInstance(xformed, TableColumnUsage)
        col_readers = list(xformed.col_readers)
        self.assertEqual(len(col_readers), 1)
        col_reader = col_readers[0]
        self.assertEqual(col_reader.start_label, 'Table')
        self.assertEqual(col_reader.start_key, TestBigQueryUsageTransform.TABLE_KEY)
        self.assertEqual(col_reader.user_email, TestBigQueryUsageTransform.EMAIL)
        self.assertEqual(col_reader.read_count, TestBigQueryUsageTransform.READ_COUNT)

    def test_scope(self) -> None:
        config = ConfigFactory.from_dict({})

        transformer = BigqueryUsageTransformer()
        transformer.init(config)

        self.assertEqual(transformer.get_scope(), 'transformer.bigquery_usage')
