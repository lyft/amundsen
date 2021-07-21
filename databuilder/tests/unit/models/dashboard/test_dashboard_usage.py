# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import unittest
from typing import Any, Dict
from unittest.mock import ANY

from databuilder.models.dashboard.dashboard_usage import DashboardUsage
from databuilder.models.graph_serializable import (
    RELATION_END_KEY, RELATION_END_LABEL, RELATION_REVERSE_TYPE, RELATION_START_KEY, RELATION_START_LABEL,
    RELATION_TYPE,
)
from databuilder.serializers import (
    mysql_serializer, neo4_serializer, neptune_serializer,
)
from databuilder.serializers.neptune_serializer import (
    METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT, NEPTUNE_CREATION_TYPE_JOB,
    NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT, NEPTUNE_HEADER_ID, NEPTUNE_HEADER_LABEL,
    NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT, NEPTUNE_RELATIONSHIP_HEADER_FROM,
    NEPTUNE_RELATIONSHIP_HEADER_TO,
)


class TestDashboardOwner(unittest.TestCase):

    def test_dashboard_usage_user_nodes(self) -> None:
        dashboard_usage = DashboardUsage(dashboard_group_id='dashboard_group_id', dashboard_id='dashboard_id',
                                         email='foo@bar.com', view_count=123, cluster='cluster_id',
                                         product='product_id', should_create_user_node=True)

        actual = dashboard_usage.create_next_node()
        actual_serialized = neo4_serializer.serialize_node(actual)
        expected: Dict[str, Any] = {
            'LABEL': 'User',
            'KEY': 'foo@bar.com',
            'email': 'foo@bar.com',
        }

        assert actual is not None
        self.assertDictEqual(expected, actual_serialized)
        self.assertIsNone(dashboard_usage.create_next_node())

    def test_dashboard_usage_no_user_nodes(self) -> None:
        dashboard_usage = DashboardUsage(dashboard_group_id='dashboard_group_id', dashboard_id='dashboard_id',
                                         email='foo@bar.com', view_count=123,
                                         should_create_user_node=False, cluster='cluster_id',
                                         product='product_id')

        self.assertIsNone(dashboard_usage.create_next_node())

    def test_dashboard_owner_relations(self) -> None:
        dashboard_usage = DashboardUsage(dashboard_group_id='dashboard_group_id', dashboard_id='dashboard_id',
                                         email='foo@bar.com', view_count=123, cluster='cluster_id',
                                         product='product_id')

        actual = dashboard_usage.create_next_relation()
        actual_serialized = neo4_serializer.serialize_relationship(actual)
        expected: Dict[str, Any] = {
            'read_count:UNQUOTED': 123,
            RELATION_END_KEY: 'foo@bar.com',
            RELATION_START_LABEL: 'Dashboard',
            RELATION_END_LABEL: 'User',
            RELATION_START_KEY: 'product_id_dashboard://cluster_id.dashboard_group_id/dashboard_id',
            RELATION_TYPE: 'READ_BY',
            RELATION_REVERSE_TYPE: 'READ'
        }

        assert actual is not None
        self.assertDictEqual(expected, actual_serialized)
        self.assertIsNone(dashboard_usage.create_next_relation())

    def test_dashboard_owner_relations_neptune(self) -> None:
        dashboard_usage = DashboardUsage(dashboard_group_id='dashboard_group_id', dashboard_id='dashboard_id',
                                         email='foo@bar.com', view_count=123, cluster='cluster_id',
                                         product='product_id')

        actual = dashboard_usage.create_next_relation()
        actual_serialized = neptune_serializer.convert_relationship(actual)

        forward_id = "{label}:{from_vertex_id}_{to_vertex_id}".format(
            from_vertex_id='Dashboard:product_id_dashboard://cluster_id.dashboard_group_id/dashboard_id',
            to_vertex_id='User:foo@bar.com',
            label='READ_BY'
        )
        reverse_id = "{label}:{from_vertex_id}_{to_vertex_id}".format(
            from_vertex_id='User:foo@bar.com',
            to_vertex_id='Dashboard:product_id_dashboard://cluster_id.dashboard_group_id/dashboard_id',
            label='READ'
        )

        dashboard_id = 'Dashboard:product_id_dashboard://cluster_id.dashboard_group_id/dashboard_id'
        neptune_forward_expected = {
            NEPTUNE_HEADER_ID: forward_id,
            METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: forward_id,
            NEPTUNE_RELATIONSHIP_HEADER_FROM: dashboard_id,
            NEPTUNE_RELATIONSHIP_HEADER_TO: 'User:foo@bar.com',
            NEPTUNE_HEADER_LABEL: 'READ_BY',
            NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
            NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB,
            'read_count:Long(single)': 123
        }

        neptune_reversed_expected = {
            NEPTUNE_HEADER_ID: reverse_id,
            METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: reverse_id,
            NEPTUNE_RELATIONSHIP_HEADER_FROM: 'User:foo@bar.com',
            NEPTUNE_RELATIONSHIP_HEADER_TO: dashboard_id,
            NEPTUNE_HEADER_LABEL: 'READ',
            NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
            NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB,
            'read_count:Long(single)': 123,
        }

        assert actual is not None
        self.maxDiff = None
        self.assertDictEqual(neptune_forward_expected, actual_serialized[0])
        self.assertDictEqual(neptune_reversed_expected, actual_serialized[1])
        self.assertIsNone(dashboard_usage.create_next_relation())

    def test_dashboard_usage_user_records(self) -> None:
        dashboard_usage = DashboardUsage(dashboard_group_id='dashboard_group_id', dashboard_id='dashboard_id',
                                         email='foo@bar.com', view_count=123, cluster='cluster_id',
                                         product='product_id', should_create_user_node=True)

        actual1 = dashboard_usage.create_next_record()
        actual1_serialized = mysql_serializer.serialize_record(actual1)
        expected1 = {
            'rk': 'foo@bar.com',
            'email': 'foo@bar.com',
        }

        assert actual1 is not None
        self.assertDictEqual(expected1, actual1_serialized)

        actual2 = dashboard_usage.create_next_record()
        actual2_serialized = mysql_serializer.serialize_record(actual2)
        expected2 = {
            'user_rk': 'foo@bar.com',
            'dashboard_rk': 'product_id_dashboard://cluster_id.dashboard_group_id/dashboard_id',
            'read_count': 123
        }

        assert actual2 is not None
        self.assertDictEqual(expected2, actual2_serialized)
        self.assertIsNone(dashboard_usage.create_next_record())
