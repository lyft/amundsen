# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import unittest
from unittest.mock import ANY

from databuilder.models.graph_serializable import (
    NODE_KEY, NODE_LABEL, RELATION_END_KEY, RELATION_END_LABEL, RELATION_REVERSE_TYPE, RELATION_START_KEY,
    RELATION_START_LABEL, RELATION_TYPE,
)
from databuilder.models.table_last_updated import TableLastUpdated
from databuilder.models.timestamp import timestamp_constants
from databuilder.serializers import (
    mysql_serializer, neo4_serializer, neptune_serializer,
)
from databuilder.serializers.neptune_serializer import (
    METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT, NEPTUNE_CREATION_TYPE_JOB,
    NEPTUNE_CREATION_TYPE_NODE_PROPERTY_NAME_BULK_LOADER_FORMAT,
    NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT, NEPTUNE_HEADER_ID, NEPTUNE_HEADER_LABEL,
    NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT, NEPTUNE_RELATIONSHIP_HEADER_FROM,
    NEPTUNE_RELATIONSHIP_HEADER_TO,
)


class TestTableLastUpdated(unittest.TestCase):

    def setUp(self) -> None:
        super(TestTableLastUpdated, self).setUp()

        self.tableLastUpdated = TableLastUpdated(table_name='test_table',
                                                 last_updated_time_epoch=25195665,
                                                 schema='default')

        self.expected_node_results = [{
            NODE_KEY: 'hive://gold.default/test_table/timestamp',
            NODE_LABEL: 'Timestamp',
            'last_updated_timestamp:UNQUOTED': 25195665,
            timestamp_constants.TIMESTAMP_PROPERTY + ":UNQUOTED": 25195665,
            'name': 'last_updated_timestamp'
        }]

        self.expected_relation_results = [{
            RELATION_START_KEY: 'hive://gold.default/test_table',
            RELATION_START_LABEL: 'Table',
            RELATION_END_KEY: 'hive://gold.default/test_table/timestamp',
            RELATION_END_LABEL: 'Timestamp',
            RELATION_TYPE: 'LAST_UPDATED_AT',
            RELATION_REVERSE_TYPE: 'LAST_UPDATED_TIME_OF'
        }]

    def test_get_table_model_key(self) -> None:
        table = self.tableLastUpdated.get_table_model_key()
        self.assertEqual(table, 'hive://gold.default/test_table')

    def test_get_last_updated_model_key(self) -> None:
        last_updated = self.tableLastUpdated.get_last_updated_model_key()
        self.assertEqual(last_updated, 'hive://gold.default/test_table/timestamp')

    def test_create_nodes(self) -> None:
        actual = []
        node = self.tableLastUpdated.create_next_node()
        while node:
            serialize_node = neo4_serializer.serialize_node(node)
            actual.append(serialize_node)
            node = self.tableLastUpdated.create_next_node()

        self.assertEqual(actual, self.expected_node_results)

    def test_create_nodes_neptune(self) -> None:
        node_id = TableLastUpdated.LAST_UPDATED_NODE_LABEL + ":" + self.tableLastUpdated.get_last_updated_model_key()
        expected_nodes = [{
            NEPTUNE_HEADER_ID: node_id,
            METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: self.tableLastUpdated.get_last_updated_model_key(),
            NEPTUNE_HEADER_LABEL: TableLastUpdated.LAST_UPDATED_NODE_LABEL,
            NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
            NEPTUNE_CREATION_TYPE_NODE_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB,
            'name:String(single)': 'last_updated_timestamp',
            'last_updated_timestamp:Long(single)': 25195665,
            timestamp_constants.TIMESTAMP_PROPERTY + ":Long(single)": 25195665,
        }]

        actual = []
        next_node = self.tableLastUpdated.create_next_node()
        while next_node:
            next_node_serialized = neptune_serializer.convert_node(next_node)
            actual.append(next_node_serialized)
            next_node = self.tableLastUpdated.create_next_node()

        self.assertEqual(actual, expected_nodes)

    def test_create_relation(self) -> None:
        actual = []
        relation = self.tableLastUpdated.create_next_relation()
        while relation:
            serialized_relation = neo4_serializer.serialize_relationship(relation)
            actual.append(serialized_relation)
            relation = self.tableLastUpdated.create_next_relation()

    def test_create_relation_neptune(self) -> None:
        actual = []
        next_relation = self.tableLastUpdated.create_next_relation()
        while next_relation:
            next_relation_serialized = neptune_serializer.convert_relationship(next_relation)
            actual.append(next_relation_serialized)
            next_relation = self.tableLastUpdated.create_next_relation()

        expected = [
            [
                {
                    NEPTUNE_HEADER_ID: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                        from_vertex_id='Table:hive://gold.default/test_table',
                        to_vertex_id='Timestamp:hive://gold.default/test_table/timestamp',
                        label='LAST_UPDATED_AT'
                    ),
                    METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                        from_vertex_id='Table:hive://gold.default/test_table',
                        to_vertex_id='Timestamp:hive://gold.default/test_table/timestamp',
                        label='LAST_UPDATED_AT'
                    ),
                    NEPTUNE_RELATIONSHIP_HEADER_FROM: 'Table:hive://gold.default/test_table',
                    NEPTUNE_RELATIONSHIP_HEADER_TO: 'Timestamp:hive://gold.default/test_table/timestamp',
                    NEPTUNE_HEADER_LABEL: 'LAST_UPDATED_AT',
                    NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
                    NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB
                },
                {
                    NEPTUNE_HEADER_ID: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                        from_vertex_id='Timestamp:hive://gold.default/test_table/timestamp',
                        to_vertex_id='Table:hive://gold.default/test_table',
                        label='LAST_UPDATED_TIME_OF'
                    ),
                    METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                        from_vertex_id='Timestamp:hive://gold.default/test_table/timestamp',
                        to_vertex_id='Table:hive://gold.default/test_table',
                        label='LAST_UPDATED_TIME_OF'
                    ),
                    NEPTUNE_RELATIONSHIP_HEADER_FROM: 'Timestamp:hive://gold.default/test_table/timestamp',
                    NEPTUNE_RELATIONSHIP_HEADER_TO: 'Table:hive://gold.default/test_table',
                    NEPTUNE_HEADER_LABEL: 'LAST_UPDATED_TIME_OF',
                    NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
                    NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB
                }
            ]
        ]

        self.assertEqual(actual, expected)

    def test_create_records(self) -> None:
        expected = [{
            'rk': 'hive://gold.default/test_table/timestamp',
            'last_updated_timestamp': 25195665,
            'timestamp': 25195665,
            'name': 'last_updated_timestamp',
            'table_rk': 'hive://gold.default/test_table'
        }]

        actual = []
        record = self.tableLastUpdated.create_next_record()
        while record:
            serialized_record = mysql_serializer.serialize_record(record)
            actual.append(serialized_record)
            record = self.tableLastUpdated.create_next_record()

        self.assertEqual(expected, actual)
