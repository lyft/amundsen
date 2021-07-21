# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import unittest
from unittest.mock import ANY

from databuilder.models.graph_serializable import (
    NODE_KEY, NODE_LABEL, RELATION_END_KEY, RELATION_END_LABEL, RELATION_REVERSE_TYPE, RELATION_START_KEY,
    RELATION_START_LABEL, RELATION_TYPE,
)
from databuilder.models.table_stats import TableColumnStats
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


class TestTableStats(unittest.TestCase):

    def setUp(self) -> None:
        super(TestTableStats, self).setUp()
        self.table_stats = TableColumnStats(table_name='base.test',
                                            col_name='col',
                                            stat_name='avg',
                                            stat_val='1',
                                            start_epoch='1',
                                            end_epoch='2',)

        self.expected_node_results = [{
            NODE_KEY: 'hive://gold.base/test/col/avg/',
            NODE_LABEL: 'Stat',
            'stat_val': '1',
            'stat_type': 'avg',
            'start_epoch': '1',
            'end_epoch': '2',
        }]

        self.expected_relation_results = [{
            RELATION_START_KEY: 'hive://gold.base/test/col/avg/',
            RELATION_START_LABEL: 'Stat',
            RELATION_END_KEY: 'hive://gold.base/test/col',
            RELATION_END_LABEL: 'Column',
            RELATION_TYPE: 'STAT_OF',
            RELATION_REVERSE_TYPE: 'STAT'
        }]

    def test_get_table_stat_model_key(self) -> None:
        table_stats = self.table_stats.get_table_stat_model_key()
        self.assertEqual(table_stats, 'hive://gold.base/test/col/avg/')

    def test_get_col_key(self) -> None:
        metadata = self.table_stats.get_col_key()
        self.assertEqual(metadata, 'hive://gold.base/test/col')

    def test_create_nodes(self) -> None:
        actual = []
        node = self.table_stats.create_next_node()
        while node:
            serialized_node = neo4_serializer.serialize_node(node)
            actual.append(serialized_node)
            node = self.table_stats.create_next_node()

        self.assertEqual(actual, self.expected_node_results)

    def test_create_relation(self) -> None:
        actual = []
        relation = self.table_stats.create_next_relation()
        while relation:
            serialized_relation = neo4_serializer.serialize_relationship(relation)
            actual.append(serialized_relation)
            relation = self.table_stats.create_next_relation()

        self.assertEqual(actual, self.expected_relation_results)

    def test_create_nodes_neptune(self) -> None:
        actual = []
        next_node = self.table_stats.create_next_node()
        while next_node:
            serialized_node = neptune_serializer.convert_node(next_node)
            actual.append(serialized_node)
            next_node = self.table_stats.create_next_node()

        expected_neptune_nodes = [{
            NEPTUNE_HEADER_ID: 'Stat:hive://gold.base/test/col/avg/',
            METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: 'hive://gold.base/test/col/avg/',
            NEPTUNE_HEADER_LABEL: 'Stat',
            NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
            NEPTUNE_CREATION_TYPE_NODE_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB,
            'stat_val:String(single)': '1',
            'stat_type:String(single)': 'avg',
            'start_epoch:String(single)': '1',
            'end_epoch:String(single)': '2',
        }]

        self.assertEqual(actual, expected_neptune_nodes)

    def test_create_relation_neptune(self) -> None:
        self.expected_relation_result = {
            RELATION_START_KEY: 'hive://gold.base/test/col/avg/',
            RELATION_START_LABEL: 'Stat',
            RELATION_END_KEY: 'hive://gold.base/test/col',
            RELATION_END_LABEL: 'Column',
            RELATION_TYPE: 'STAT_OF',
            RELATION_REVERSE_TYPE: 'STAT'
        }

        expected = [
            [
                {
                    NEPTUNE_HEADER_ID: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                        from_vertex_id='Stat:hive://gold.base/test/col/avg/',
                        to_vertex_id='Column:hive://gold.base/test/col',
                        label='STAT_OF'
                    ),
                    METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                        from_vertex_id='Stat:hive://gold.base/test/col/avg/',
                        to_vertex_id='Column:hive://gold.base/test/col',
                        label='STAT_OF'
                    ),
                    NEPTUNE_RELATIONSHIP_HEADER_FROM: 'Stat:hive://gold.base/test/col/avg/',
                    NEPTUNE_RELATIONSHIP_HEADER_TO: 'Column:hive://gold.base/test/col',
                    NEPTUNE_HEADER_LABEL: 'STAT_OF',
                    NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
                    NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB
                },
                {
                    NEPTUNE_HEADER_ID: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                        from_vertex_id='Column:hive://gold.base/test/col',
                        to_vertex_id='Stat:hive://gold.base/test/col/avg/',
                        label='STAT'
                    ),
                    METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                        from_vertex_id='Column:hive://gold.base/test/col',
                        to_vertex_id='Stat:hive://gold.base/test/col/avg/',
                        label='STAT'
                    ),
                    NEPTUNE_RELATIONSHIP_HEADER_FROM: 'Column:hive://gold.base/test/col',
                    NEPTUNE_RELATIONSHIP_HEADER_TO: 'Stat:hive://gold.base/test/col/avg/',
                    NEPTUNE_HEADER_LABEL: 'STAT',
                    NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
                    NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB
                }
            ]
        ]

        actual = []
        next_relation = self.table_stats.create_next_relation()
        while next_relation:
            serialized_relation = neptune_serializer.convert_relationship(next_relation)
            actual.append(serialized_relation)
            next_relation = self.table_stats.create_next_relation()

        self.assertListEqual(actual, expected)

    def test_create_records(self) -> None:
        expected = [{
            'rk': 'hive://gold.base/test/col/avg/',
            'stat_val': '1',
            'stat_type': 'avg',
            'start_epoch': '1',
            'end_epoch': '2',
            'column_rk': 'hive://gold.base/test/col'
        }]

        actual = []
        record = self.table_stats.create_next_record()
        while record:
            serialized_record = mysql_serializer.serialize_record(record)
            actual.append(serialized_record)
            record = self.table_stats.create_next_record()

        self.assertEqual(actual, expected)
