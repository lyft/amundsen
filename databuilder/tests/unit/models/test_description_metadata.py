# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import unittest

from databuilder.models.table_metadata import DescriptionMetadata
from databuilder.serializers import neo4_serializer


class TestDescriptionMetadata(unittest.TestCase):
    def test_raise_exception_when_missing_data(self) -> None:
        # assert raise when missing description node key
        self.assertRaises(
            Exception,
            DescriptionMetadata(text='test_text').next_node
        )
        DescriptionMetadata(text='test_text', description_key='test_key').next_node()
        DescriptionMetadata(text='test_text', start_key='start_key').next_node()

        # assert raise when missing relation start label
        self.assertRaises(
            Exception,
            DescriptionMetadata(text='test_text', start_key='start_key').next_relation
        )
        DescriptionMetadata(text='test_text', start_key='test_key', start_label='Table').next_relation()

        # assert raise when missing relation start key
        self.assertRaises(
            Exception,
            DescriptionMetadata(text='test_text', description_key='test_key', start_label='Table').next_relation
        )

    def test_serialize_table_description_metadata(self) -> None:
        description_metadata = DescriptionMetadata(
            text='test text 1',
            start_label='Table',
            start_key='test_start_key'
        )
        node_row = description_metadata.next_node()
        actual = []
        while node_row:
            node_row_serialized = neo4_serializer.serialize_node(node_row)
            actual.append(node_row_serialized)
            node_row = description_metadata.next_node()
        expected = [
            {'description': 'test text 1', 'KEY': 'test_start_key/_description',
             'LABEL': 'Description', 'description_source': 'description'},
        ]
        self.assertEqual(actual, expected)

        relation_row = description_metadata.next_relation()
        actual = []
        while relation_row:
            relation_row_serialized = neo4_serializer.serialize_relationship(relation_row)
            actual.append(relation_row_serialized)
            relation_row = description_metadata.next_relation()
        expected = [
            {'START_KEY': 'test_start_key', 'START_LABEL': 'Table', 'END_KEY': 'test_start_key/_description',
             'END_LABEL': 'Description', 'TYPE': 'DESCRIPTION', 'REVERSE_TYPE': 'DESCRIPTION_OF'}
        ]
        self.assertEqual(actual, expected)

    def test_serialize_column_description_metadata(self) -> None:
        description_metadata = DescriptionMetadata(
            text='test text 2',
            start_label='Column',
            start_key='test_start_key',
            description_key='customized_key'
        )
        node_row = description_metadata.next_node()
        actual = []
        while node_row:
            node_row_serialized = neo4_serializer.serialize_node(node_row)
            actual.append(node_row_serialized)
            node_row = description_metadata.next_node()
        expected = [
            {'description': 'test text 2', 'KEY': 'customized_key',
             'LABEL': 'Description', 'description_source': 'description'},
        ]
        self.assertEqual(actual, expected)

        relation_row = description_metadata.next_relation()
        actual = []
        while relation_row:
            relation_row_serialized = neo4_serializer.serialize_relationship(relation_row)
            actual.append(relation_row_serialized)
            relation_row = description_metadata.next_relation()
        expected = [
            {'START_KEY': 'test_start_key', 'START_LABEL': 'Column', 'END_KEY': 'customized_key',
             'END_LABEL': 'Description', 'TYPE': 'DESCRIPTION', 'REVERSE_TYPE': 'DESCRIPTION_OF'}
        ]
        self.assertEqual(actual, expected)

    def test_serialize_column_with_source_description_metadata(self) -> None:
        description_metadata = DescriptionMetadata(
            text='test text 3',
            start_label='Column',
            start_key='test_start_key',
            description_key='customized_key',
            source='external',
        )
        node_row = description_metadata.next_node()
        actual = []
        while node_row:
            node_row_serialized = neo4_serializer.serialize_node(node_row)
            actual.append(node_row_serialized)
            node_row = description_metadata.next_node()
        expected = [
            {'description': 'test text 3', 'KEY': 'customized_key',
             'LABEL': 'Programmatic_Description', 'description_source': 'external'},
        ]
        self.assertEqual(actual, expected)

        relation_row = description_metadata.next_relation()
        actual = []
        while relation_row:
            relation_row_serialized = neo4_serializer.serialize_relationship(relation_row)
            actual.append(relation_row_serialized)
            relation_row = description_metadata.next_relation()
        expected = [
            {'START_KEY': 'test_start_key', 'START_LABEL': 'Column', 'END_KEY': 'customized_key',
             'END_LABEL': 'Programmatic_Description', 'TYPE': 'DESCRIPTION', 'REVERSE_TYPE': 'DESCRIPTION_OF'}
        ]
        self.assertEqual(actual, expected)
