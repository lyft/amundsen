# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import unittest

from databuilder.models.usage.usage import Usage
from databuilder.serializers import mysql_serializer, neo4_serializer


class TestUsage(unittest.TestCase):

    def setUp(self) -> None:
        self.usage = Usage(
            start_label='Table',
            start_key='the_key',
            user_email='foo@bar.biz',
            read_count=42,
        )

        self.expected_nodes = [
            {
                'KEY': 'foo@bar.biz',
                'LABEL': 'User',
                'email': 'foo@bar.biz',
            }
        ]

        self.expected_relations = [
            {
                'START_LABEL': 'Table',
                'END_LABEL': 'User',
                'START_KEY': 'the_key',
                'END_KEY': 'foo@bar.biz',
                'TYPE': 'READ_BY',
                'REVERSE_TYPE': 'READ',
                'read_count:UNQUOTED': 42,
            },
        ]

        self.expected_records = [
            {
                'rk': 'foo@bar.biz',
                'email': 'foo@bar.biz',
            },
            {
                'table_rk': 'the_key',
                'user_rk': 'foo@bar.biz',
                'read_count': 42,
            }
        ]

    def test_usage_not_supported(self) -> None:
        with self.assertRaises(Exception) as e:
            Usage(
                start_label='User',  # users can't have usage
                start_key='user@user.us',
                user_email='another_user@user.us',
            )
        self.assertEqual(e.exception.args, ('usage for User is not supported',))

    def test_usage_nodes(self) -> None:
        node = self.usage.next_node()
        actual = []
        while node:
            node_serialized = neo4_serializer.serialize_node(node)
            actual.append(node_serialized)
            node = self.usage.next_node()

        self.assertEqual(actual, self.expected_nodes)

    def test_usage_relations(self) -> None:
        actual = []
        relation = self.usage.create_next_relation()
        while relation:
            serialized_relation = neo4_serializer.serialize_relationship(relation)
            actual.append(serialized_relation)
            relation = self.usage.create_next_relation()

        self.assertEqual(actual, self.expected_relations)

    def test_usage_record(self) -> None:
        actual = []
        record = self.usage.create_next_record()
        while record:
            serialized_record = mysql_serializer.serialize_record(record)
            actual.append(serialized_record)
            record = self.usage.create_next_record()

        self.assertEqual(actual, self.expected_records)

    def test_usage_not_table_serializable(self) -> None:
        feature_usage = Usage(
            start_label='Feature',
            start_key='feature://a/b/c',
            user_email='user@user.us',
        )
        with self.assertRaises(Exception) as e:
            record = feature_usage.create_next_record()
            while record:
                record = feature_usage.create_next_record()
        self.assertEqual(e.exception.args, ('Feature usage is not table serializable',))
