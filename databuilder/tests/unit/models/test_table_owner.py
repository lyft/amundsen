# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import unittest
from unittest.mock import ANY

from databuilder.models.graph_serializable import (
    NODE_KEY, NODE_LABEL, RELATION_END_KEY, RELATION_END_LABEL, RELATION_REVERSE_TYPE, RELATION_START_KEY,
    RELATION_START_LABEL, RELATION_TYPE,
)
from databuilder.models.owner_constants import OWNER_OF_OBJECT_RELATION_TYPE, OWNER_RELATION_TYPE
from databuilder.models.table_owner import TableOwner
from databuilder.models.user import User
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
TABLE_KEY = 'hive://DEFAULT.BASE/TEST'
owner1 = 'user1@1'
owner2 = 'user2@2'


class TestTableOwner(unittest.TestCase):

    def setUp(self) -> None:
        super(TestTableOwner, self).setUp()
        self.table_owner = TableOwner(db_name='hive',
                                      schema=SCHEMA,
                                      table_name=TABLE,
                                      cluster=CLUSTER,
                                      owners="user1@1, user2@2 ")

    def test_create_nodes(self) -> None:
        expected_node1 = {
            NODE_KEY: User.USER_NODE_KEY_FORMAT.format(email=owner1),
            NODE_LABEL: User.USER_NODE_LABEL,
            User.USER_NODE_EMAIL: owner1
        }
        expected_node2 = {
            NODE_KEY: User.USER_NODE_KEY_FORMAT.format(email=owner2),
            NODE_LABEL: User.USER_NODE_LABEL,
            User.USER_NODE_EMAIL: owner2
        }
        expected = [expected_node1, expected_node2]

        actual = []
        node = self.table_owner.create_next_node()
        while node:
            serialized_node = neo4_serializer.serialize_node(node)
            actual.append(serialized_node)
            node = self.table_owner.create_next_node()

        self.assertEqual(actual, expected)

    def test_create_nodes_neptune(self) -> None:
        expected_node1 = {
            NEPTUNE_HEADER_ID: "User:" + User.USER_NODE_KEY_FORMAT.format(email=owner1),
            METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: User.USER_NODE_KEY_FORMAT.format(email=owner1),
            NEPTUNE_HEADER_LABEL: User.USER_NODE_LABEL,
            NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
            NEPTUNE_CREATION_TYPE_NODE_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB,
            User.USER_NODE_EMAIL + ":String(single)": owner1
        }
        expected_node2 = {
            NEPTUNE_HEADER_ID: "User:" + User.USER_NODE_KEY_FORMAT.format(email=owner2),
            METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: User.USER_NODE_KEY_FORMAT.format(email=owner2),
            NEPTUNE_HEADER_LABEL: User.USER_NODE_LABEL,
            NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
            NEPTUNE_CREATION_TYPE_NODE_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB,
            User.USER_NODE_EMAIL + ":String(single)": owner2
        }
        expected = [expected_node1, expected_node2]

        actual = []
        node = self.table_owner.create_next_node()
        while node:
            serialized_node = neptune_serializer.convert_node(node)
            actual.append(serialized_node)
            node = self.table_owner.create_next_node()

        self.assertEqual(actual, expected)

    def test_create_relation(self) -> None:
        expected_relation1 = {
            RELATION_START_KEY: TABLE_KEY,
            RELATION_START_LABEL: 'Table',
            RELATION_END_KEY: owner1,
            RELATION_END_LABEL: User.USER_NODE_LABEL,
            RELATION_TYPE: OWNER_RELATION_TYPE,
            RELATION_REVERSE_TYPE: OWNER_OF_OBJECT_RELATION_TYPE,
        }
        expected_relation2 = {
            RELATION_START_KEY: TABLE_KEY,
            RELATION_START_LABEL: 'Table',
            RELATION_END_KEY: owner2,
            RELATION_END_LABEL: User.USER_NODE_LABEL,
            RELATION_TYPE: OWNER_RELATION_TYPE,
            RELATION_REVERSE_TYPE: OWNER_OF_OBJECT_RELATION_TYPE,
        }
        expected = [expected_relation1, expected_relation2]

        actual = []
        relation = self.table_owner.create_next_relation()
        while relation:
            serialized_relation = neo4_serializer.serialize_relationship(relation)
            actual.append(serialized_relation)
            relation = self.table_owner.create_next_relation()

        self.assertEqual(actual, expected)

    def test_create_relation_neptune(self) -> None:
        expected = [
            [
                {
                    NEPTUNE_HEADER_ID: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                        from_vertex_id="Table:" + TABLE_KEY,
                        to_vertex_id="User:" + owner1,
                        label=OWNER_RELATION_TYPE
                    ),
                    METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                        from_vertex_id="Table:" + TABLE_KEY,
                        to_vertex_id="User:" + owner1,
                        label=OWNER_RELATION_TYPE
                    ),
                    NEPTUNE_RELATIONSHIP_HEADER_FROM: "Table:" + TABLE_KEY,
                    NEPTUNE_RELATIONSHIP_HEADER_TO: "User:" + owner1,
                    NEPTUNE_HEADER_LABEL: OWNER_RELATION_TYPE,
                    NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
                    NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB
                },
                {
                    NEPTUNE_HEADER_ID: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                        from_vertex_id="User:" + owner1,
                        to_vertex_id="Table:" + TABLE_KEY,
                        label=OWNER_OF_OBJECT_RELATION_TYPE
                    ),
                    METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                        from_vertex_id="User:" + owner1,
                        to_vertex_id="Table:" + TABLE_KEY,
                        label=OWNER_OF_OBJECT_RELATION_TYPE
                    ),
                    NEPTUNE_RELATIONSHIP_HEADER_FROM: "User:" + owner1,
                    NEPTUNE_RELATIONSHIP_HEADER_TO: "Table:" + TABLE_KEY,
                    NEPTUNE_HEADER_LABEL: OWNER_OF_OBJECT_RELATION_TYPE,
                    NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
                    NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB
                },
            ],
            [
                {
                    NEPTUNE_HEADER_ID: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                        from_vertex_id="Table:" + TABLE_KEY,
                        to_vertex_id="User:" + owner2,
                        label=OWNER_RELATION_TYPE
                    ),
                    METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                        from_vertex_id="Table:" + TABLE_KEY,
                        to_vertex_id="User:" + owner2,
                        label=OWNER_RELATION_TYPE
                    ),
                    NEPTUNE_RELATIONSHIP_HEADER_FROM: "Table:" + TABLE_KEY,
                    NEPTUNE_RELATIONSHIP_HEADER_TO: "User:" + owner2,
                    NEPTUNE_HEADER_LABEL: OWNER_RELATION_TYPE,
                    NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
                    NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB
                },
                {
                    NEPTUNE_HEADER_ID: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                        from_vertex_id="User:" + owner2,
                        to_vertex_id="Table:" + TABLE_KEY,
                        label=OWNER_OF_OBJECT_RELATION_TYPE
                    ),
                    METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                        from_vertex_id="User:" + owner2,
                        to_vertex_id="Table:" + TABLE_KEY,
                        label=OWNER_OF_OBJECT_RELATION_TYPE
                    ),
                    NEPTUNE_RELATIONSHIP_HEADER_FROM: "User:" + owner2,
                    NEPTUNE_RELATIONSHIP_HEADER_TO: "Table:" + TABLE_KEY,
                    NEPTUNE_HEADER_LABEL: OWNER_OF_OBJECT_RELATION_TYPE,
                    NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
                    NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB
                },
            ]
        ]

        actual = []
        relation = self.table_owner.create_next_relation()
        while relation:
            serialized_relation = neptune_serializer.convert_relationship(relation)
            actual.append(serialized_relation)
            relation = self.table_owner.create_next_relation()

        self.assertEqual(expected, actual)

    def test_create_records(self) -> None:
        expected = [
            {
                'rk': User.USER_NODE_KEY_FORMAT.format(email=owner1),
                'email': owner1
            },
            {
                'table_rk': TABLE_KEY,
                'user_rk': owner1
            },
            {
                'rk': User.USER_NODE_KEY_FORMAT.format(email=owner2),
                'email': owner2
            },
            {
                'table_rk': TABLE_KEY,
                'user_rk': owner2
            }
        ]

        actual = []
        record = self.table_owner.create_next_record()
        while record:
            serialized_record = mysql_serializer.serialize_record(record)
            actual.append(serialized_record)
            record = self.table_owner.create_next_record()

        self.assertEqual(actual, expected)

    def test_create_nodes_with_owners_list(self) -> None:
        self.table_owner_list = TableOwner(db_name='hive',
                                           schema=SCHEMA,
                                           table_name=TABLE,
                                           cluster=CLUSTER,
                                           owners=['user1@1', ' user2@2 '])
        expected_node1 = {
            NODE_KEY: User.USER_NODE_KEY_FORMAT.format(email=owner1),
            NODE_LABEL: User.USER_NODE_LABEL,
            User.USER_NODE_EMAIL: owner1
        }
        expected_node2 = {
            NODE_KEY: User.USER_NODE_KEY_FORMAT.format(email=owner2),
            NODE_LABEL: User.USER_NODE_LABEL,
            User.USER_NODE_EMAIL: owner2
        }
        expected = [expected_node1, expected_node2]

        actual = []
        node = self.table_owner_list.create_next_node()
        while node:
            serialized_node = neo4_serializer.serialize_node(node)
            actual.append(serialized_node)
            node = self.table_owner_list.create_next_node()

        self.assertEqual(actual, expected)
