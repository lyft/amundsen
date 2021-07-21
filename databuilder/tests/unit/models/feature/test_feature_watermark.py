# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import unittest

from databuilder.models.feature.feature_watermark import FeatureWatermark
from databuilder.serializers import neo4_serializer


class TestFeatureWatermark(unittest.TestCase):
    def setUp(self) -> None:
        self.watermark = FeatureWatermark(
            feature_group='group1',
            feature_name='feat_name_123',
            feature_version='2.0.0',
            timestamp=1622596581,
            wm_type='low_watermark'
        )

        self.expected_nodes = [
            {
                'KEY': 'group1/feat_name_123/2.0.0/low_watermark',
                'LABEL': 'Feature_Watermark',
                'timestamp:UNQUOTED': 1622596581,
                'watermark_type': 'low_watermark',
            }
        ]

        self.expected_rels = [
            {
                'START_LABEL': 'Feature',
                'END_LABEL': 'Feature_Watermark',
                'START_KEY': 'group1/feat_name_123/2.0.0',
                'END_KEY': 'group1/feat_name_123/2.0.0/low_watermark',
                'TYPE': 'WATERMARK',
                'REVERSE_TYPE': 'BELONG_TO_FEATURE',
            }
        ]

    def test_basic_feature_watermark(self) -> None:
        node = self.watermark.next_node()
        actual = []
        while node:
            node_serialized = neo4_serializer.serialize_node(node)
            actual.append(node_serialized)
            node = self.watermark.next_node()

        self.assertEqual(self.expected_nodes, actual)

        relation = self.watermark.next_relation()
        actual = []
        while relation:
            relation_serialized = neo4_serializer.serialize_relationship(relation)
            actual.append(relation_serialized)
            relation = self.watermark.next_relation()

        self.assertEqual(self.expected_rels, actual)


if __name__ == '__main__':
    unittest.main()
