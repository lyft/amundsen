# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import unittest

from databuilder.models.graph_serializable import (
    RELATION_END_KEY, RELATION_END_LABEL, RELATION_REVERSE_TYPE, RELATION_START_KEY, RELATION_START_LABEL,
    RELATION_TYPE,
)
from databuilder.models.query.query import QueryMetadata
from databuilder.models.query.query_join import QueryJoinMetadata
from databuilder.models.table_metadata import ColumnMetadata, TableMetadata
from databuilder.serializers import neo4_serializer


class TestQueryJoin(unittest.TestCase):

    def setUp(self) -> None:
        super(TestQueryJoin, self).setUp()
        # Display full diffs
        self.maxDiff = None
        self.tbl1_col = ColumnMetadata('field', '', '', 0)
        self.left_table_metadata = TableMetadata(
            'hive',
            'gold',
            'test_schema1',
            'test_table1',
            'test_table1 desc',
            [self.tbl1_col]
        )
        self.tbl2_col = ColumnMetadata('field', '', '', 0)
        self.right_table_metadata = TableMetadata(
            'hive',
            'gold',
            'test_schema1',
            'test_table2',
            'test_table2 desc',
            [self.tbl2_col]
        )
        self.query_metadata = QueryMetadata(sql="select * from table a where a.field > 3",
                                            tables=[self.left_table_metadata, self.right_table_metadata])

        self.query_join_metadata = QueryJoinMetadata(
            left_table=self.left_table_metadata,
            right_table=self.right_table_metadata,
            left_column=self.tbl1_col,
            right_column=self.tbl2_col,
            join_type='inner join',
            join_operator='=',
            join_sql='test_table1 = join test_table2 on test_tabl1.field = test_table2.field',
            query_metadata=self.query_metadata
        )
        self._expected_key = (
            'inner-join-'
            'hive://gold.test_schema1/test_table1/field-'
            '=-'
            'hive://gold.test_schema1/test_table2/field'
        )

    def test_get_model_key(self) -> None:
        key = QueryJoinMetadata.get_key(left_column_key=self.left_table_metadata._get_col_key(col=self.tbl1_col),
                                        right_column_key=self.right_table_metadata._get_col_key(col=self.tbl2_col),
                                        join_type='inner join',
                                        operator='=')

        self.assertEqual(key, self._expected_key)

    def test_create_nodes(self) -> None:
        expected_nodes = [{
            'LABEL': 'Join',
            'KEY': self._expected_key,
            'join_sql': 'test_table1 = join test_table2 on test_tabl1.field = test_table2.field',
            'join_type': 'inner join',
            'left_cluster': 'gold',
            'left_database': 'hive',
            'left_schema': 'test_schema1',
            'left_table': 'test_table1',
            'left_table_key': 'hive://gold.test_schema1/test_table1',
            'operator': '=',
            'right_cluster': 'gold',
            'right_database': 'hive',
            'right_schema': 'test_schema1',
            'right_table': 'test_table2',
            'right_table_key': 'hive://gold.test_schema1/test_table2'
        }]

        actual = []
        node = self.query_join_metadata.create_next_node()
        while node:
            serialized_node = neo4_serializer.serialize_node(node)
            actual.append(serialized_node)
            node = self.query_join_metadata.create_next_node()

        self.assertEqual(actual, expected_nodes)

    def test_create_relation(self) -> None:
        actual = []
        relation = self.query_join_metadata.create_next_relation()
        while relation:
            serialized_relation = neo4_serializer.serialize_relationship(relation)
            actual.append(serialized_relation)
            relation = self.query_join_metadata.create_next_relation()

        expected_relations = [
            {
                RELATION_END_KEY: self._expected_key,
                RELATION_END_LABEL: QueryJoinMetadata.NODE_LABEL,
                RELATION_REVERSE_TYPE: QueryJoinMetadata.INVERSE_COLUMN_JOIN_RELATION_TYPE,
                RELATION_START_KEY: 'hive://gold.test_schema1/test_table1/field',
                RELATION_START_LABEL: ColumnMetadata.COLUMN_NODE_LABEL,
                RELATION_TYPE: QueryJoinMetadata.COLUMN_JOIN_RELATION_TYPE
            },
            {
                RELATION_END_KEY: self._expected_key,
                RELATION_END_LABEL: QueryJoinMetadata.NODE_LABEL,
                RELATION_REVERSE_TYPE: QueryJoinMetadata.INVERSE_COLUMN_JOIN_RELATION_TYPE,
                RELATION_START_KEY: 'hive://gold.test_schema1/test_table2/field',
                RELATION_START_LABEL: ColumnMetadata.COLUMN_NODE_LABEL,
                RELATION_TYPE: QueryJoinMetadata.COLUMN_JOIN_RELATION_TYPE
            },
            {
                RELATION_END_KEY: self._expected_key,
                RELATION_END_LABEL: QueryJoinMetadata.NODE_LABEL,
                RELATION_REVERSE_TYPE: QueryJoinMetadata.INVERSE_QUERY_JOIN_RELATION_TYPE,
                RELATION_START_KEY: '748c28f86de411b1d2b9deb6ae105eba',
                RELATION_START_LABEL: QueryMetadata.NODE_LABEL,
                RELATION_TYPE: QueryJoinMetadata.QUERY_JOIN_RELATION_TYPE
            }
        ]
        self.assertEquals(expected_relations, actual)
