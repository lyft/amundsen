# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import copy
import unittest
from typing import Dict, List
from unittest.mock import ANY

from databuilder.models.dashboard.dashboard_metadata import DashboardMetadata
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


class TestDashboardMetadata(unittest.TestCase):
    def setUp(self) -> None:
        self.full_dashboard_metadata = DashboardMetadata(
            'Product - Jobs.cz',
            'Agent',
            'Agent dashboard description',
            ['test_tag', 'tag2'],
            dashboard_group_description='foo dashboard group description',
            created_timestamp=123456789,
            dashboard_group_url='https://foo.bar/dashboard_group/foo',
            dashboard_url='https://foo.bar/dashboard_group/foo/dashboard/bar'
        )

        # Without tags
        self.dashboard_metadata2 = DashboardMetadata('Product - Atmoskop',
                                                     'Atmoskop',
                                                     'Atmoskop dashboard description',
                                                     [],
                                                     )

        # One common tag with dashboard_metadata, no description
        self.dashboard_metadata3 = DashboardMetadata('Product - Jobs.cz',
                                                     'Dohazovac',
                                                     '',
                                                     ['test_tag', 'tag3']
                                                     )

        # Necessary minimum -- NOT USED
        self.dashboard_metadata4 = DashboardMetadata('',
                                                     'PzR',
                                                     '',
                                                     []
                                                     )

        self.expected_nodes_deduped = [
            {
                'KEY': '_dashboard://gold',
                'LABEL': 'Cluster', 'name': 'gold'
            },
            {
                'created_timestamp:UNQUOTED': 123456789,
                'name': 'Agent',
                'KEY': '_dashboard://gold.Product - Jobs.cz/Agent',
                'LABEL': 'Dashboard',
                'dashboard_url': 'https://foo.bar/dashboard_group/foo/dashboard/bar'
            },
            {'name': 'Product - Jobs.cz', 'KEY': '_dashboard://gold.Product - Jobs.cz', 'LABEL': 'Dashboardgroup',
             'dashboard_group_url': 'https://foo.bar/dashboard_group/foo'},
            {'KEY': '_dashboard://gold.Product - Jobs.cz/_description', 'LABEL': 'Description',
             'description': 'foo dashboard group description'},
            {'description': 'Agent dashboard description',
             'KEY': '_dashboard://gold.Product - Jobs.cz/Agent/_description', 'LABEL': 'Description'},
            {'tag_type': 'dashboard', 'KEY': 'test_tag', 'LABEL': 'Tag'},
            {'tag_type': 'dashboard', 'KEY': 'tag2', 'LABEL': 'Tag'}
        ]

        self.expected_nodes = copy.deepcopy(self.expected_nodes_deduped)

        self.expected_rels_deduped = [
            {'END_KEY': '_dashboard://gold.Product - Jobs.cz', 'END_LABEL': 'Dashboardgroup',
             'REVERSE_TYPE': 'DASHBOARD_GROUP_OF', 'START_KEY': '_dashboard://gold',
             'START_LABEL': 'Cluster', 'TYPE': 'DASHBOARD_GROUP'},
            {'END_KEY': '_dashboard://gold.Product - Jobs.cz/_description', 'END_LABEL': 'Description',
             'REVERSE_TYPE': 'DESCRIPTION_OF', 'START_KEY': '_dashboard://gold.Product - Jobs.cz',
             'START_LABEL': 'Dashboardgroup', 'TYPE': 'DESCRIPTION'},
            {'END_KEY': '_dashboard://gold.Product - Jobs.cz', 'START_LABEL': 'Dashboard',
             'END_LABEL': 'Dashboardgroup',
             'START_KEY': '_dashboard://gold.Product - Jobs.cz/Agent', 'TYPE': 'DASHBOARD_OF',
             'REVERSE_TYPE': 'DASHBOARD'},
            {'END_KEY': '_dashboard://gold.Product - Jobs.cz/Agent/_description', 'START_LABEL': 'Dashboard',
             'END_LABEL': 'Description',
             'START_KEY': '_dashboard://gold.Product - Jobs.cz/Agent', 'TYPE': 'DESCRIPTION',
             'REVERSE_TYPE': 'DESCRIPTION_OF'},
            {'END_KEY': 'test_tag', 'START_LABEL': 'Dashboard', 'END_LABEL': 'Tag',
             'START_KEY': '_dashboard://gold.Product - Jobs.cz/Agent', 'TYPE': 'TAG', 'REVERSE_TYPE': 'TAG_OF'},
            {'END_KEY': 'tag2', 'START_LABEL': 'Dashboard', 'END_LABEL': 'Tag',
             'START_KEY': '_dashboard://gold.Product - Jobs.cz/Agent', 'TYPE': 'TAG', 'REVERSE_TYPE': 'TAG_OF'}
        ]

        self.expected_rels = copy.deepcopy(self.expected_rels_deduped)

        self.expected_nodes_deduped2 = [
            {'KEY': '_dashboard://gold', 'LABEL': 'Cluster', 'name': 'gold'},
            {'name': 'Atmoskop', 'KEY': '_dashboard://gold.Product - Atmoskop/Atmoskop', 'LABEL': 'Dashboard'},
            {'name': 'Product - Atmoskop', 'KEY': '_dashboard://gold.Product - Atmoskop', 'LABEL': 'Dashboardgroup'},
            {'description': 'Atmoskop dashboard description',
             'KEY': '_dashboard://gold.Product - Atmoskop/Atmoskop/_description',
             'LABEL': 'Description'},
        ]

        self.expected_nodes2 = copy.deepcopy(self.expected_nodes_deduped2)

        self.expected_rels_deduped2 = [
            {'END_KEY': '_dashboard://gold.Product - Atmoskop', 'END_LABEL': 'Dashboardgroup',
             'REVERSE_TYPE': 'DASHBOARD_GROUP_OF', 'START_KEY': '_dashboard://gold',
             'START_LABEL': 'Cluster', 'TYPE': 'DASHBOARD_GROUP'},
            {'END_KEY': '_dashboard://gold.Product - Atmoskop', 'START_LABEL': 'Dashboard',
             'END_LABEL': 'Dashboardgroup',
             'START_KEY': '_dashboard://gold.Product - Atmoskop/Atmoskop', 'TYPE': 'DASHBOARD_OF',
             'REVERSE_TYPE': 'DASHBOARD'},
            {'END_KEY': '_dashboard://gold.Product - Atmoskop/Atmoskop/_description', 'START_LABEL': 'Dashboard',
             'END_LABEL': 'Description',
             'START_KEY': '_dashboard://gold.Product - Atmoskop/Atmoskop', 'TYPE': 'DESCRIPTION',
             'REVERSE_TYPE': 'DESCRIPTION_OF'},
        ]

        self.expected_rels2 = copy.deepcopy(self.expected_rels_deduped2)

        self.expected_nodes_deduped3 = [
            {'KEY': '_dashboard://gold', 'LABEL': 'Cluster', 'name': 'gold'},
            {'name': 'Dohazovac', 'KEY': '_dashboard://gold.Product - Jobs.cz/Dohazovac', 'LABEL': 'Dashboard'},
            {'name': 'Product - Jobs.cz', 'KEY': '_dashboard://gold.Product - Jobs.cz', 'LABEL': 'Dashboardgroup'},
            {'tag_type': 'dashboard', 'KEY': 'test_tag', 'LABEL': 'Tag'},
            {'tag_type': 'dashboard', 'KEY': 'tag3', 'LABEL': 'Tag'}
        ]

        self.expected_nodes3 = copy.deepcopy(self.expected_nodes_deduped3)

        self.expected_rels_deduped3 = [
            {'END_KEY': '_dashboard://gold.Product - Jobs.cz', 'END_LABEL': 'Dashboardgroup',
             'REVERSE_TYPE': 'DASHBOARD_GROUP_OF', 'START_KEY': '_dashboard://gold',
             'START_LABEL': 'Cluster', 'TYPE': 'DASHBOARD_GROUP'},
            {'END_KEY': '_dashboard://gold.Product - Jobs.cz', 'START_LABEL': 'Dashboard',
             'END_LABEL': 'Dashboardgroup',
             'START_KEY': '_dashboard://gold.Product - Jobs.cz/Dohazovac', 'TYPE': 'DASHBOARD_OF',
             'REVERSE_TYPE': 'DASHBOARD'},
            {'END_KEY': 'test_tag', 'START_LABEL': 'Dashboard', 'END_LABEL': 'Tag',
             'START_KEY': '_dashboard://gold.Product - Jobs.cz/Dohazovac', 'TYPE': 'TAG', 'REVERSE_TYPE': 'TAG_OF'},
            {'END_KEY': 'tag3', 'START_LABEL': 'Dashboard', 'END_LABEL': 'Tag',
             'START_KEY': '_dashboard://gold.Product - Jobs.cz/Dohazovac', 'TYPE': 'TAG', 'REVERSE_TYPE': 'TAG_OF'},
        ]

        self.expected_rels3 = copy.deepcopy(self.expected_rels_deduped3)

    def test_full_example(self) -> None:
        node_row = self.full_dashboard_metadata.next_node()
        actual = []
        while node_row:
            node_serialized = neo4_serializer.serialize_node(node_row)
            actual.append(node_serialized)
            node_row = self.full_dashboard_metadata.next_node()

        self.assertEqual(self.expected_nodes, actual)

        relation_row = self.full_dashboard_metadata.next_relation()
        actual = []
        while relation_row:
            relation_serialized = neo4_serializer.serialize_relationship(relation_row)
            actual.append(relation_serialized)
            relation_row = self.full_dashboard_metadata.next_relation()

        self.assertEqual(self.expected_rels, actual)

    def test_full_dashboard_example_neptune(self) -> None:
        expected_neptune_rels = [
            [
                {
                    NEPTUNE_HEADER_ID: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                        from_vertex_id='Cluster:_dashboard://gold',
                        to_vertex_id='Dashboardgroup:_dashboard://gold.Product - Jobs.cz',
                        label='DASHBOARD_GROUP'
                    ),
                    METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                        from_vertex_id='Cluster:_dashboard://gold',
                        to_vertex_id='Dashboardgroup:_dashboard://gold.Product - Jobs.cz',
                        label='DASHBOARD_GROUP'
                    ),
                    NEPTUNE_RELATIONSHIP_HEADER_FROM: 'Cluster:_dashboard://gold',
                    NEPTUNE_RELATIONSHIP_HEADER_TO: 'Dashboardgroup:_dashboard://gold.Product - Jobs.cz',
                    NEPTUNE_HEADER_LABEL: 'DASHBOARD_GROUP',
                    NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
                    NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB
                },
                {
                    NEPTUNE_HEADER_ID: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                        from_vertex_id='Dashboardgroup:_dashboard://gold.Product - Jobs.cz',
                        to_vertex_id='Cluster:_dashboard://gold',
                        label='DASHBOARD_GROUP_OF'
                    ),
                    METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                        from_vertex_id='Dashboardgroup:_dashboard://gold.Product - Jobs.cz',
                        to_vertex_id='Cluster:_dashboard://gold',
                        label='DASHBOARD_GROUP_OF'
                    ),
                    NEPTUNE_RELATIONSHIP_HEADER_FROM: 'Dashboardgroup:_dashboard://gold.Product - Jobs.cz',
                    NEPTUNE_RELATIONSHIP_HEADER_TO: 'Cluster:_dashboard://gold',
                    NEPTUNE_HEADER_LABEL: 'DASHBOARD_GROUP_OF',
                    NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
                    NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB
                }
            ],
            [
                {
                    NEPTUNE_HEADER_ID: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                        from_vertex_id='Dashboardgroup:_dashboard://gold.Product - Jobs.cz',
                        to_vertex_id='Description:_dashboard://gold.Product - Jobs.cz/_description',
                        label='DESCRIPTION'
                    ),
                    METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                        from_vertex_id='Dashboardgroup:_dashboard://gold.Product - Jobs.cz',
                        to_vertex_id='Description:_dashboard://gold.Product - Jobs.cz/_description',
                        label='DESCRIPTION'
                    ),
                    NEPTUNE_RELATIONSHIP_HEADER_FROM: 'Dashboardgroup:_dashboard://gold.Product - Jobs.cz',
                    NEPTUNE_RELATIONSHIP_HEADER_TO: 'Description:_dashboard://gold.Product - Jobs.cz/_description',
                    NEPTUNE_HEADER_LABEL: 'DESCRIPTION',
                    NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
                    NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB
                },
                {
                    NEPTUNE_HEADER_ID: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                        from_vertex_id='Description:_dashboard://gold.Product - Jobs.cz/_description',
                        to_vertex_id='Dashboardgroup:_dashboard://gold.Product - Jobs.cz',
                        label='DESCRIPTION_OF'
                    ),
                    METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                        from_vertex_id='Description:_dashboard://gold.Product - Jobs.cz/_description',
                        to_vertex_id='Dashboardgroup:_dashboard://gold.Product - Jobs.cz',
                        label='DESCRIPTION_OF'
                    ),
                    NEPTUNE_RELATIONSHIP_HEADER_FROM: 'Description:_dashboard://gold.Product - Jobs.cz/_description',
                    NEPTUNE_RELATIONSHIP_HEADER_TO: 'Dashboardgroup:_dashboard://gold.Product - Jobs.cz',
                    NEPTUNE_HEADER_LABEL: 'DESCRIPTION_OF',
                    NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
                    NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB
                }
            ],
            [
                {
                    NEPTUNE_HEADER_ID: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                        from_vertex_id='Dashboard:_dashboard://gold.Product - Jobs.cz/Agent',
                        to_vertex_id='Dashboardgroup:_dashboard://gold.Product - Jobs.cz',
                        label='DASHBOARD_OF'
                    ),
                    METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                        from_vertex_id='Dashboard:_dashboard://gold.Product - Jobs.cz/Agent',
                        to_vertex_id='Dashboardgroup:_dashboard://gold.Product - Jobs.cz',
                        label='DASHBOARD_OF'
                    ),
                    NEPTUNE_RELATIONSHIP_HEADER_FROM: 'Dashboard:_dashboard://gold.Product - Jobs.cz/Agent',
                    NEPTUNE_RELATIONSHIP_HEADER_TO: 'Dashboardgroup:_dashboard://gold.Product - Jobs.cz',
                    NEPTUNE_HEADER_LABEL: 'DASHBOARD_OF',
                    NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
                    NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB
                },
                {
                    NEPTUNE_HEADER_ID: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                        from_vertex_id='Dashboardgroup:_dashboard://gold.Product - Jobs.cz',
                        to_vertex_id='Dashboard:_dashboard://gold.Product - Jobs.cz/Agent',
                        label='DASHBOARD'
                    ),
                    METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                        from_vertex_id='Dashboardgroup:_dashboard://gold.Product - Jobs.cz',
                        to_vertex_id='Dashboard:_dashboard://gold.Product - Jobs.cz/Agent',
                        label='DASHBOARD'
                    ),
                    NEPTUNE_RELATIONSHIP_HEADER_FROM: 'Dashboardgroup:_dashboard://gold.Product - Jobs.cz',
                    NEPTUNE_RELATIONSHIP_HEADER_TO: 'Dashboard:_dashboard://gold.Product - Jobs.cz/Agent',
                    NEPTUNE_HEADER_LABEL: 'DASHBOARD',
                    NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
                    NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB
                }
            ],
            [
                {
                    NEPTUNE_HEADER_ID: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                        from_vertex_id='Dashboard:_dashboard://gold.Product - Jobs.cz/Agent',
                        to_vertex_id='Description:_dashboard://gold.Product - Jobs.cz/Agent/_description',
                        label='DESCRIPTION'
                    ),
                    METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                        from_vertex_id='Dashboard:_dashboard://gold.Product - Jobs.cz/Agent',
                        to_vertex_id='Description:_dashboard://gold.Product - Jobs.cz/Agent/_description',
                        label='DESCRIPTION'
                    ),
                    NEPTUNE_RELATIONSHIP_HEADER_FROM: 'Dashboard:_dashboard://gold.Product - Jobs.cz/Agent',
                    NEPTUNE_RELATIONSHIP_HEADER_TO:
                        'Description:_dashboard://gold.Product - Jobs.cz/Agent/_description',
                    NEPTUNE_HEADER_LABEL: 'DESCRIPTION',
                    NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
                    NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB
                },
                {
                    NEPTUNE_HEADER_ID: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                        from_vertex_id='Description:_dashboard://gold.Product - Jobs.cz/Agent/_description',
                        to_vertex_id='Dashboard:_dashboard://gold.Product - Jobs.cz/Agent',
                        label='DESCRIPTION_OF'
                    ),
                    METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                        from_vertex_id='Description:_dashboard://gold.Product - Jobs.cz/Agent/_description',
                        to_vertex_id='Dashboard:_dashboard://gold.Product - Jobs.cz/Agent',
                        label='DESCRIPTION_OF'
                    ),
                    NEPTUNE_RELATIONSHIP_HEADER_FROM:
                        'Description:_dashboard://gold.Product - Jobs.cz/Agent/_description',
                    NEPTUNE_RELATIONSHIP_HEADER_TO: 'Dashboard:_dashboard://gold.Product - Jobs.cz/Agent',
                    NEPTUNE_HEADER_LABEL: 'DESCRIPTION_OF',
                    NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
                    NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB
                }
            ],
            [
                {
                    NEPTUNE_HEADER_ID: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                        from_vertex_id='Dashboard:_dashboard://gold.Product - Jobs.cz/Agent',
                        to_vertex_id='Tag:test_tag',
                        label='TAG'
                    ),
                    METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                        from_vertex_id='Dashboard:_dashboard://gold.Product - Jobs.cz/Agent',
                        to_vertex_id='Tag:test_tag',
                        label='TAG'
                    ),
                    NEPTUNE_RELATIONSHIP_HEADER_FROM: 'Dashboard:_dashboard://gold.Product - Jobs.cz/Agent',
                    NEPTUNE_RELATIONSHIP_HEADER_TO: 'Tag:test_tag',
                    NEPTUNE_HEADER_LABEL: 'TAG',
                    NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
                    NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB
                },
                {
                    NEPTUNE_HEADER_ID: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                        from_vertex_id='Tag:test_tag',
                        to_vertex_id='Dashboard:_dashboard://gold.Product - Jobs.cz/Agent',
                        label='TAG_OF'
                    ),
                    METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                        from_vertex_id='Tag:test_tag',
                        to_vertex_id='Dashboard:_dashboard://gold.Product - Jobs.cz/Agent',
                        label='TAG_OF'
                    ),
                    NEPTUNE_RELATIONSHIP_HEADER_FROM: 'Tag:test_tag',
                    NEPTUNE_RELATIONSHIP_HEADER_TO: 'Dashboard:_dashboard://gold.Product - Jobs.cz/Agent',
                    NEPTUNE_HEADER_LABEL: 'TAG_OF',
                    NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
                    NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB
                }
            ],
            [
                {
                    NEPTUNE_HEADER_ID: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                        from_vertex_id='Dashboard:_dashboard://gold.Product - Jobs.cz/Agent',
                        to_vertex_id='Tag:tag2',
                        label='TAG'
                    ),
                    METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                        from_vertex_id='Dashboard:_dashboard://gold.Product - Jobs.cz/Agent',
                        to_vertex_id='Tag:tag2',
                        label='TAG'
                    ),
                    NEPTUNE_RELATIONSHIP_HEADER_FROM: 'Dashboard:_dashboard://gold.Product - Jobs.cz/Agent',
                    NEPTUNE_RELATIONSHIP_HEADER_TO: 'Tag:tag2',
                    NEPTUNE_HEADER_LABEL: 'TAG',
                    NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
                    NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB
                },
                {
                    NEPTUNE_HEADER_ID: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                        from_vertex_id='Tag:tag2',
                        to_vertex_id='Dashboard:_dashboard://gold.Product - Jobs.cz/Agent',
                        label='TAG_OF'
                    ),
                    METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                        from_vertex_id='Tag:tag2',
                        to_vertex_id='Dashboard:_dashboard://gold.Product - Jobs.cz/Agent',
                        label='TAG_OF'
                    ),
                    NEPTUNE_RELATIONSHIP_HEADER_FROM: 'Tag:tag2',
                    NEPTUNE_RELATIONSHIP_HEADER_TO: 'Dashboard:_dashboard://gold.Product - Jobs.cz/Agent',
                    NEPTUNE_HEADER_LABEL: 'TAG_OF',
                    NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
                    NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB
                }
            ],
        ]

        expected_neptune_nodes = [
            {
                NEPTUNE_HEADER_ID: 'Cluster:_dashboard://gold',
                METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: '_dashboard://gold',
                NEPTUNE_HEADER_LABEL: 'Cluster',
                NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
                NEPTUNE_CREATION_TYPE_NODE_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB,
                'name:String(single)': 'gold'
            },
            {
                NEPTUNE_HEADER_ID: 'Dashboard:_dashboard://gold.Product - Jobs.cz/Agent',
                METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: '_dashboard://gold.Product - Jobs.cz/Agent',
                NEPTUNE_HEADER_LABEL: 'Dashboard',
                NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
                NEPTUNE_CREATION_TYPE_NODE_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB,
                'name:String(single)': 'Agent',
                'dashboard_url:String(single)': 'https://foo.bar/dashboard_group/foo/dashboard/bar',
                'created_timestamp:Long(single)': 123456789,
            },
            {
                NEPTUNE_HEADER_ID: 'Dashboardgroup:_dashboard://gold.Product - Jobs.cz',
                METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: '_dashboard://gold.Product - Jobs.cz',
                NEPTUNE_HEADER_LABEL: 'Dashboardgroup',
                NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
                NEPTUNE_CREATION_TYPE_NODE_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB,
                'name:String(single)': 'Product - Jobs.cz',
                'dashboard_group_url:String(single)': 'https://foo.bar/dashboard_group/foo'
            },
            {
                NEPTUNE_HEADER_ID: 'Description:_dashboard://gold.Product - Jobs.cz/_description',
                METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: '_dashboard://gold.Product - Jobs.cz/_description',
                NEPTUNE_HEADER_LABEL: 'Description',
                NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
                NEPTUNE_CREATION_TYPE_NODE_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB,
                'description:String(single)': 'foo dashboard group description',
            },
            {
                NEPTUNE_HEADER_ID: 'Description:_dashboard://gold.Product - Jobs.cz/Agent/_description',
                METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: '_dashboard://gold.Product - Jobs.cz/Agent/_description',
                NEPTUNE_HEADER_LABEL: 'Description',
                NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
                NEPTUNE_CREATION_TYPE_NODE_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB,
                'description:String(single)': 'Agent dashboard description'
            },
            {
                NEPTUNE_HEADER_ID: 'Tag:test_tag',
                METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: 'test_tag',
                NEPTUNE_HEADER_LABEL: 'Tag',
                NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
                NEPTUNE_CREATION_TYPE_NODE_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB,
                'tag_type:String(single)': 'dashboard'
            },
            {
                NEPTUNE_HEADER_ID: 'Tag:tag2',
                METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: 'tag2',
                NEPTUNE_HEADER_LABEL: 'Tag',
                NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
                NEPTUNE_CREATION_TYPE_NODE_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB,
                'tag_type:String(single)': 'dashboard'
            },
        ]
        self.maxDiff = None
        node_row = self.full_dashboard_metadata.next_node()
        actual = []
        while node_row:
            node_serialized = neptune_serializer.convert_node(node_row)
            actual.append(node_serialized)
            node_row = self.full_dashboard_metadata.next_node()

        self.assertEqual(expected_neptune_nodes, actual)

        relation_row = self.full_dashboard_metadata.next_relation()
        neptune_actual: List[List[Dict]] = []
        while relation_row:
            relation_serialized = neptune_serializer.convert_relationship(relation_row)
            neptune_actual.append(relation_serialized)
            relation_row = self.full_dashboard_metadata.next_relation()

        self.assertEqual(expected_neptune_rels, neptune_actual)

    def test_dashboard_without_tags(self) -> None:
        node_row = self.dashboard_metadata2.next_node()
        actual = []
        while node_row:
            node_serialized = neo4_serializer.serialize_node(node_row)
            actual.append(node_serialized)
            node_row = self.dashboard_metadata2.next_node()

        self.assertEqual(self.expected_nodes_deduped2, actual)

        relation_row = self.dashboard_metadata2.next_relation()
        actual = []
        while relation_row:
            relation_serialized = neo4_serializer.serialize_relationship(relation_row)
            actual.append(relation_serialized)
            relation_row = self.dashboard_metadata2.next_relation()

        self.assertEqual(self.expected_rels_deduped2, actual)

    def test_dashboard_no_description(self) -> None:
        node_row = self.dashboard_metadata3.next_node()
        actual = []
        while node_row:
            node_serialized = neo4_serializer.serialize_node(node_row)
            actual.append(node_serialized)
            node_row = self.dashboard_metadata3.next_node()

        self.assertEqual(self.expected_nodes_deduped3, actual)

        relation_row = self.dashboard_metadata3.next_relation()
        actual = []
        while relation_row:
            relation_serialized = neo4_serializer.serialize_relationship(relation_row)
            actual.append(relation_serialized)
            relation_row = self.dashboard_metadata3.next_relation()

        self.assertEqual(self.expected_rels_deduped3, actual)

    def test_dashboard_record_full_example(self) -> None:
        expected_records = [
            {'rk': '_dashboard://gold', 'name': 'gold'},
            {'rk': '_dashboard://gold.Product - Jobs.cz', 'name': 'Product - Jobs.cz',
             'cluster_rk': '_dashboard://gold',
             'dashboard_group_url': 'https://foo.bar/dashboard_group/foo'},
            {'rk': '_dashboard://gold.Product - Jobs.cz/_description', 'description': 'foo dashboard group description',
             'dashboard_group_rk': '_dashboard://gold.Product - Jobs.cz'},
            {'rk': '_dashboard://gold.Product - Jobs.cz/Agent', 'name': 'Agent',
             'dashboard_group_rk': '_dashboard://gold.Product - Jobs.cz', 'created_timestamp': 123456789,
             'dashboard_url': 'https://foo.bar/dashboard_group/foo/dashboard/bar'},
            {'rk': '_dashboard://gold.Product - Jobs.cz/Agent/_description',
             'description': 'Agent dashboard description',
             'dashboard_rk': '_dashboard://gold.Product - Jobs.cz/Agent'},
            {'rk': 'test_tag', 'tag_type': 'dashboard'},
            {'dashboard_rk': '_dashboard://gold.Product - Jobs.cz/Agent', 'tag_rk': 'test_tag'},
            {'rk': 'tag2', 'tag_type': 'dashboard'},
            {'dashboard_rk': '_dashboard://gold.Product - Jobs.cz/Agent', 'tag_rk': 'tag2'}
        ]
        record = self.full_dashboard_metadata.next_record()
        actual = []
        while record:
            record_serialized = mysql_serializer.serialize_record(record)
            actual.append(record_serialized)
            record = self.full_dashboard_metadata.next_record()

        self.assertEqual(expected_records, actual)

    def test_dashboard_record_without_tags(self) -> None:
        expected_records_without_tags = [
            {'rk': '_dashboard://gold', 'name': 'gold'},
            {'rk': '_dashboard://gold.Product - Atmoskop', 'name': 'Product - Atmoskop',
             'cluster_rk': '_dashboard://gold'},
            {'rk': '_dashboard://gold.Product - Atmoskop/Atmoskop', 'name': 'Atmoskop',
             'dashboard_group_rk': '_dashboard://gold.Product - Atmoskop'},
            {'rk': '_dashboard://gold.Product - Atmoskop/Atmoskop/_description',
             'description': 'Atmoskop dashboard description',
             'dashboard_rk': '_dashboard://gold.Product - Atmoskop/Atmoskop'}
        ]
        record = self.dashboard_metadata2.next_record()
        actual = []
        while record:
            record_serialized = mysql_serializer.serialize_record(record)
            actual.append(record_serialized)
            record = self.dashboard_metadata2.next_record()

        self.assertEqual(expected_records_without_tags, actual)

    def test_dashboard_record_no_description(self) -> None:
        expected_records_without_description = [
            {'rk': '_dashboard://gold', 'name': 'gold'},
            {'rk': '_dashboard://gold.Product - Jobs.cz', 'name': 'Product - Jobs.cz',
             'cluster_rk': '_dashboard://gold'},
            {'rk': '_dashboard://gold.Product - Jobs.cz/Dohazovac', 'name': 'Dohazovac',
             'dashboard_group_rk': '_dashboard://gold.Product - Jobs.cz'},
            {'rk': 'test_tag', 'tag_type': 'dashboard'},
            {'dashboard_rk': '_dashboard://gold.Product - Jobs.cz/Dohazovac', 'tag_rk': 'test_tag'},
            {'rk': 'tag3', 'tag_type': 'dashboard'},
            {'dashboard_rk': '_dashboard://gold.Product - Jobs.cz/Dohazovac', 'tag_rk': 'tag3'}
        ]
        record = self.dashboard_metadata3.next_record()
        actual = []
        while record:
            record_serialized = mysql_serializer.serialize_record(record)
            actual.append(record_serialized)
            record = self.dashboard_metadata3.next_record()

        self.assertEqual(expected_records_without_description, actual)

    def test_full_dashboard_example_atlas(self) -> None:

        expected = [{'description': 'foo dashboard group description',
                     'id': 'Product - Jobs.cz',
                     'name': 'Product - Jobs.cz',
                     'operation': 'CREATE',
                     'qualifiedName': '_dashboard://gold.Product - Jobs.cz',
                     'relationships': None,
                     'typeName': 'DashboardGroup',
                     'url': 'https://foo.bar/dashboard_group/foo'},
                    {'cluster': 'gold',
                     'createdTimestamp': 123456789,
                     'description': 'Agent dashboard description',
                     'name': 'Agent',
                     'operation': 'CREATE',
                     'product': '',
                     'qualifiedName': '_dashboard://gold.Product - Jobs.cz/Agent',
                     'relationships': 'group#DashboardGroup#_dashboard://gold.Product - Jobs.cz',
                     'typeName': 'Dashboard',
                     'url': 'https://foo.bar/dashboard_group/foo/dashboard/bar'}]

        entity = self.full_dashboard_metadata.next_atlas_entity()
        actual = []
        while entity:
            record_serialized = atlas_serializer.serialize_entity(entity)
            actual.append(record_serialized)
            entity = self.full_dashboard_metadata.next_atlas_entity()

        self.assertEqual(expected, actual)


if __name__ == '__main__':
    unittest.main()
