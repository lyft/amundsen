# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import unittest
from unittest.mock import ANY

from databuilder.models.dashboard.dashboard_query import DashboardQuery
from databuilder.models.graph_serializable import (
    NODE_KEY, NODE_LABEL, RELATION_END_KEY, RELATION_END_LABEL, RELATION_REVERSE_TYPE, RELATION_START_KEY,
    RELATION_START_LABEL, RELATION_TYPE,
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


class TestDashboardQuery(unittest.TestCase):

    def setUp(self) -> None:
        self.dashboard_query = DashboardQuery(
            dashboard_group_id='dg_id',
            dashboard_id='d_id',
            query_id='q_id',
            query_name='q_name',
            url='http://foo.bar/query/baz',
            query_text='SELECT * FROM foo.bar'
        )

    def test_create_nodes(self) -> None:
        actual = self.dashboard_query.create_next_node()
        actual_serialized = neo4_serializer.serialize_node(actual)
        expected = {
            'url': 'http://foo.bar/query/baz',
            'name': 'q_name',
            'id': 'q_id',
            'query_text': 'SELECT * FROM foo.bar',
            NODE_KEY: '_dashboard://gold.dg_id/d_id/query/q_id',
            NODE_LABEL: DashboardQuery.DASHBOARD_QUERY_LABEL
        }

        self.assertEqual(expected, actual_serialized)

    def test_create_nodes_neptune(self) -> None:
        actual = self.dashboard_query.create_next_node()
        actual_serialized = neptune_serializer.convert_node(actual)
        neptune_expected = {
            NEPTUNE_HEADER_ID: 'Query:_dashboard://gold.dg_id/d_id/query/q_id',
            METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: '_dashboard://gold.dg_id/d_id/query/q_id',
            NEPTUNE_HEADER_LABEL: DashboardQuery.DASHBOARD_QUERY_LABEL,
            NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
            NEPTUNE_CREATION_TYPE_NODE_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB,
            'id:String(single)': 'q_id',
            'query_text:String(single)': 'SELECT * FROM foo.bar',
            'name:String(single)': 'q_name',
            'url:String(single)': 'http://foo.bar/query/baz'
        }
        self.assertEqual(neptune_expected, actual_serialized)

    def test_create_relation(self) -> None:
        actual = self.dashboard_query.create_next_relation()
        actual_serialized = neo4_serializer.serialize_relationship(actual)
        expected = {
            RELATION_END_KEY: '_dashboard://gold.dg_id/d_id/query/q_id',
            RELATION_START_LABEL: 'Dashboard',
            RELATION_END_LABEL: DashboardQuery.DASHBOARD_QUERY_LABEL,
            RELATION_START_KEY: '_dashboard://gold.dg_id/d_id',
            RELATION_TYPE: 'HAS_QUERY',
            RELATION_REVERSE_TYPE: 'QUERY_OF'
        }

        self.assertEqual(expected, actual_serialized)

    def test_create_relation_neptune(self) -> None:
        actual = self.dashboard_query.create_next_relation()
        actual_serialized = neptune_serializer.convert_relationship(actual)
        neptune_forward_expected = {
            NEPTUNE_HEADER_ID: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                from_vertex_id='Dashboard:_dashboard://gold.dg_id/d_id',
                to_vertex_id='Query:_dashboard://gold.dg_id/d_id/query/q_id',
                label='HAS_QUERY'
            ),
            METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                from_vertex_id='Dashboard:_dashboard://gold.dg_id/d_id',
                to_vertex_id='Query:_dashboard://gold.dg_id/d_id/query/q_id',
                label='HAS_QUERY'
            ),
            NEPTUNE_RELATIONSHIP_HEADER_FROM: 'Dashboard:_dashboard://gold.dg_id/d_id',
            NEPTUNE_RELATIONSHIP_HEADER_TO: 'Query:_dashboard://gold.dg_id/d_id/query/q_id',
            NEPTUNE_HEADER_LABEL: 'HAS_QUERY',
            NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
            NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB
        }

        neptune_reversed_expected = {
            NEPTUNE_HEADER_ID: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                from_vertex_id='Query:_dashboard://gold.dg_id/d_id/query/q_id',
                to_vertex_id='Dashboard:_dashboard://gold.dg_id/d_id',
                label='QUERY_OF'
            ),
            METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                from_vertex_id='Query:_dashboard://gold.dg_id/d_id/query/q_id',
                to_vertex_id='Dashboard:_dashboard://gold.dg_id/d_id',
                label='QUERY_OF'
            ),
            NEPTUNE_RELATIONSHIP_HEADER_FROM: 'Query:_dashboard://gold.dg_id/d_id/query/q_id',
            NEPTUNE_RELATIONSHIP_HEADER_TO: 'Dashboard:_dashboard://gold.dg_id/d_id',
            NEPTUNE_HEADER_LABEL: 'QUERY_OF',
            NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
            NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB
        }

        assert actual is not None
        self.assertDictEqual(actual_serialized[0], neptune_forward_expected)
        self.assertDictEqual(actual_serialized[1], neptune_reversed_expected)

    def test_create_records(self) -> None:
        actual = self.dashboard_query.create_next_record()
        actual_serialized = mysql_serializer.serialize_record(actual)
        expected = {
            'rk': '_dashboard://gold.dg_id/d_id/query/q_id',
            'name': 'q_name',
            'id': 'q_id',
            'dashboard_rk': '_dashboard://gold.dg_id/d_id',
            'url': 'http://foo.bar/query/baz',
            'query_text': 'SELECT * FROM foo.bar'
        }

        assert actual is not None
        self.assertDictEqual(expected, actual_serialized)
        self.assertIsNone(self.dashboard_query.create_next_record())

    def test_create_next_atlas_entity(self) -> None:
        actual = self.dashboard_query.create_next_atlas_entity()
        actual_serialized = atlas_serializer.serialize_entity(actual)

        expected = {
            "typeName": "DashboardQuery",
            "operation": "CREATE",
            "relationships": "dashboard#Dashboard#_dashboard://gold.dg_id/d_id",
            "qualifiedName": "_dashboard://gold.dg_id/d_id/query/q_id",
            "name": "q_name",
            "id": "q_id",
            "url": "http://foo.bar/query/baz",
            "queryText": "SELECT * FROM foo.bar"
        }

        assert actual is not None
        self.assertDictEqual(expected, actual_serialized)
        self.assertIsNone(self.dashboard_query.create_next_atlas_entity())
