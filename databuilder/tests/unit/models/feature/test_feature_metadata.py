# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import unittest

from databuilder.models.feature.feature_metadata import FeatureMetadata
from databuilder.serializers import neo4_serializer


class TestFeatureMetadata(unittest.TestCase):
    def setUp(self) -> None:
        # reset node cache
        FeatureMetadata.processed_feature_group_keys = set()
        FeatureMetadata.processed_database_keys = set()

        self.full_metadata = FeatureMetadata(
            feature_group='My Feature Group',
            name='feature_123',
            version='2.0.0',
            status='ready',
            entity='Buyer',
            data_type='float',
            availability=['hive', 'dynamo'],
            description='My awesome feature',
            tags=['qa passed', 'core'],
            created_timestamp=1622596581,
        )

        self.required_only_metadata = FeatureMetadata(
            feature_group='My Feature Group',
            name='feature_123',
            version='2.0.0',
        )

        self.expected_nodes_full = [
            {
                'KEY': 'My Feature Group/feature_123/2.0.0',
                'LABEL': 'Feature',
                'name': 'feature_123',
                'version': '2.0.0',
                'status': 'ready',
                'entity': 'Buyer',
                'data_type': 'float',
                'created_timestamp:UNQUOTED': 1622596581,
            },
            {
                'KEY': 'My Feature Group',
                'LABEL': 'Feature_Group',
                'name': 'My Feature Group',
            },
            {
                'KEY': 'My Feature Group/feature_123/2.0.0/_description',
                'LABEL': 'Description',
                'description_source': 'description',
                'description': 'My awesome feature',
            },
            {
                'KEY': 'database://hive',
                'LABEL': 'Database',
                'name': 'hive',
            },
            {
                'KEY': 'database://dynamo',
                'LABEL': 'Database',
                'name': 'dynamo',
            },
            {
                'KEY': 'qa passed',
                'LABEL': 'Tag',
                'tag_type': 'default',
            },
            {
                'KEY': 'core',
                'LABEL': 'Tag',
                'tag_type': 'default',
            },
        ]

        self.expected_rels_full = [
            {
                'START_LABEL': 'Feature',
                'END_LABEL': 'Feature_Group',
                'START_KEY': 'My Feature Group/feature_123/2.0.0',
                'END_KEY': 'My Feature Group',
                'TYPE': 'GROUPED_BY',
                'REVERSE_TYPE': 'GROUPS',
            },
            {
                'START_LABEL': 'Feature',
                'END_LABEL': 'Description',
                'START_KEY': 'My Feature Group/feature_123/2.0.0',
                'END_KEY': 'My Feature Group/feature_123/2.0.0/_description',
                'TYPE': 'DESCRIPTION',
                'REVERSE_TYPE': 'DESCRIPTION_OF',
            },
            {
                'START_LABEL': 'Feature',
                'END_LABEL': 'Database',
                'START_KEY': 'My Feature Group/feature_123/2.0.0',
                'END_KEY': 'database://hive',
                'TYPE': 'FEATURE_AVAILABLE_IN',
                'REVERSE_TYPE': 'AVAILABLE_FEATURE',
            },
            {
                'START_LABEL': 'Feature',
                'END_LABEL': 'Database',
                'START_KEY': 'My Feature Group/feature_123/2.0.0',
                'END_KEY': 'database://dynamo',
                'TYPE': 'FEATURE_AVAILABLE_IN',
                'REVERSE_TYPE': 'AVAILABLE_FEATURE',
            },
            {
                'START_LABEL': 'Feature',
                'END_LABEL': 'Tag',
                'START_KEY': 'My Feature Group/feature_123/2.0.0',
                'END_KEY': 'qa passed',
                'TYPE': 'TAGGED_BY',
                'REVERSE_TYPE': 'TAG',
            },
            {
                'START_LABEL': 'Feature',
                'END_LABEL': 'Tag',
                'START_KEY': 'My Feature Group/feature_123/2.0.0',
                'END_KEY': 'core',
                'TYPE': 'TAGGED_BY',
                'REVERSE_TYPE': 'TAG',
            }
        ]

        self.expected_nodes_required_only = [
            {
                'KEY': 'My Feature Group/feature_123/2.0.0',
                'LABEL': 'Feature',
                'name': 'feature_123',
                'version': '2.0.0',
            },
            {
                'KEY': 'My Feature Group',
                'LABEL': 'Feature_Group',
                'name': 'My Feature Group',
            },
        ]

        self.expected_rels_required_only = [
            {
                'START_LABEL': 'Feature',
                'END_LABEL': 'Feature_Group',
                'START_KEY': 'My Feature Group/feature_123/2.0.0',
                'END_KEY': 'My Feature Group',
                'TYPE': 'GROUPED_BY',
                'REVERSE_TYPE': 'GROUPS',
            },
        ]

    def test_full_example(self) -> None:
        node_row = self.full_metadata.next_node()
        actual = []
        while node_row:
            node_serialized = neo4_serializer.serialize_node(node_row)
            actual.append(node_serialized)
            node_row = self.full_metadata.next_node()

        self.assertEqual(self.expected_nodes_full, actual)

        relation_row = self.full_metadata.next_relation()
        actual = []
        while relation_row:
            relation_serialized = neo4_serializer.serialize_relationship(relation_row)
            actual.append(relation_serialized)
            relation_row = self.full_metadata.next_relation()
        self.assertEqual(self.expected_rels_full, actual)

    def test_required_only_example(self) -> None:
        node_row = self.required_only_metadata.next_node()
        actual = []
        while node_row:
            node_serialized = neo4_serializer.serialize_node(node_row)
            actual.append(node_serialized)
            node_row = self.required_only_metadata.next_node()

        self.assertEqual(self.expected_nodes_required_only, actual)

        relation_row = self.required_only_metadata.next_relation()
        actual = []
        while relation_row:
            relation_serialized = neo4_serializer.serialize_relationship(relation_row)
            actual.append(relation_serialized)
            relation_row = self.required_only_metadata.next_relation()
        self.assertEqual(self.expected_rels_required_only, actual)


if __name__ == '__main__':
    unittest.main()
