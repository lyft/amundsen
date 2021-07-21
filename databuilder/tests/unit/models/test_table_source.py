# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import unittest
from unittest.mock import ANY

from databuilder.models.graph_serializable import (
    RELATION_END_KEY, RELATION_END_LABEL, RELATION_REVERSE_TYPE, RELATION_START_KEY, RELATION_START_LABEL,
    RELATION_TYPE,
)
from databuilder.models.table_source import TableSource
from databuilder.serializers import (
    mysql_serializer, neo4_serializer, neptune_serializer,
)
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
SOURCE = '/etl/sql/file.py'


class TestTableSource(unittest.TestCase):

    def setUp(self) -> None:
        super(TestTableSource, self).setUp()
        self.table_source = TableSource(db_name='hive',
                                        schema=SCHEMA,
                                        table_name=TABLE,
                                        cluster=CLUSTER,
                                        source=SOURCE)

        self.start_key = f'{DB}://{CLUSTER}.{SCHEMA}/{TABLE}/_source'
        self.end_key = f'{DB}://{CLUSTER}.{SCHEMA}/{TABLE}'

    def test_get_source_model_key(self) -> None:
        source = self.table_source.get_source_model_key()
        self.assertEqual(source, f'{DB}://{CLUSTER}.{SCHEMA}/{TABLE}/_source')

    def test_get_metadata_model_key(self) -> None:
        metadata = self.table_source.get_metadata_model_key()
        self.assertEqual(metadata, 'hive://default.base/test')

    def test_create_nodes(self) -> None:
        expected_nodes = [{
            'LABEL': 'Source',
            'KEY': f'{DB}://{CLUSTER}.{SCHEMA}/{TABLE}/_source',
            'source': SOURCE,
            'source_type': 'github'
        }]

        actual = []
        node = self.table_source.create_next_node()
        while node:
            serialized_node = neo4_serializer.serialize_node(node)
            actual.append(serialized_node)
            node = self.table_source.create_next_node()

        self.assertEqual(expected_nodes, actual)

    def test_create_relation(self) -> None:
        expected_relations = [{
            RELATION_START_KEY: self.start_key,
            RELATION_START_LABEL: TableSource.LABEL,
            RELATION_END_KEY: self.end_key,
            RELATION_END_LABEL: 'Table',
            RELATION_TYPE: TableSource.SOURCE_TABLE_RELATION_TYPE,
            RELATION_REVERSE_TYPE: TableSource.TABLE_SOURCE_RELATION_TYPE
        }]

        actual = []
        relation = self.table_source.create_next_relation()
        while relation:
            serialized_relation = neo4_serializer.serialize_relationship(relation)
            actual.append(serialized_relation)
            relation = self.table_source.create_next_relation()

        self.assertEqual(expected_relations, actual)

    def test_create_relation_neptune(self) -> None:
        actual = []
        relation = self.table_source.create_next_relation()
        while relation:
            serialized_relation = neptune_serializer.convert_relationship(relation)
            actual.append(serialized_relation)
            relation = self.table_source.create_next_relation()

        expected = [
            [
                {
                    NEPTUNE_HEADER_ID: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                        from_vertex_id="Source:" + self.start_key,
                        to_vertex_id="Table:" + self.end_key,
                        label=TableSource.SOURCE_TABLE_RELATION_TYPE
                    ),
                    METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                        from_vertex_id="Source:" + self.start_key,
                        to_vertex_id="Table:" + self.end_key,
                        label=TableSource.SOURCE_TABLE_RELATION_TYPE
                    ),
                    NEPTUNE_RELATIONSHIP_HEADER_FROM: "Source:" + self.start_key,
                    NEPTUNE_RELATIONSHIP_HEADER_TO: "Table:" + self.end_key,
                    NEPTUNE_HEADER_LABEL: TableSource.SOURCE_TABLE_RELATION_TYPE,
                    NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
                    NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB
                },
                {
                    NEPTUNE_HEADER_ID: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                        from_vertex_id="Table:" + self.end_key,
                        to_vertex_id="Source:" + self.start_key,
                        label=TableSource.TABLE_SOURCE_RELATION_TYPE
                    ),
                    METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                        from_vertex_id="Table:" + self.end_key,
                        to_vertex_id="Source:" + self.start_key,
                        label=TableSource.TABLE_SOURCE_RELATION_TYPE
                    ),
                    NEPTUNE_RELATIONSHIP_HEADER_FROM: "Table:" + self.end_key,
                    NEPTUNE_RELATIONSHIP_HEADER_TO: "Source:" + self.start_key,
                    NEPTUNE_HEADER_LABEL: TableSource.TABLE_SOURCE_RELATION_TYPE,
                    NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
                    NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB
                }
            ]
        ]

        self.assertListEqual(expected, actual)

    def test_create_records(self) -> None:
        expected = [{
            'rk': self.table_source.get_source_model_key(),
            'source': self.table_source.source,
            'source_type': self.table_source.source_type,
            'table_rk': self.table_source.get_metadata_model_key()
        }]

        actual = []
        record = self.table_source.create_next_record()
        while record:
            serialized_record = mysql_serializer.serialize_record(record)
            actual.append(serialized_record)
            record = self.table_source.create_next_record()

        self.assertEqual(expected, actual)
