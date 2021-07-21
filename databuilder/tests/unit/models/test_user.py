# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import unittest
from unittest.mock import ANY

from databuilder.models.graph_serializable import (
    RELATION_END_KEY, RELATION_END_LABEL, RELATION_REVERSE_TYPE, RELATION_START_KEY, RELATION_START_LABEL,
    RELATION_TYPE,
)
from databuilder.models.user import User
from databuilder.serializers import (
    mysql_serializer, neo4_serializer, neptune_serializer,
)
from databuilder.serializers.neptune_serializer import (
    METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT, NEPTUNE_CREATION_TYPE_JOB,
    NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT, NEPTUNE_HEADER_ID, NEPTUNE_HEADER_LABEL,
    NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT, NEPTUNE_RELATIONSHIP_HEADER_FROM,
    NEPTUNE_RELATIONSHIP_HEADER_TO,
)


class TestUser(unittest.TestCase):

    def setUp(self) -> None:
        super(TestUser, self).setUp()
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

    def test_get_user_model_key(self) -> None:
        user_email = User.get_user_model_key(email=self.user.email)
        self.assertEqual(user_email, 'test@email.com')

    def test_create_nodes(self) -> None:
        expected_nodes = [{
            'LABEL': 'User',
            'KEY': 'test@email.com',
            'email': 'test@email.com',
            'is_active:UNQUOTED': True,
            'first_name': 'test_first',
            'last_name': 'test_last',
            'full_name': 'test_first test_last',
            'github_username': 'github_test',
            'team_name': 'test_team',
            'employee_type': 'FTE',
            'slack_id': 'slack',
            'role_name': 'swe',
            'updated_at:UNQUOTED': 1
        }]

        actual = []
        node = self.user.create_next_node()
        while node:
            serialized_node = neo4_serializer.serialize_node(node)
            actual.append(serialized_node)
            node = self.user.create_next_node()

        self.assertEqual(actual, expected_nodes)

    def test_create_node_additional_attr(self) -> None:
        test_user = User(first_name='test_first',
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
                         role_name='swe',
                         enable_notify=True)
        node = test_user.create_next_node()
        serialized_node = neo4_serializer.serialize_node(node)
        self.assertEqual(serialized_node['email'], 'test@email.com')
        self.assertEqual(serialized_node['role_name'], 'swe')
        self.assertTrue(serialized_node['enable_notify:UNQUOTED'])

    def test_create_node_additional_attr_neptune(self) -> None:
        test_user = User(first_name='test_first',
                         last_name='test_last',
                         name='test_first test_last',
                         email='test@email.com',
                         github_username='github_test',
                         team_name='test_team',
                         employee_type='FTE',
                         manager_email='test_manager@email.com',
                         slack_id='slack',
                         is_active=True,
                         updated_at=1,
                         role_name='swe',
                         enable_notify=True)
        node = test_user.create_next_node()
        serialized_node = neptune_serializer.convert_node(node)
        self.assertEqual(serialized_node['email:String(single)'], 'test@email.com')
        self.assertEqual(serialized_node['role_name:String(single)'], 'swe')
        self.assertTrue(serialized_node['enable_notify:Bool(single)'])

    def test_create_record_additional_attr_mysql(self) -> None:
        test_user = User(first_name='test_first',
                         last_name='test_last',
                         name='test_first test_last',
                         email='test@email.com',
                         github_username='github_test',
                         team_name='test_team',
                         employee_type='FTE',
                         manager_email='test_manager@email.com',
                         slack_id='slack',
                         is_active=True,
                         updated_at=1,
                         role_name='swe',
                         enable_notify=True)
        record = test_user.create_next_record()
        serialized_record = mysql_serializer.serialize_record(record)
        self.assertEqual(serialized_record['email'], 'test@email.com')
        self.assertEqual(serialized_record['role_name'], 'swe')

    def test_create_relation(self) -> None:
        actual = []
        relation = self.user.create_next_relation()
        while relation:
            serialized_relation = neo4_serializer.serialize_relationship(relation)
            actual.append(serialized_relation)
            relation = self.user.create_next_relation()

        start_key = 'test@email.com'
        end_key = 'test_manager@email.com'

        expected_relations = [{
            RELATION_START_KEY: start_key,
            RELATION_START_LABEL: User.USER_NODE_LABEL,
            RELATION_END_KEY: end_key,
            RELATION_END_LABEL: User.USER_NODE_LABEL,
            RELATION_TYPE: User.USER_MANAGER_RELATION_TYPE,
            RELATION_REVERSE_TYPE: User.MANAGER_USER_RELATION_TYPE
        }]

        self.assertTrue(expected_relations, actual)

    def test_create_relation_neptune(self) -> None:
        actual = []
        relation = self.user.create_next_relation()
        while relation:
            serialized = neptune_serializer.convert_relationship(relation)
            actual.append(serialized)
            relation = self.user.create_next_relation()

        start_key = 'User:{email}'.format(email='test@email.com')
        end_key = 'User:{email}'.format(email='test_manager@email.com')

        expected = [
            [
                {
                    NEPTUNE_HEADER_ID: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                        from_vertex_id=start_key,
                        to_vertex_id=end_key,
                        label=User.USER_MANAGER_RELATION_TYPE
                    ),
                    METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                        from_vertex_id=start_key,
                        to_vertex_id=end_key,
                        label=User.USER_MANAGER_RELATION_TYPE
                    ),
                    NEPTUNE_RELATIONSHIP_HEADER_FROM: start_key,
                    NEPTUNE_RELATIONSHIP_HEADER_TO: end_key,
                    NEPTUNE_HEADER_LABEL: User.USER_MANAGER_RELATION_TYPE,
                    NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
                    NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB
                },
                {
                    NEPTUNE_HEADER_ID: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                        from_vertex_id=end_key,
                        to_vertex_id=start_key,
                        label=User.MANAGER_USER_RELATION_TYPE
                    ),
                    METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                        from_vertex_id=end_key,
                        to_vertex_id=start_key,
                        label=User.MANAGER_USER_RELATION_TYPE
                    ),
                    NEPTUNE_RELATIONSHIP_HEADER_FROM: end_key,
                    NEPTUNE_RELATIONSHIP_HEADER_TO: start_key,
                    NEPTUNE_HEADER_LABEL: User.MANAGER_USER_RELATION_TYPE,
                    NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
                    NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB
                }
            ]
        ]

        self.assertListEqual(actual, expected)

    def test_not_including_empty_attribute(self) -> None:
        test_user = User(email='test@email.com',
                         foo='bar')

        self.assertDictEqual(neo4_serializer.serialize_node(test_user.create_next_node()),
                             {'KEY': 'test@email.com', 'LABEL': 'User', 'email': 'test@email.com',
                              'is_active:UNQUOTED': True, 'first_name': '', 'last_name': '', 'full_name': '',
                              'github_username': '', 'team_name': '', 'employee_type': '', 'slack_id': '',
                              'role_name': '', 'updated_at:UNQUOTED': 0, 'foo': 'bar'})

        test_user2 = User(email='test@email.com',
                          foo='bar',
                          is_active=False,
                          do_not_update_empty_attribute=True)

        self.assertDictEqual(neo4_serializer.serialize_node(test_user2.create_next_node()),
                             {'KEY': 'test@email.com', 'LABEL': 'User', 'email': 'test@email.com', 'foo': 'bar'})
