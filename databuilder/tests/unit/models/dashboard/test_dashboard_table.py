# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import unittest
from unittest.mock import ANY

from databuilder.models.dashboard.dashboard_table import DashboardTable
from databuilder.models.graph_serializable import (
    RELATION_END_KEY, RELATION_END_LABEL, RELATION_REVERSE_TYPE, RELATION_START_KEY, RELATION_START_LABEL,
    RELATION_TYPE,
)
from databuilder.serializers import (
    atlas_serializer, mysql_serializer, neo4_serializer, neptune_serializer,
)
from databuilder.serializers.neptune_serializer import (
    METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT, NEPTUNE_CREATION_TYPE_JOB,
    NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT, NEPTUNE_HEADER_ID, NEPTUNE_HEADER_LABEL,
    NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT, NEPTUNE_RELATIONSHIP_HEADER_FROM,
    NEPTUNE_RELATIONSHIP_HEADER_TO,
)


class TestDashboardTable(unittest.TestCase):
    def test_dashboard_table_nodes(self) -> None:
        dashboard_table = DashboardTable(table_ids=['hive://gold.schema/table1', 'hive://gold.schema/table2'],
                                         cluster='cluster_id', product='product_id',
                                         dashboard_id='dashboard_id', dashboard_group_id='dashboard_group_id')

        actual = dashboard_table.create_next_node()
        self.assertIsNone(actual)

    def test_dashboard_table_relations(self) -> None:
        dashboard_table = DashboardTable(table_ids=['hive://gold.schema/table1'],
                                         cluster='cluster_id', product='product_id',
                                         dashboard_id='dashboard_id', dashboard_group_id='dashboard_group_id')

        actual = dashboard_table.create_next_relation()
        actual_serialized = neo4_serializer.serialize_relationship(actual)
        actual_neptune_serialized = neptune_serializer.convert_relationship(actual)
        expected = {RELATION_END_KEY: 'hive://gold.schema/table1', RELATION_START_LABEL: 'Dashboard',
                    RELATION_END_LABEL: 'Table',
                    RELATION_START_KEY: 'product_id_dashboard://cluster_id.dashboard_group_id/dashboard_id',
                    RELATION_TYPE: 'DASHBOARD_WITH_TABLE',
                    RELATION_REVERSE_TYPE: 'TABLE_OF_DASHBOARD'}

        neptune_forward_expected = {
            NEPTUNE_HEADER_ID: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                from_vertex_id='Dashboard:product_id_dashboard://cluster_id.dashboard_group_id/dashboard_id',
                to_vertex_id='Table:hive://gold.schema/table1',
                label='DASHBOARD_WITH_TABLE'
            ),
            METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                from_vertex_id='Dashboard:product_id_dashboard://cluster_id.dashboard_group_id/dashboard_id',
                to_vertex_id='Table:hive://gold.schema/table1',
                label='DASHBOARD_WITH_TABLE'
            ),
            NEPTUNE_RELATIONSHIP_HEADER_FROM:
                'Dashboard:product_id_dashboard://cluster_id.dashboard_group_id/dashboard_id',
            NEPTUNE_RELATIONSHIP_HEADER_TO: 'Table:hive://gold.schema/table1',
            NEPTUNE_HEADER_LABEL: 'DASHBOARD_WITH_TABLE',
            NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
            NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB
        }

        neptune_reversed_expected = {
            NEPTUNE_HEADER_ID: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                from_vertex_id='Table:hive://gold.schema/table1',
                to_vertex_id='Dashboard:product_id_dashboard://cluster_id.dashboard_group_id/dashboard_id',
                label='TABLE_OF_DASHBOARD'
            ),
            METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                from_vertex_id='Table:hive://gold.schema/table1',
                to_vertex_id='Dashboard:product_id_dashboard://cluster_id.dashboard_group_id/dashboard_id',
                label='TABLE_OF_DASHBOARD'
            ),
            NEPTUNE_RELATIONSHIP_HEADER_FROM: 'Table:hive://gold.schema/table1',
            NEPTUNE_RELATIONSHIP_HEADER_TO:
                'Dashboard:product_id_dashboard://cluster_id.dashboard_group_id/dashboard_id',
            NEPTUNE_HEADER_LABEL: 'TABLE_OF_DASHBOARD',
            NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
            NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB
        }
        assert actual is not None
        self.assertDictEqual(actual_serialized, expected)
        self.assertDictEqual(actual_neptune_serialized[0], neptune_forward_expected)
        self.assertDictEqual(actual_neptune_serialized[1], neptune_reversed_expected)

    def test_dashboard_table_without_dot_as_name(self) -> None:
        dashboard_table = DashboardTable(table_ids=['bq-name://project-id.schema-name/table-name'],
                                         cluster='cluster_id', product='product_id',
                                         dashboard_id='dashboard_id', dashboard_group_id='dashboard_group_id')
        actual = dashboard_table.create_next_relation()
        actual_serialized = neo4_serializer.serialize_relationship(actual)
        expected = {RELATION_END_KEY: 'bq-name://project-id.schema-name/table-name', RELATION_START_LABEL: 'Dashboard',
                    RELATION_END_LABEL: 'Table',
                    RELATION_START_KEY: 'product_id_dashboard://cluster_id.dashboard_group_id/dashboard_id',
                    RELATION_TYPE: 'DASHBOARD_WITH_TABLE',
                    RELATION_REVERSE_TYPE: 'TABLE_OF_DASHBOARD'}
        assert actual is not None
        self.assertDictEqual(actual_serialized, expected)

    def test_dashboard_table_with_dot_as_name(self) -> None:
        dashboard_table = DashboardTable(table_ids=['bq-name://project.id.schema-name/table-name'],
                                         cluster='cluster_id', product='product_id',
                                         dashboard_id='dashboard_id', dashboard_group_id='dashboard_group_id')
        actual = dashboard_table.create_next_relation()
        self.assertIsNone(actual)

    def test_dashboard_table_with_slash_as_name(self) -> None:
        dashboard_table = DashboardTable(table_ids=['bq/name://project/id.schema/name/table/name'],
                                         cluster='cluster_id', product='product_id',
                                         dashboard_id='dashboard_id', dashboard_group_id='dashboard_group_id')
        actual = dashboard_table.create_next_relation()
        self.assertIsNone(actual)

    def test_dashboard_table_records(self) -> None:
        dashboard_table = DashboardTable(table_ids=['hive://gold.schema/table1', 'hive://gold.schema/table2'],
                                         cluster='cluster_id', product='product_id',
                                         dashboard_id='dashboard_id', dashboard_group_id='dashboard_group_id')
        actual1 = dashboard_table.create_next_record()
        actual1_serialized = mysql_serializer.serialize_record(actual1)
        expected1 = {
            'dashboard_rk': 'product_id_dashboard://cluster_id.dashboard_group_id/dashboard_id',
            'table_rk': 'hive://gold.schema/table1'
        }

        actual2 = dashboard_table.create_next_record()
        actual2_serialized = mysql_serializer.serialize_record(actual2)
        expected2 = {
            'dashboard_rk': 'product_id_dashboard://cluster_id.dashboard_group_id/dashboard_id',
            'table_rk': 'hive://gold.schema/table2'
        }

        assert actual1 is not None
        self.assertDictEqual(expected1, actual1_serialized)

        assert actual2 is not None
        self.assertDictEqual(expected2, actual2_serialized)
        self.assertIsNone(dashboard_table.create_next_record())

    def test_create_next_atlas_relation(self) -> None:
        dashboard_table = DashboardTable(
            table_ids=['hive://gold.schema/table1', 'hive_table://gold.schema/table2'],
            cluster='cluster_id', product='product_id',
            dashboard_id='dashboard_id', dashboard_group_id='dashboard_group_id',
        )

        # 'hive' is db name compatible with Amundsen Databuilder sourced data. in such case qn = amundsen key
        # 'hive_table' is db name compatible with data sources from Atlas Hive Hook. in such case custom qn is used
        expected = [
            {
                "relationshipType": "Table__Dashboard",
                "entityType1": "Table",
                "entityQualifiedName1": "hive://gold.schema/table1",
                "entityType2": "Dashboard",
                "entityQualifiedName2": "product_id_dashboard://cluster_id.dashboard_group_id/dashboard_id",
            },
            {
                "relationshipType": "Table__Dashboard",
                "entityType1": "Table",
                "entityQualifiedName1": "schema.table2@gold",
                "entityType2": "Dashboard",
                "entityQualifiedName2": "product_id_dashboard://cluster_id.dashboard_group_id/dashboard_id",
            },
        ]
        relationship = dashboard_table.create_next_atlas_relation()  # type: ignore
        actual = []
        while relationship:
            actual_serialized = atlas_serializer.serialize_relationship(relationship)
            actual.append(actual_serialized)
            relationship = dashboard_table.create_next_atlas_relation()

        self.assertEqual(expected, actual)
