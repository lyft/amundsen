# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import unittest
from unittest.mock import ANY

from databuilder.models.graph_node import GraphNode
from databuilder.models.graph_relationship import GraphRelationship
from databuilder.models.graph_serializable import (
    NODE_KEY, NODE_LABEL, RELATION_END_KEY, RELATION_END_LABEL, RELATION_REVERSE_TYPE, RELATION_START_KEY,
    RELATION_START_LABEL, RELATION_TYPE,
)
from databuilder.models.watermark import Watermark
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

CREATE_TIME = '2017-09-18T00:00:00'
DATABASE = 'DYNAMO'
SCHEMA = 'BASE'
TABLE = 'TEST'
NESTED_PART = 'ds=2017-09-18/feature_id=9'
CLUSTER = 'DEFAULT'
PART_TYPE = 'LOW_WATERMARK'


class TestWatermark(unittest.TestCase):

    def setUp(self) -> None:
        super(TestWatermark, self).setUp()
        self.watermark = Watermark(
            create_time='2017-09-18T00:00:00',
            database=DATABASE,
            schema=SCHEMA,
            table_name=TABLE,
            cluster=CLUSTER,
            part_type=PART_TYPE,
            part_name=NESTED_PART
        )
        self.start_key = f'{DATABASE}://{CLUSTER}.{SCHEMA}/{TABLE}/{PART_TYPE}/'
        self.end_key = f'{DATABASE}://{CLUSTER}.{SCHEMA}/{TABLE}'
        self.expected_node_result = GraphNode(
            key=self.start_key,
            label='Watermark',
            attributes={
                'partition_key': 'ds',
                'partition_value': '2017-09-18/feature_id=9',
                'create_time': '2017-09-18T00:00:00'
            }
        )

        self.expected_serialized_node_results = [{
            NODE_KEY: self.start_key,
            NODE_LABEL: 'Watermark',
            'partition_key': 'ds',
            'partition_value': '2017-09-18/feature_id=9',
            'create_time': '2017-09-18T00:00:00'
        }]

        self.expected_relation_result = GraphRelationship(
            start_label='Watermark',
            end_label='Table',
            start_key=self.start_key,
            end_key=self.end_key,
            type='BELONG_TO_TABLE',
            reverse_type='WATERMARK',
            attributes={}
        )

        self.expected_serialized_relation_results = [{
            RELATION_START_KEY: self.start_key,
            RELATION_START_LABEL: 'Watermark',
            RELATION_END_KEY: self.end_key,
            RELATION_END_LABEL: 'Table',
            RELATION_TYPE: 'BELONG_TO_TABLE',
            RELATION_REVERSE_TYPE: 'WATERMARK'
        }]

    def test_get_watermark_model_key(self) -> None:
        watermark = self.watermark.get_watermark_model_key()
        self.assertEqual(watermark, f'{DATABASE}://{CLUSTER}.{SCHEMA}/{TABLE}/{PART_TYPE}/')

    def test_get_metadata_model_key(self) -> None:
        metadata = self.watermark.get_metadata_model_key()
        self.assertEqual(metadata, f'{DATABASE}://{CLUSTER}.{SCHEMA}/{TABLE}')

    def test_create_nodes(self) -> None:
        actual = []
        node = self.watermark.create_next_node()
        while node:
            serialized_node = neo4_serializer.serialize_node(node)
            actual.append(serialized_node)
            node = self.watermark.create_next_node()

        self.assertEqual(actual, self.expected_serialized_node_results)

    def test_create_nodes_neptune(self) -> None:
        expected_serialized_node_results = [{
            NEPTUNE_HEADER_ID: 'Watermark:' + self.start_key,
            METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: self.start_key,
            NEPTUNE_HEADER_LABEL: 'Watermark',
            NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
            NEPTUNE_CREATION_TYPE_NODE_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB,
            'partition_key:String(single)': 'ds',
            'partition_value:String(single)': '2017-09-18/feature_id=9',
            'create_time:String(single)': '2017-09-18T00:00:00'
        }]

        actual = []
        node = self.watermark.create_next_node()
        while node:
            serialized_node = neptune_serializer.convert_node(node)
            actual.append(serialized_node)
            node = self.watermark.create_next_node()

        self.assertEqual(expected_serialized_node_results, actual)

    def test_create_relation(self) -> None:
        actual = []
        relation = self.watermark.create_next_relation()
        while relation:
            serialized_relation = neo4_serializer.serialize_relationship(relation)
            actual.append(serialized_relation)
            relation = self.watermark.create_next_relation()

        self.assertEqual(actual, self.expected_serialized_relation_results)

    def test_create_relation_neptune(self) -> None:
        actual = []
        relation = self.watermark.create_next_relation()
        while relation:
            serialized_relation = neptune_serializer.convert_relationship(relation)
            actual.append(serialized_relation)
            relation = self.watermark.create_next_relation()

        expected = [
            [
                {
                    NEPTUNE_HEADER_ID: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                        from_vertex_id="Watermark:" + self.start_key,
                        to_vertex_id="Table:" + self.end_key,
                        label='BELONG_TO_TABLE'
                    ),
                    METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                        from_vertex_id="Watermark:" + self.start_key,
                        to_vertex_id="Table:" + self.end_key,
                        label='BELONG_TO_TABLE'
                    ),
                    NEPTUNE_RELATIONSHIP_HEADER_FROM: "Watermark:" + self.start_key,
                    NEPTUNE_RELATIONSHIP_HEADER_TO: "Table:" + self.end_key,
                    NEPTUNE_HEADER_LABEL: 'BELONG_TO_TABLE',
                    NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
                    NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB
                },
                {
                    NEPTUNE_HEADER_ID: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                        from_vertex_id="Table:" + self.end_key,
                        to_vertex_id="Watermark:" + self.start_key,
                        label='WATERMARK'
                    ),
                    METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                        from_vertex_id="Table:" + self.end_key,
                        to_vertex_id="Watermark:" + self.start_key,
                        label='WATERMARK'
                    ),
                    NEPTUNE_RELATIONSHIP_HEADER_FROM: "Table:" + self.end_key,
                    NEPTUNE_RELATIONSHIP_HEADER_TO: "Watermark:" + self.start_key,
                    NEPTUNE_HEADER_LABEL: 'WATERMARK',
                    NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
                    NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB
                }
            ]
        ]

        self.assertListEqual(actual, expected)

    def test_create_records(self) -> None:
        expected = [{
            'rk': self.start_key,
            'partition_key': 'ds',
            'partition_value': '2017-09-18/feature_id=9',
            'create_time': '2017-09-18T00:00:00',
            'table_rk': self.end_key
        }]

        actual = []
        record = self.watermark.create_next_record()
        while record:
            serialized_record = mysql_serializer.serialize_record(record)
            actual.append(serialized_record)
            record = self.watermark.create_next_record()

        self.assertEqual(actual, expected)
