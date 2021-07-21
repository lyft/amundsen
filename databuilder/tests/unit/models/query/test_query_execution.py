
# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import unittest

from databuilder.models.graph_serializable import (
    RELATION_END_KEY, RELATION_END_LABEL, RELATION_REVERSE_TYPE, RELATION_START_KEY, RELATION_START_LABEL,
    RELATION_TYPE,
)
from databuilder.models.query.query import QueryMetadata
from databuilder.models.query.query_execution import QueryExecutionsMetadata
from databuilder.models.table_metadata import ColumnMetadata, TableMetadata
from databuilder.serializers import neo4_serializer


class TestQueryExecution(unittest.TestCase):

    def setUp(self) -> None:
        super(TestQueryExecution, self).setUp()
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

        self.query_join_metadata = QueryExecutionsMetadata(query_metadata=self.query_metadata,
                                                           start_time=10,
                                                           execution_count=7)
        self._expected_key = '748c28f86de411b1d2b9deb6ae105eba-10'

    def test_get_model_key(self) -> None:
        key = QueryExecutionsMetadata.get_key(query_key=self.query_metadata.get_key_self(), start_time=10)

        self.assertEqual(key, self._expected_key)

    def test_create_nodes(self) -> None:
        expected_nodes = [{
            'LABEL': QueryExecutionsMetadata.NODE_LABEL,
            'KEY': self._expected_key,
            'execution_count:UNQUOTED': 7,
            'start_time:UNQUOTED': 10,
            'window_duration': 'daily'
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

        self.maxDiff = None
        expected_relations = [
            {
                RELATION_END_KEY: self._expected_key,
                RELATION_END_LABEL: QueryExecutionsMetadata.NODE_LABEL,
                RELATION_REVERSE_TYPE: QueryExecutionsMetadata.INVERSE_QUERY_EXECUTION_RELATION_TYPE,
                RELATION_START_KEY: self.query_metadata.get_key_self(),
                RELATION_START_LABEL: QueryMetadata.NODE_LABEL,
                RELATION_TYPE: QueryExecutionsMetadata.QUERY_EXECUTION_RELATION_TYPE
            }
        ]
        self.assertEquals(expected_relations, actual)
