# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import unittest
from typing import Any, Dict
from unittest.mock import ANY

from databuilder.models.dashboard.dashboard_chart import DashboardChart
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


class TestDashboardChart(unittest.TestCase):

    def test_create_nodes(self) -> None:
        dashboard_chart = DashboardChart(dashboard_group_id='dg_id',
                                         dashboard_id='d_id',
                                         query_id='q_id',
                                         chart_id='c_id',
                                         chart_name='c_name',
                                         chart_type='bar',
                                         chart_url='http://gold.foo/chart'
                                         )

        actual = dashboard_chart.create_next_node()
        actual_serialized = neo4_serializer.serialize_node(actual)
        neptune_serialized = neptune_serializer.convert_node(actual)
        expected: Dict[str, Any] = {
            'name': 'c_name',
            'type': 'bar',
            'id': 'c_id',
            'url': 'http://gold.foo/chart',
            'KEY': '_dashboard://gold.dg_id/d_id/query/q_id/chart/c_id',
            'LABEL': 'Chart'
        }
        neptune_expected = {
            '~id': 'Chart:_dashboard://gold.dg_id/d_id/query/q_id/chart/c_id',
            METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: '_dashboard://gold.dg_id/d_id/query/q_id/chart/c_id',
            '~label': 'Chart',
            NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
            NEPTUNE_CREATION_TYPE_NODE_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB,
            'type:String(single)': 'bar',
            'name:String(single)': 'c_name',
            'id:String(single)': 'c_id',
            'url:String(single)': 'http://gold.foo/chart',
        }

        assert actual is not None
        self.assertDictEqual(expected, actual_serialized)
        self.assertDictEqual(neptune_expected, neptune_serialized)
        self.assertIsNone(dashboard_chart.create_next_node())

        dashboard_chart = DashboardChart(
            dashboard_group_id='dg_id',
            dashboard_id='d_id',
            query_id='q_id',
            chart_id='c_id',
            chart_url='http://gold.foo.bar/'
        )

        actual2 = dashboard_chart.create_next_node()
        actual2_serialized = neo4_serializer.serialize_node(actual2)
        actual2_neptune_serialized = neptune_serializer.convert_node(actual2)
        expected2: Dict[str, Any] = {
            'id': 'c_id',
            'KEY': '_dashboard://gold.dg_id/d_id/query/q_id/chart/c_id',
            'LABEL': 'Chart',
            'url': 'http://gold.foo.bar/'
        }
        neptune_expected2 = {
            '~id': 'Chart:_dashboard://gold.dg_id/d_id/query/q_id/chart/c_id',
            METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: '_dashboard://gold.dg_id/d_id/query/q_id/chart/c_id',
            '~label': 'Chart',
            'id:String(single)': 'c_id',
            NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
            NEPTUNE_CREATION_TYPE_NODE_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB,
            'url:String(single)': 'http://gold.foo.bar/',
        }
        assert actual2 is not None
        self.assertDictEqual(expected2, actual2_serialized)
        self.assertDictEqual(neptune_expected2, actual2_neptune_serialized)

    def test_create_relation(self) -> None:
        dashboard_chart = DashboardChart(dashboard_group_id='dg_id',
                                         dashboard_id='d_id',
                                         query_id='q_id',
                                         chart_id='c_id',
                                         chart_name='c_name',
                                         chart_type='bar',
                                         )

        actual = dashboard_chart.create_next_relation()
        actual_serialized = neo4_serializer.serialize_relationship(actual)
        actual_neptune_serialized = neptune_serializer.convert_relationship(actual)
        start_key = '_dashboard://gold.dg_id/d_id/query/q_id'
        end_key = '_dashboard://gold.dg_id/d_id/query/q_id/chart/c_id'
        expected: Dict[str, Any] = {
            RELATION_END_KEY: end_key,
            RELATION_START_LABEL: 'Query',
            RELATION_END_LABEL: 'Chart',
            RELATION_START_KEY: start_key,
            RELATION_TYPE: 'HAS_CHART',
            RELATION_REVERSE_TYPE: 'CHART_OF'
        }

        neptune_forward_expected = {
            NEPTUNE_HEADER_ID: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                from_vertex_id="Query:" + start_key,
                to_vertex_id="Chart:" + end_key,
                label='HAS_CHART'
            ),
            METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                from_vertex_id="Query:" + start_key,
                to_vertex_id="Chart:" + end_key,
                label='HAS_CHART'
            ),
            NEPTUNE_RELATIONSHIP_HEADER_FROM: "Query:" + start_key,
            NEPTUNE_RELATIONSHIP_HEADER_TO: "Chart:" + end_key,
            NEPTUNE_HEADER_LABEL: 'HAS_CHART',
            NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
            NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB
        }

        neptune_reversed_expected = {
            NEPTUNE_HEADER_ID: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                from_vertex_id="Chart:" + end_key,
                to_vertex_id="Query:" + start_key,
                label='CHART_OF'
            ),
            METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                from_vertex_id="Chart:" + end_key,
                to_vertex_id="Query:" + start_key,
                label='CHART_OF'
            ),
            NEPTUNE_RELATIONSHIP_HEADER_FROM: "Chart:" + end_key,
            NEPTUNE_RELATIONSHIP_HEADER_TO: "Query:" + start_key,
            NEPTUNE_HEADER_LABEL: 'CHART_OF',
            NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
            NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB
        }

        assert actual is not None
        self.assertEqual(expected, actual_serialized)
        self.assertEqual(neptune_forward_expected, actual_neptune_serialized[0])
        self.assertEqual(neptune_reversed_expected, actual_neptune_serialized[1])
        self.assertIsNone(dashboard_chart.create_next_relation())

    def test_create_records(self) -> None:
        dashboard_chart = DashboardChart(dashboard_group_id='dg_id',
                                         dashboard_id='d_id',
                                         query_id='q_id',
                                         chart_id='c_id',
                                         chart_name='c_name',
                                         chart_type='bar',
                                         chart_url='http://gold.foo/chart'
                                         )

        actual = dashboard_chart.create_next_record()
        actual_serialized = mysql_serializer.serialize_record(actual)
        expected = {
            'rk': '_dashboard://gold.dg_id/d_id/query/q_id/chart/c_id',
            'id': 'c_id',
            'query_rk': '_dashboard://gold.dg_id/d_id/query/q_id',
            'name': 'c_name',
            'type': 'bar',
            'url': 'http://gold.foo/chart'
        }

        assert actual is not None
        self.assertDictEqual(expected, actual_serialized)
        self.assertIsNone(dashboard_chart.create_next_record())

        dashboard_chart = DashboardChart(dashboard_group_id='dg_id',
                                         dashboard_id='d_id',
                                         query_id='q_id',
                                         chart_id='c_id',
                                         chart_url='http://gold.foo.bar/'
                                         )

        actual2 = dashboard_chart.create_next_record()
        actual2_serialized = mysql_serializer.serialize_record(actual2)
        expected2 = {
            'rk': '_dashboard://gold.dg_id/d_id/query/q_id/chart/c_id',
            'id': 'c_id',
            'query_rk': '_dashboard://gold.dg_id/d_id/query/q_id',
            'url': 'http://gold.foo.bar/'
        }

        assert actual2 is not None
        self.assertDictEqual(expected2, actual2_serialized)

    def test_create_atlas_entity(self) -> None:
        dashboard_chart = DashboardChart(dashboard_group_id='dg_id',
                                         dashboard_id='d_id',
                                         query_id='q_id',
                                         chart_id='c_id',
                                         chart_name='c_name',
                                         chart_type='bar',
                                         chart_url='http://gold.foo/chart',
                                         product='superset'
                                         )

        actual = dashboard_chart.create_next_atlas_entity()
        actual_serialized = atlas_serializer.serialize_entity(actual)
        expected = {
            'typeName': 'DashboardChart',
            'operation': 'CREATE',
            'relationships': 'query#DashboardQuery#superset_dashboard://gold.dg_id/d_id/query/q_id',
            'qualifiedName': 'superset_dashboard://gold.dg_id/d_id/query/q_id/chart/c_id',
            'name': 'c_name',
            'type': 'bar',
            'url': 'http://gold.foo/chart'
        }

        assert actual is not None
        self.assertDictEqual(expected, actual_serialized)
        self.assertIsNone(dashboard_chart.create_next_atlas_entity())
