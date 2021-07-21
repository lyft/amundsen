# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import unittest
from unittest.mock import ANY

from databuilder.models.badge import Badge, BadgeMetadata
from databuilder.models.graph_serializable import (
    NODE_KEY, NODE_LABEL, RELATION_END_KEY, RELATION_END_LABEL, RELATION_REVERSE_TYPE, RELATION_START_KEY,
    RELATION_START_LABEL, RELATION_TYPE,
)
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

db = 'hive'
SCHEMA = 'BASE'
TABLE = 'TEST'
CLUSTER = 'DEFAULT'
badge1 = Badge('badge1', 'column')
badge2 = Badge('badge2', 'column')


class TestBadge(unittest.TestCase):
    def setUp(self) -> None:
        super(TestBadge, self).setUp()
        self.badge_metada = BadgeMetadata(start_label='Column',
                                          start_key='hive://default.base/test/ds',
                                          badges=[badge1, badge2])

    def test_badge_name_category_are_lower_cases(self) -> None:
        uppercase_badge = Badge('BadGe3', 'COLUMN_3')
        self.assertEqual(uppercase_badge.name, 'badge3')
        self.assertEqual(uppercase_badge.category, 'column_3')

    def test_get_badge_key(self) -> None:
        badge_key = self.badge_metada.get_badge_key(badge1.name)
        self.assertEqual(badge_key, badge1.name)

    def test_create_nodes(self) -> None:
        node1 = {
            NODE_KEY: BadgeMetadata.BADGE_KEY_FORMAT.format(badge=badge1.name),
            NODE_LABEL: BadgeMetadata.BADGE_NODE_LABEL,
            BadgeMetadata.BADGE_CATEGORY: badge1.category
        }
        node2 = {
            NODE_KEY: BadgeMetadata.BADGE_KEY_FORMAT.format(badge=badge2.name),
            NODE_LABEL: BadgeMetadata.BADGE_NODE_LABEL,
            BadgeMetadata.BADGE_CATEGORY: badge2.category
        }
        expected = [node1, node2]

        actual = []
        node = self.badge_metada.create_next_node()
        while node:
            serialized_node = neo4_serializer.serialize_node(node)
            actual.append(serialized_node)
            node = self.badge_metada.create_next_node()

        self.assertEqual(expected, actual)

    def test_create_nodes_neptune(self) -> None:
        actual = []
        node = self.badge_metada.create_next_node()
        while node:
            serialized_node = neptune_serializer.convert_node(node)
            actual.append(serialized_node)
            node = self.badge_metada.create_next_node()
        node_key_1 = BadgeMetadata.BADGE_KEY_FORMAT.format(badge=badge1.name)
        node_id_1 = BadgeMetadata.BADGE_NODE_LABEL + ":" + node_key_1
        expected_node1 = {
            NEPTUNE_HEADER_ID: node_id_1,
            METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: node_key_1,
            NEPTUNE_HEADER_LABEL: BadgeMetadata.BADGE_NODE_LABEL,
            NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
            NEPTUNE_CREATION_TYPE_NODE_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB,
            BadgeMetadata.BADGE_CATEGORY + ':String(single)': badge1.category
        }
        node_key_2 = BadgeMetadata.BADGE_KEY_FORMAT.format(badge=badge2.name)
        node_id_2 = BadgeMetadata.BADGE_NODE_LABEL + ":" + node_key_2
        expected_node2 = {
            NEPTUNE_HEADER_ID: node_id_2,
            METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: node_key_2,
            NEPTUNE_HEADER_LABEL: BadgeMetadata.BADGE_NODE_LABEL,
            NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
            NEPTUNE_CREATION_TYPE_NODE_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB,
            BadgeMetadata.BADGE_CATEGORY + ':String(single)': badge2.category
        }
        expected = [expected_node1, expected_node2]

        self.assertEqual(expected, actual)

    def test_bad_entity_label(self) -> None:
        user_label = 'User'
        table_key = 'hive://default.base/test'
        self.assertRaises(Exception,
                          BadgeMetadata,
                          start_label=user_label,
                          start_key=table_key,
                          badges=[badge1, badge2])

    def test_create_relation(self) -> None:
        actual = []
        relation = self.badge_metada.create_next_relation()
        while relation:
            serialized_relation = neo4_serializer.serialize_relationship(relation)
            actual.append(serialized_relation)
            relation = self.badge_metada.create_next_relation()

        relation1 = {
            RELATION_START_LABEL: self.badge_metada.start_label,
            RELATION_END_LABEL: BadgeMetadata.BADGE_NODE_LABEL,
            RELATION_START_KEY: self.badge_metada.start_key,
            RELATION_END_KEY: BadgeMetadata.get_badge_key(badge1.name),
            RELATION_TYPE: BadgeMetadata.BADGE_RELATION_TYPE,
            RELATION_REVERSE_TYPE: BadgeMetadata.INVERSE_BADGE_RELATION_TYPE,
        }
        relation2 = {
            RELATION_START_LABEL: self.badge_metada.start_label,
            RELATION_END_LABEL: BadgeMetadata.BADGE_NODE_LABEL,
            RELATION_START_KEY: self.badge_metada.start_key,
            RELATION_END_KEY: BadgeMetadata.get_badge_key(badge2.name),
            RELATION_TYPE: BadgeMetadata.BADGE_RELATION_TYPE,
            RELATION_REVERSE_TYPE: BadgeMetadata.INVERSE_BADGE_RELATION_TYPE,
        }
        expected = [relation1, relation2]

        self.assertEqual(expected, actual)

    def test_create_relation_neptune(self) -> None:
        actual = []
        relation = self.badge_metada.create_next_relation()
        while relation:
            serialized_relations = neptune_serializer.convert_relationship(relation)
            actual.append(serialized_relations)
            relation = self.badge_metada.create_next_relation()

        badge_id_1 = BadgeMetadata.BADGE_NODE_LABEL + ':' + BadgeMetadata.get_badge_key(badge1.name)
        badge_id_2 = BadgeMetadata.BADGE_NODE_LABEL + ':' + BadgeMetadata.get_badge_key(badge2.name)
        start_key = self.badge_metada.start_label + ':' + self.badge_metada.start_key

        neptune_forward_expected_1 = {
            NEPTUNE_HEADER_ID: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                from_vertex_id=start_key,
                to_vertex_id=badge_id_1,
                label=BadgeMetadata.BADGE_RELATION_TYPE,
            ),
            METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                from_vertex_id=start_key,
                to_vertex_id=badge_id_1,
                label=BadgeMetadata.BADGE_RELATION_TYPE,
            ),
            NEPTUNE_RELATIONSHIP_HEADER_FROM: start_key,
            NEPTUNE_RELATIONSHIP_HEADER_TO: badge_id_1,
            NEPTUNE_HEADER_LABEL: BadgeMetadata.BADGE_RELATION_TYPE,
            NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
            NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB
        }

        neptune_reversed_expected_1 = {
            NEPTUNE_HEADER_ID: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                from_vertex_id=badge_id_1,
                to_vertex_id=start_key,
                label=BadgeMetadata.INVERSE_BADGE_RELATION_TYPE
            ),
            METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                from_vertex_id=badge_id_1,
                to_vertex_id=start_key,
                label=BadgeMetadata.INVERSE_BADGE_RELATION_TYPE
            ),
            NEPTUNE_RELATIONSHIP_HEADER_FROM: badge_id_1,
            NEPTUNE_RELATIONSHIP_HEADER_TO: start_key,
            NEPTUNE_HEADER_LABEL: BadgeMetadata.INVERSE_BADGE_RELATION_TYPE,
            NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
            NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB
        }

        neptune_forward_expected_2 = {
            NEPTUNE_HEADER_ID: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                from_vertex_id=start_key,
                to_vertex_id=badge_id_2,
                label=BadgeMetadata.BADGE_RELATION_TYPE,
            ),
            METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                from_vertex_id=start_key,
                to_vertex_id=badge_id_2,
                label=BadgeMetadata.BADGE_RELATION_TYPE,
            ),
            NEPTUNE_RELATIONSHIP_HEADER_FROM: start_key,
            NEPTUNE_RELATIONSHIP_HEADER_TO: badge_id_2,
            NEPTUNE_HEADER_LABEL: BadgeMetadata.BADGE_RELATION_TYPE,
            NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
            NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB
        }

        neptune_reversed_expected_2 = {
            NEPTUNE_HEADER_ID: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                from_vertex_id=badge_id_2,
                to_vertex_id=start_key,
                label=BadgeMetadata.INVERSE_BADGE_RELATION_TYPE,
            ),
            METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                from_vertex_id=badge_id_2,
                to_vertex_id=start_key,
                label=BadgeMetadata.INVERSE_BADGE_RELATION_TYPE,
            ),
            NEPTUNE_RELATIONSHIP_HEADER_FROM: badge_id_2,
            NEPTUNE_RELATIONSHIP_HEADER_TO: start_key,
            NEPTUNE_HEADER_LABEL: BadgeMetadata.INVERSE_BADGE_RELATION_TYPE,
            NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
            NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB
        }
        expected = [[neptune_forward_expected_1, neptune_reversed_expected_1],
                    [neptune_forward_expected_2, neptune_reversed_expected_2]]

        self.assertEqual(expected, actual)

    def test_create_records(self) -> None:
        expected = [
            {
                'rk': BadgeMetadata.BADGE_KEY_FORMAT.format(badge=badge1.name),
                'category': badge1.category
            },
            {
                'rk': BadgeMetadata.BADGE_KEY_FORMAT.format(badge=badge2.name),
                'category': badge2.category
            }
        ]

        actual = []
        record = self.badge_metada.create_next_record()
        while record:
            serialized_record = mysql_serializer.serialize_record(record)
            actual.append(serialized_record)
            record = self.badge_metada.create_next_record()

        self.assertEqual(expected, actual)
