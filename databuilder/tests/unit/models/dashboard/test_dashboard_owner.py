# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import unittest
from unittest.mock import ANY

from databuilder.models.dashboard.dashboard_owner import DashboardOwner
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

    def setUp(self) -> None:
        self.dashboard_owner = DashboardOwner(
            email='foo@bar.com',
            cluster='cluster_id',
            product='product_id',
            dashboard_id='dashboard_id',
            dashboard_group_id='dashboard_group_id'
        )

    def test_dashboard_owner_nodes(self) -> None:
        actual = self.dashboard_owner.create_next_node()
        self.assertIsNone(actual)

    def test_dashboard_owner_relations(self) -> None:

        actual = self.dashboard_owner.create_next_relation()
        actual_serialized = neo4_serializer.serialize_relationship(actual)
        expected = {
            RELATION_END_KEY: 'foo@bar.com',
            RELATION_START_LABEL: 'Dashboard',
            RELATION_END_LABEL: 'User',
            RELATION_START_KEY: 'product_id_dashboard://cluster_id.dashboard_group_id/dashboard_id',
            RELATION_TYPE: 'OWNER',
            RELATION_REVERSE_TYPE: 'OWNER_OF'
        }
        assert actual is not None
        self.assertDictEqual(actual_serialized, expected)

    def test_dashboard_owner_relations_neptune(self) -> None:
        actual = self.dashboard_owner.create_next_relation()
        actual_serialized = neptune_serializer.convert_relationship(actual)
        neptune_forward_expected = {
            NEPTUNE_HEADER_ID: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                from_vertex_id='Dashboard:product_id_dashboard://cluster_id.dashboard_group_id/dashboard_id',
                to_vertex_id='User:foo@bar.com',
                label='OWNER'
            ),
            METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                from_vertex_id='Dashboard:product_id_dashboard://cluster_id.dashboard_group_id/dashboard_id',
                to_vertex_id='User:foo@bar.com',
                label='OWNER'
            ),
            NEPTUNE_RELATIONSHIP_HEADER_FROM:
                'Dashboard:product_id_dashboard://cluster_id.dashboard_group_id/dashboard_id',
            NEPTUNE_RELATIONSHIP_HEADER_TO: 'User:foo@bar.com',
            NEPTUNE_HEADER_LABEL: 'OWNER',
            NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
            NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB
        }

        neptune_reversed_expected = {
            NEPTUNE_HEADER_ID: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                from_vertex_id='User:foo@bar.com',
                to_vertex_id='Dashboard:product_id_dashboard://cluster_id.dashboard_group_id/dashboard_id',
                label='OWNER_OF'
            ),
            METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                from_vertex_id='User:foo@bar.com',
                to_vertex_id='Dashboard:product_id_dashboard://cluster_id.dashboard_group_id/dashboard_id',
                label='OWNER_OF'
            ),
            NEPTUNE_RELATIONSHIP_HEADER_FROM: 'User:foo@bar.com',
            NEPTUNE_RELATIONSHIP_HEADER_TO:
                'Dashboard:product_id_dashboard://cluster_id.dashboard_group_id/dashboard_id',
            NEPTUNE_HEADER_LABEL: 'OWNER_OF',
            NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
            NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB
        }

        assert actual is not None
        self.assertDictEqual(actual_serialized[0], neptune_forward_expected)
        self.assertDictEqual(actual_serialized[1], neptune_reversed_expected)

    def test_dashboard_owner_record(self) -> None:

        actual = self.dashboard_owner.create_next_record()
        actual_serialized = mysql_serializer.serialize_record(actual)
        expected = {
            'user_rk': 'foo@bar.com',
            'dashboard_rk': 'product_id_dashboard://cluster_id.dashboard_group_id/dashboard_id'
        }

        assert actual is not None
        self.assertDictEqual(expected, actual_serialized)
        self.assertIsNone(self.dashboard_owner.create_next_record())
