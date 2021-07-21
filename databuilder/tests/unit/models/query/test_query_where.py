# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import unittest

from databuilder.models.graph_serializable import (
    RELATION_END_KEY, RELATION_END_LABEL, RELATION_REVERSE_TYPE, RELATION_START_KEY, RELATION_START_LABEL,
    RELATION_TYPE,
)
from databuilder.models.query.query import QueryMetadata
from databuilder.models.query.query_where import QueryWhereMetadata
from databuilder.models.table_metadata import ColumnMetadata, TableMetadata
from databuilder.serializers import neo4_serializer


class TestQueryWhere(unittest.TestCase):

    def setUp(self) -> None:
        super(TestQueryWhere, self).setUp()
        # Display full diffs
        self.maxDiff = None
        self.table_metadata = TableMetadata(
            'hive',
            'gold',
            'test_schema1',
            'test_table1',
            'test_table1',
            [
                ColumnMetadata('field', '', '', 0),
            ]
        )
        self.query_metadata = QueryMetadata(sql="select * from table a where a.field > 3",
                                            tables=[self.table_metadata])

        self.query_where_metadata = QueryWhereMetadata(tables=[self.table_metadata],
                                                       where_clause='a.field > 3',
                                                       left_arg='field',
                                                       right_arg='3',
                                                       operator='>',
                                                       query_metadata=self.query_metadata)
        self._expected_key_hash = '795a2a16184c09b88ae518cd5230cfb5-be8634550905b354508dc8aba8008c14'

    def test_get_model_key(self) -> None:
        key = QueryWhereMetadata.get_key(table_hash=self.query_where_metadata._table_hash,
                                         where_hash=self.query_where_metadata._where_hash)
        self.assertEqual(key, self._expected_key_hash)

    def test_create_nodes(self) -> None:
        expected_nodes = [{
            'LABEL': 'Where',
            'KEY': self._expected_key_hash,
            'left_arg': 'field',
            'operator': '>',
            'right_arg': '3',
            'where_clause': 'a.field > 3'
        }]

        actual = []
        node = self.query_where_metadata.create_next_node()
        while node:
            serialized_node = neo4_serializer.serialize_node(node)
            actual.append(serialized_node)
            node = self.query_where_metadata.create_next_node()

        self.assertEqual(actual, expected_nodes)

    def test_create_relation(self) -> None:
        actual = []
        relation = self.query_where_metadata.create_next_relation()
        while relation:
            serialized_relation = neo4_serializer.serialize_relationship(relation)
            actual.append(serialized_relation)
            relation = self.query_where_metadata.create_next_relation()

        expected_relations = [
            {
                RELATION_START_KEY: 'hive://gold.test_schema1/test_table1/field',
                RELATION_START_LABEL: ColumnMetadata.COLUMN_NODE_LABEL,
                RELATION_END_KEY: self._expected_key_hash,
                RELATION_END_LABEL: QueryWhereMetadata.NODE_LABEL,
                RELATION_TYPE: QueryWhereMetadata.COLUMN_WHERE_RELATION_TYPE,
                RELATION_REVERSE_TYPE: QueryWhereMetadata.INVERSE_COLUMN_WHERE_RELATION_TYPE
            },
            {
                RELATION_START_KEY: self.query_metadata.get_key_self(),
                RELATION_START_LABEL: QueryMetadata.NODE_LABEL,
                RELATION_END_KEY: self.query_where_metadata.get_key_self(),
                RELATION_END_LABEL: QueryWhereMetadata.NODE_LABEL,
                RELATION_TYPE: QueryWhereMetadata.QUERY_WHERE_RELATION_TYPE,
                RELATION_REVERSE_TYPE: QueryWhereMetadata.INVERSE_QUERY_WHERE_RELATION_TYPE
            }
        ]
        self.assertEquals(expected_relations, actual)
