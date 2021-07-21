# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import unittest

from databuilder.models.graph_serializable import (
    RELATION_END_KEY, RELATION_END_LABEL, RELATION_REVERSE_TYPE, RELATION_START_KEY, RELATION_START_LABEL,
    RELATION_TYPE,
)
from databuilder.models.query import QueryMetadata
from databuilder.models.table_metadata import ColumnMetadata, TableMetadata
from databuilder.models.user import User
from databuilder.serializers import neo4_serializer


class TestQuery(unittest.TestCase):

    def setUp(self) -> None:
        self.maxDiff = None
        super(TestQuery, self).setUp()
        self.user = User(first_name='test_first',
                         last_name='test_last',
                         full_name='test_first test_last',
                         email='test@email.com',
                         github_username='github_test',
                         team_name='test_team',
                         employee_type='FTE',
                         manager_email='test_manager@email.com',
                         slack_id='slack',
                         is_active=True,
                         updated_at=1,
                         role_name='swe')
        self.table_metadata = TableMetadata(
            'hive',
            'gold',
            'test_schema1',
            'test_table1',
            'test_table1',
            [
                ColumnMetadata('test_id1', 'description of test_table1', 'bigint', 0),
                ColumnMetadata('test_id2', 'description of test_id2', 'bigint', 1),
                ColumnMetadata('is_active', None, 'boolean', 2),
                ColumnMetadata('source', 'description of source', 'varchar', 3),
                ColumnMetadata('etl_created_at', 'description of etl_created_at', 'timestamp', 4),
                ColumnMetadata('ds', None, 'varchar', 5)
            ]
        )
        self.sql = "select * from table"
        self.query_metadata = QueryMetadata(sql=self.sql,
                                            tables=[self.table_metadata],
                                            user=self.user)
        self._query_hash = 'da44ff72560e593a8eca9ffcee6a2696'

    def test_get_model_key(self) -> None:
        key = QueryMetadata.get_key(sql_hash=self.query_metadata.sql_hash)
        self.assertEqual(key, self._query_hash)

    def test_create_nodes(self) -> None:
        expected_nodes = [{
            'LABEL': 'Query',
            'KEY': self._query_hash,
            'sql': self.sql
        }]

        actual = []
        node = self.query_metadata.create_next_node()
        while node:
            serialized_node = neo4_serializer.serialize_node(node)
            actual.append(serialized_node)
            node = self.query_metadata.create_next_node()

        self.assertEqual(actual, expected_nodes)

    def test_create_relation(self) -> None:
        actual = []
        relation = self.query_metadata.create_next_relation()
        while relation:
            serialized_relation = neo4_serializer.serialize_relationship(relation)
            actual.append(serialized_relation)
            relation = self.query_metadata.create_next_relation()

        expected_relations = [
            {
                RELATION_START_KEY: 'hive://gold.test_schema1/test_table1',
                RELATION_START_LABEL: TableMetadata.TABLE_NODE_LABEL,
                RELATION_END_KEY: self._query_hash,
                RELATION_END_LABEL: QueryMetadata.NODE_LABEL,
                RELATION_TYPE: QueryMetadata.TABLE_QUERY_RELATION_TYPE,
                RELATION_REVERSE_TYPE: QueryMetadata.INVERSE_TABLE_QUERY_RELATION_TYPE
            },
            {
                RELATION_START_KEY: 'test@email.com',
                RELATION_START_LABEL: User.USER_NODE_LABEL,
                RELATION_END_KEY: self._query_hash,
                RELATION_END_LABEL: QueryMetadata.NODE_LABEL,
                RELATION_TYPE: QueryMetadata.USER_QUERY_RELATION_TYPE,
                RELATION_REVERSE_TYPE: QueryMetadata.INVERSE_USER_QUERY_RELATION_TYPE
            }
        ]

        self.assertEquals(expected_relations, actual)

    def test_keys_of_query_containing_strings_with_spaces(self) -> None:
        query_metadata1 = QueryMetadata(sql="select * from table a where a.field == 'xyz'",
                                        tables=[self.table_metadata])

        query_metadata2 = QueryMetadata(sql="select * from table a where a.field == 'x y z'",
                                        tables=[self.table_metadata])

        self.assertNotEqual(query_metadata1.get_key_self(), query_metadata2.get_key_self())

    def test_keys_of_query_containing_strings_with_mixed_case(self) -> None:
        query_metadata1 = QueryMetadata(sql="select * from table a where a.field == 'x Y z'",
                                        tables=[self.table_metadata])

        query_metadata2 = QueryMetadata(sql="select * from table a where a.field == 'x y z'",
                                        tables=[self.table_metadata])

        self.assertNotEqual(query_metadata1.get_key_self(), query_metadata2.get_key_self())
