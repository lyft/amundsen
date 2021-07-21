# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import unittest
from unittest.mock import ANY

from databuilder.models.graph_serializable import (
    RELATION_END_KEY, RELATION_END_LABEL, RELATION_REVERSE_TYPE, RELATION_START_KEY, RELATION_START_LABEL,
    RELATION_TYPE,
)
from databuilder.models.table_lineage import TableLineage
from databuilder.serializers import neo4_serializer, neptune_serializer
from databuilder.serializers.neptune_serializer import (
    METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT, NEPTUNE_CREATION_TYPE_JOB,
    NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT, NEPTUNE_HEADER_ID, NEPTUNE_HEADER_LABEL,
    NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT, NEPTUNE_RELATIONSHIP_HEADER_FROM,
    NEPTUNE_RELATIONSHIP_HEADER_TO,
)

DB = 'hive'
SCHEMA = 'base'
TABLE = 'test'
CLUSTER = 'default'


class TestTableLineage(unittest.TestCase):

    def setUp(self) -> None:
        super(TestTableLineage, self).setUp()
        self.table_lineage = TableLineage(table_key=f'{DB}://{CLUSTER}.{SCHEMA}/{TABLE}',
                                          downstream_deps=['hive://default.test_schema/test_table1',
                                                           'hive://default.test_schema/test_table2'])

        self.start_key = f'{DB}://{CLUSTER}.{SCHEMA}/{TABLE}'
        self.end_key1 = f'{DB}://{CLUSTER}.test_schema/test_table1'
        self.end_key2 = f'{DB}://{CLUSTER}.test_schema/test_table2'

    def test_create_nodes(self) -> None:
        actual = []
        node = self.table_lineage.create_next_node()
        while node:
            serialized_node = neo4_serializer.serialize_node(node)
            actual.append(serialized_node)
            node = self.table_lineage.create_next_node()

        self.assertEqual(len(actual), 0)

    def test_create_relation(self) -> None:
        expected_relations = [
            {
                RELATION_START_KEY: self.start_key,
                RELATION_START_LABEL: 'Table',
                RELATION_END_KEY: self.end_key1,
                RELATION_END_LABEL: 'Table',
                RELATION_TYPE: TableLineage.ORIGIN_DEPENDENCY_RELATION_TYPE,
                RELATION_REVERSE_TYPE: TableLineage.DEPENDENCY_ORIGIN_RELATION_TYPE
            },
            {
                RELATION_START_KEY: self.start_key,
                RELATION_START_LABEL: 'Table',
                RELATION_END_KEY: self.end_key2,
                RELATION_END_LABEL: 'Table',
                RELATION_TYPE: TableLineage.ORIGIN_DEPENDENCY_RELATION_TYPE,
                RELATION_REVERSE_TYPE: TableLineage.DEPENDENCY_ORIGIN_RELATION_TYPE
            }
        ]

        actual = []
        relation = self.table_lineage.create_next_relation()
        while relation:
            serialized_relation = neo4_serializer.serialize_relationship(relation)
            actual.append(serialized_relation)
            relation = self.table_lineage.create_next_relation()

        self.assertEqual(actual, expected_relations)

    def test_create_relation_neptune(self) -> None:
        expected = [
            [
                {
                    NEPTUNE_HEADER_ID: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                        from_vertex_id='Table:' + self.start_key,
                        to_vertex_id='Table:' + self.end_key1,
                        label=TableLineage.ORIGIN_DEPENDENCY_RELATION_TYPE,
                    ),
                    METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                        from_vertex_id='Table:' + self.start_key,
                        to_vertex_id='Table:' + self.end_key1,
                        label=TableLineage.ORIGIN_DEPENDENCY_RELATION_TYPE,
                    ),
                    NEPTUNE_RELATIONSHIP_HEADER_FROM: 'Table:' + self.start_key,
                    NEPTUNE_RELATIONSHIP_HEADER_TO: 'Table:' + self.end_key1,
                    NEPTUNE_HEADER_LABEL: TableLineage.ORIGIN_DEPENDENCY_RELATION_TYPE,
                    NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
                    NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB
                },
                {
                    NEPTUNE_HEADER_ID: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                        from_vertex_id='Table:' + self.end_key1,
                        to_vertex_id='Table:' + self.start_key,
                        label=TableLineage.DEPENDENCY_ORIGIN_RELATION_TYPE
                    ),
                    METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                        from_vertex_id='Table:' + self.end_key1,
                        to_vertex_id='Table:' + self.start_key,
                        label=TableLineage.DEPENDENCY_ORIGIN_RELATION_TYPE
                    ),
                    NEPTUNE_RELATIONSHIP_HEADER_FROM: 'Table:' + self.end_key1,
                    NEPTUNE_RELATIONSHIP_HEADER_TO: 'Table:' + self.start_key,
                    NEPTUNE_HEADER_LABEL: TableLineage.DEPENDENCY_ORIGIN_RELATION_TYPE,
                    NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
                    NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB
                }
            ],
            [
                {
                    NEPTUNE_HEADER_ID: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                        from_vertex_id='Table:' + self.start_key,
                        to_vertex_id='Table:' + self.end_key2,
                        label=TableLineage.ORIGIN_DEPENDENCY_RELATION_TYPE,
                    ),
                    METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                        from_vertex_id='Table:' + self.start_key,
                        to_vertex_id='Table:' + self.end_key2,
                        label=TableLineage.ORIGIN_DEPENDENCY_RELATION_TYPE,
                    ),
                    NEPTUNE_RELATIONSHIP_HEADER_FROM: 'Table:' + self.start_key,
                    NEPTUNE_RELATIONSHIP_HEADER_TO: 'Table:' + self.end_key2,
                    NEPTUNE_HEADER_LABEL: TableLineage.ORIGIN_DEPENDENCY_RELATION_TYPE,
                    NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
                    NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB
                },
                {
                    NEPTUNE_HEADER_ID: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                        from_vertex_id='Table:' + self.end_key2,
                        to_vertex_id='Table:' + self.start_key,
                        label=TableLineage.DEPENDENCY_ORIGIN_RELATION_TYPE
                    ),
                    METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                        from_vertex_id='Table:' + self.end_key2,
                        to_vertex_id='Table:' + self.start_key,
                        label=TableLineage.DEPENDENCY_ORIGIN_RELATION_TYPE
                    ),
                    NEPTUNE_RELATIONSHIP_HEADER_FROM: 'Table:' + self.end_key2,
                    NEPTUNE_RELATIONSHIP_HEADER_TO: 'Table:' + self.start_key,
                    NEPTUNE_HEADER_LABEL: TableLineage.DEPENDENCY_ORIGIN_RELATION_TYPE,
                    NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
                    NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB
                }
            ]
        ]

        actual = []
        relation = self.table_lineage.create_next_relation()
        while relation:
            serialized_relation = neptune_serializer.convert_relationship(relation)
            actual.append(serialized_relation)
            relation = self.table_lineage.create_next_relation()

        self.assertEqual(actual, expected)
