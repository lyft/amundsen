# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import unittest

from databuilder.models.owner import Owner
from databuilder.serializers import mysql_serializer, neo4_serializer


class TestDashboardOwner(unittest.TestCase):

    def setUp(self) -> None:
        self.owner = Owner(
            start_label='Table',
            start_key='the_key',
            owner_emails=[
                ' Foo@bar.biz',  # should be converted to 'foo@bar.biz'
                'moo@cow.farm',
            ]
        )

        self.expected_nodes = [
            {
                'KEY': 'foo@bar.biz',
                'LABEL': 'User',
                'email': 'foo@bar.biz',
            },
            {
                'KEY': 'moo@cow.farm',
                'LABEL': 'User',
                'email': 'moo@cow.farm',
            },
        ]

        self.expected_relations = [
            {
                'START_LABEL': 'Table',
                'END_LABEL': 'User',
                'START_KEY': 'the_key',
                'END_KEY': 'foo@bar.biz',
                'TYPE': 'OWNER',
                'REVERSE_TYPE': 'OWNER_OF',
            },
            {
                'START_LABEL': 'Table',
                'END_LABEL': 'User',
                'START_KEY': 'the_key',
                'END_KEY': 'moo@cow.farm',
                'TYPE': 'OWNER',
                'REVERSE_TYPE': 'OWNER_OF',
            },
        ]

        self.expected_records = [
            {
                'rk': 'foo@bar.biz',
                'email': 'foo@bar.biz'
            },
            {
                'table_rk': 'the_key',
                'user_rk': 'foo@bar.biz'
            },
            {
                'rk': 'moo@cow.farm',
                'email': 'moo@cow.farm'
            },
            {
                'table_rk': 'the_key',
                'user_rk': 'moo@cow.farm'
            }
        ]

    def test_not_ownable_label(self) -> None:
        with self.assertRaises(Exception) as e:
            Owner(
                start_label='User',  # users can't be owned by other users
                start_key='user@user.us',
                owner_emails=['another_user@user.us']
            )
        self.assertEqual(e.exception.args, ('owners for User are not supported',))

    def test_owner_nodes(self) -> None:
        node = self.owner.next_node()
        actual = []
        while node:
            node_serialized = neo4_serializer.serialize_node(node)
            actual.append(node_serialized)
            node = self.owner.next_node()

        self.assertEqual(actual, self.expected_nodes)

    def test_owner_relations(self) -> None:
        actual = []
        relation = self.owner.create_next_relation()
        while relation:
            serialized_relation = neo4_serializer.serialize_relationship(relation)
            actual.append(serialized_relation)
            relation = self.owner.create_next_relation()

        self.assertEqual(actual, self.expected_relations)

    def test_owner_record(self) -> None:
        actual = []
        record = self.owner.create_next_record()
        while record:
            serialized_record = mysql_serializer.serialize_record(record)
            actual.append(serialized_record)
            record = self.owner.create_next_record()

        self.assertEqual(actual, self.expected_records)

    def test_not_table_serializable(self) -> None:
        feature_owner = Owner(
            start_label='Feature',
            start_key='feature://a/b/c',
            owner_emails=['user@user.us']
        )
        with self.assertRaises(Exception) as e:
            record = feature_owner.create_next_record()
            while record:
                record = feature_owner.create_next_record()
        self.assertEqual(e.exception.args, ('Feature<>Owner relationship is not table serializable',))
