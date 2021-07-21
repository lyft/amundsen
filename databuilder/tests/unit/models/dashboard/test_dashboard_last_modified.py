# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import unittest
from typing import Any, Dict
from unittest.mock import ANY

from databuilder.models.dashboard.dashboard_last_modified import DashboardLastModifiedTimestamp
from databuilder.models.graph_serializable import (
    RELATION_END_KEY, RELATION_END_LABEL, RELATION_REVERSE_TYPE, RELATION_START_KEY, RELATION_START_LABEL,
    RELATION_TYPE,
)
from databuilder.serializers import (
    atlas_serializer, mysql_serializer, neo4_serializer, neptune_serializer,
)
from databuilder.serializers.neptune_serializer import (
    METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT, NEPTUNE_CREATION_TYPE_JOB,
    NEPTUNE_CREATION_TYPE_NODE_PROPERTY_NAME_BULK_LOADER_FORMAT,
    NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT, NEPTUNE_HEADER_ID, NEPTUNE_HEADER_LABEL,
    NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT, NEPTUNE_RELATIONSHIP_HEADER_FROM,
    NEPTUNE_RELATIONSHIP_HEADER_TO,
)


class TestDashboardLastModifiedTimestamp(unittest.TestCase):

    def setUp(self) -> None:
        self.dashboard_last_modified = DashboardLastModifiedTimestamp(
            last_modified_timestamp=123456789,
            cluster='cluster_id',
            product='product_id',
            dashboard_id='dashboard_id',
            dashboard_group_id='dashboard_group_id'
        )

        self.expected_ts_key = 'product_id_dashboard://cluster_id.dashboard_group_id/dashboard_id/' \
                               '_last_modified_timestamp'
        self.expected_dashboard_key = 'product_id_dashboard://cluster_id.dashboard_group_id/dashboard_id'

    def test_dashboard_timestamp_nodes(self) -> None:

        actual = self.dashboard_last_modified.create_next_node()
        actual_serialized = neo4_serializer.serialize_node(actual)

        expected: Dict[str, Any] = {
            'timestamp:UNQUOTED': 123456789,
            'name': 'last_updated_timestamp',
            'KEY': self.expected_ts_key,
            'LABEL': 'Timestamp'
        }

        assert actual is not None
        self.assertDictEqual(actual_serialized, expected)

        self.assertIsNone(self.dashboard_last_modified.create_next_node())

    def test_neptune_dashboard_timestamp_nodes(self) -> None:
        actual = self.dashboard_last_modified.create_next_node()
        actual_neptune_serialized = neptune_serializer.convert_node(actual)
        neptune_expected = {
            NEPTUNE_HEADER_ID: 'Timestamp:' + self.expected_ts_key,
            METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: self.expected_ts_key,
            NEPTUNE_HEADER_LABEL: 'Timestamp',
            NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
            NEPTUNE_CREATION_TYPE_NODE_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB,
            'name:String(single)': 'last_updated_timestamp',
            'timestamp:Long(single)': 123456789,
        }

        self.assertDictEqual(actual_neptune_serialized, neptune_expected)

    def test_dashboard_owner_relations(self) -> None:

        actual = self.dashboard_last_modified.create_next_relation()
        actual_serialized = neo4_serializer.serialize_relationship(actual)

        expected: Dict[str, Any] = {
            RELATION_END_KEY: self.expected_ts_key,
            RELATION_START_LABEL: 'Dashboard',
            RELATION_END_LABEL: 'Timestamp',
            RELATION_START_KEY: self.expected_dashboard_key,
            RELATION_TYPE: 'LAST_UPDATED_AT',
            RELATION_REVERSE_TYPE: 'LAST_UPDATED_TIME_OF'
        }

        assert actual is not None
        self.assertDictEqual(actual_serialized, expected)
        self.assertIsNone(self.dashboard_last_modified.create_next_relation())

    def test_dashboard_owner_relations_neptune(self) -> None:
        actual = self.dashboard_last_modified.create_next_relation()
        actual_serialized = neptune_serializer.convert_relationship(actual)
        neptune_forward_expected = {
            NEPTUNE_HEADER_ID: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                from_vertex_id='Dashboard:' + self.expected_dashboard_key,
                to_vertex_id='Timestamp:' + self.expected_ts_key,
                label='LAST_UPDATED_AT'
            ),
            METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                from_vertex_id='Dashboard:' + self.expected_dashboard_key,
                to_vertex_id='Timestamp:' + self.expected_ts_key,
                label='LAST_UPDATED_AT'
            ),
            NEPTUNE_RELATIONSHIP_HEADER_FROM: 'Dashboard:' + self.expected_dashboard_key,
            NEPTUNE_RELATIONSHIP_HEADER_TO: 'Timestamp:' + self.expected_ts_key,
            NEPTUNE_HEADER_LABEL: 'LAST_UPDATED_AT',
            NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
            NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB
        }

        neptune_reversed_expected = {
            NEPTUNE_HEADER_ID: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                from_vertex_id='Timestamp:' + self.expected_ts_key,
                to_vertex_id='Dashboard:' + self.expected_dashboard_key,
                label='LAST_UPDATED_TIME_OF'
            ),
            METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                from_vertex_id='Timestamp:' + self.expected_ts_key,
                to_vertex_id='Dashboard:' + self.expected_dashboard_key,
                label='LAST_UPDATED_TIME_OF'
            ),
            NEPTUNE_RELATIONSHIP_HEADER_FROM: 'Timestamp:' + self.expected_ts_key,
            NEPTUNE_RELATIONSHIP_HEADER_TO: 'Dashboard:' + self.expected_dashboard_key,
            NEPTUNE_HEADER_LABEL: 'LAST_UPDATED_TIME_OF',
            NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
            NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB
        }
        self.maxDiff = None
        assert actual is not None
        self.assertDictEqual(actual_serialized[0], neptune_forward_expected)
        self.assertDictEqual(actual_serialized[1], neptune_reversed_expected)
        self.assertIsNone(self.dashboard_last_modified.create_next_relation())

    def test_dashboard_timestamp_records(self) -> None:

        actual = self.dashboard_last_modified.create_next_record()
        actual_serialized = mysql_serializer.serialize_record(actual)

        expected = {
            'rk': 'product_id_dashboard://cluster_id.dashboard_group_id/dashboard_id/_last_modified_timestamp',
            'timestamp': 123456789,
            'name': 'last_updated_timestamp',
            'dashboard_rk': 'product_id_dashboard://cluster_id.dashboard_group_id/dashboard_id'
        }

        assert actual is not None
        self.assertDictEqual(actual_serialized, expected)
        self.assertIsNone(self.dashboard_last_modified.create_next_record())

    def test_dashboard_last_modified_relation_atlas(self) -> None:

        actual = self.dashboard_last_modified.create_next_atlas_entity()
        actual_serialized = atlas_serializer.serialize_entity(actual)

        expected = {
            "typeName": "Dashboard",
            "operation": "UPDATE",
            "relationships": None,
            "qualifiedName": "product_id_dashboard://cluster_id.dashboard_group_id/dashboard_id",
            "lastModifiedTimestamp": 123456789
        }

        assert actual is not None
        self.assertDictEqual(actual_serialized, expected)
        self.assertIsNone(self.dashboard_last_modified.create_next_atlas_entity())
