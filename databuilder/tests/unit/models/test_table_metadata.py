# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import copy
import unittest
from typing import Dict, List

from databuilder.models.table_metadata import ColumnMetadata, TableMetadata
from databuilder.serializers import (
    mysql_serializer, neo4_serializer, neptune_serializer,
)
from tests.unit.models.test_fixtures.table_metadata_fixtures import (
    EXPECTED_NEPTUNE_NODES, EXPECTED_RECORDS_MYSQL, EXPECTED_RELATIONSHIPS_NEPTUNE,
)


class TestTableMetadata(unittest.TestCase):
    def setUp(self) -> None:
        super(TestTableMetadata, self).setUp()
        TableMetadata.serialized_nodes_keys = set()
        TableMetadata.serialized_rels_keys = set()
        self.table_metadata = TableMetadata(
            'hive',
            'gold',
            'test_schema1',
            'test_table1',
            'test_table1',
            [
                ColumnMetadata('test_id1', 'description of test_table1', 'bigint', 0),
                ColumnMetadata('test_id2', 'description of test_id2', 'bigint', 1),
                ColumnMetadata('is_active', None, 'boolean', 2),
                ColumnMetadata('source', 'description of source', 'varchar', 3),
                ColumnMetadata('etl_created_at', 'description of etl_created_at', 'timestamp', 4),
                ColumnMetadata('ds', None, 'varchar', 5)
            ]
        )

        self.table_metadata2 = TableMetadata(
            'hive',
            'gold',
            'test_schema1',
            'test_table1',
            'test_table1',
            [
                ColumnMetadata('test_id1', 'description of test_table1', 'bigint', 0),
                ColumnMetadata('test_id2', 'description of test_id2', 'bigint', 1),
                ColumnMetadata('is_active', None, 'boolean', 2),
                ColumnMetadata('source', 'description of source', 'varchar', 3),
                ColumnMetadata('etl_created_at', 'description of etl_created_at', 'timestamp', 4),
                ColumnMetadata('ds', None, 'varchar', 5)
            ]
        )

    def test_serialize(self) -> None:
        self.expected_nodes_deduped = [
            {'name': 'test_table1', 'KEY': 'hive://gold.test_schema1/test_table1', 'LABEL': 'Table',
             'is_view:UNQUOTED': False},
            {'description': 'test_table1', 'KEY': 'hive://gold.test_schema1/test_table1/_description',
             'LABEL': 'Description', 'description_source': 'description'},
            {'sort_order:UNQUOTED': 0, 'col_type': 'bigint', 'name': 'test_id1',
             'KEY': 'hive://gold.test_schema1/test_table1/test_id1', 'LABEL': 'Column'},
            {'description': 'description of test_table1',
             'KEY': 'hive://gold.test_schema1/test_table1/test_id1/_description', 'LABEL': 'Description',
             'description_source': 'description'},
            {'sort_order:UNQUOTED': 1, 'col_type': 'bigint', 'name': 'test_id2',
             'KEY': 'hive://gold.test_schema1/test_table1/test_id2', 'LABEL': 'Column'},
            {'description': 'description of test_id2',
             'KEY': 'hive://gold.test_schema1/test_table1/test_id2/_description',
             'LABEL': 'Description', 'description_source': 'description'},
            {'sort_order:UNQUOTED': 2, 'col_type': 'boolean', 'name': 'is_active',
             'KEY': 'hive://gold.test_schema1/test_table1/is_active', 'LABEL': 'Column'},
            {'sort_order:UNQUOTED': 3, 'col_type': 'varchar', 'name': 'source',
             'KEY': 'hive://gold.test_schema1/test_table1/source', 'LABEL': 'Column'},
            {'description': 'description of source', 'KEY': 'hive://gold.test_schema1/test_table1/source/_description',
             'LABEL': 'Description', 'description_source': 'description'},
            {'sort_order:UNQUOTED': 4, 'col_type': 'timestamp', 'name': 'etl_created_at',
             'KEY': 'hive://gold.test_schema1/test_table1/etl_created_at', 'LABEL': 'Column'},
            {'description': 'description of etl_created_at',
             'KEY': 'hive://gold.test_schema1/test_table1/etl_created_at/_description', 'LABEL': 'Description',
             'description_source': 'description'},
            {'sort_order:UNQUOTED': 5, 'col_type': 'varchar', 'name': 'ds',
             'KEY': 'hive://gold.test_schema1/test_table1/ds', 'LABEL': 'Column'}
        ]

        self.expected_nodes = copy.deepcopy(self.expected_nodes_deduped)
        self.expected_nodes.append({'name': 'hive', 'KEY': 'database://hive', 'LABEL': 'Database'})
        self.expected_nodes.append({'name': 'gold', 'KEY': 'hive://gold', 'LABEL': 'Cluster'})
        self.expected_nodes.append({'name': 'test_schema1', 'KEY': 'hive://gold.test_schema1', 'LABEL': 'Schema'})

        self.expected_rels_deduped = [
            {'END_KEY': 'hive://gold.test_schema1/test_table1', 'START_LABEL': 'Schema', 'END_LABEL': 'Table',
             'START_KEY': 'hive://gold.test_schema1', 'TYPE': 'TABLE', 'REVERSE_TYPE': 'TABLE_OF'},
            {'END_KEY': 'hive://gold.test_schema1/test_table1/_description', 'START_LABEL': 'Table',
             'END_LABEL': 'Description', 'START_KEY': 'hive://gold.test_schema1/test_table1', 'TYPE': 'DESCRIPTION',
             'REVERSE_TYPE': 'DESCRIPTION_OF'},
            {'END_KEY': 'hive://gold.test_schema1/test_table1/test_id1', 'START_LABEL': 'Table',
             'END_LABEL': 'Column', 'START_KEY': 'hive://gold.test_schema1/test_table1', 'TYPE': 'COLUMN',
             'REVERSE_TYPE': 'COLUMN_OF'},
            {'END_KEY': 'hive://gold.test_schema1/test_table1/test_id1/_description', 'START_LABEL': 'Column',
             'END_LABEL': 'Description', 'START_KEY': 'hive://gold.test_schema1/test_table1/test_id1',
             'TYPE': 'DESCRIPTION', 'REVERSE_TYPE': 'DESCRIPTION_OF'},
            {'END_KEY': 'hive://gold.test_schema1/test_table1/test_id2', 'START_LABEL': 'Table', 'END_LABEL': 'Column',
             'START_KEY': 'hive://gold.test_schema1/test_table1', 'TYPE': 'COLUMN', 'REVERSE_TYPE': 'COLUMN_OF'},
            {'END_KEY': 'hive://gold.test_schema1/test_table1/test_id2/_description', 'START_LABEL': 'Column',
             'END_LABEL': 'Description', 'START_KEY': 'hive://gold.test_schema1/test_table1/test_id2',
             'TYPE': 'DESCRIPTION', 'REVERSE_TYPE': 'DESCRIPTION_OF'},
            {'END_KEY': 'hive://gold.test_schema1/test_table1/is_active', 'START_LABEL': 'Table', 'END_LABEL': 'Column',
             'START_KEY': 'hive://gold.test_schema1/test_table1', 'TYPE': 'COLUMN', 'REVERSE_TYPE': 'COLUMN_OF'},
            {'END_KEY': 'hive://gold.test_schema1/test_table1/source', 'START_LABEL': 'Table', 'END_LABEL': 'Column',
             'START_KEY': 'hive://gold.test_schema1/test_table1', 'TYPE': 'COLUMN', 'REVERSE_TYPE': 'COLUMN_OF'},
            {'END_KEY': 'hive://gold.test_schema1/test_table1/source/_description', 'START_LABEL': 'Column',
             'END_LABEL': 'Description', 'START_KEY': 'hive://gold.test_schema1/test_table1/source',
             'TYPE': 'DESCRIPTION',
             'REVERSE_TYPE': 'DESCRIPTION_OF'},
            {'END_KEY': 'hive://gold.test_schema1/test_table1/etl_created_at', 'START_LABEL': 'Table',
             'END_LABEL': 'Column', 'START_KEY': 'hive://gold.test_schema1/test_table1', 'TYPE': 'COLUMN',
             'REVERSE_TYPE': 'COLUMN_OF'},
            {'END_KEY': 'hive://gold.test_schema1/test_table1/etl_created_at/_description', 'START_LABEL': 'Column',
             'END_LABEL': 'Description', 'START_KEY': 'hive://gold.test_schema1/test_table1/etl_created_at',
             'TYPE': 'DESCRIPTION', 'REVERSE_TYPE': 'DESCRIPTION_OF'},
            {'END_KEY': 'hive://gold.test_schema1/test_table1/ds', 'START_LABEL': 'Table', 'END_LABEL': 'Column',
             'START_KEY': 'hive://gold.test_schema1/test_table1', 'TYPE': 'COLUMN', 'REVERSE_TYPE': 'COLUMN_OF'}
        ]

        self.expected_rels = copy.deepcopy(self.expected_rels_deduped)
        self.expected_rels.append({'END_KEY': 'hive://gold', 'START_LABEL': 'Database', 'END_LABEL': 'Cluster',
                                   'START_KEY': 'database://hive', 'TYPE': 'CLUSTER', 'REVERSE_TYPE': 'CLUSTER_OF'})
        self.expected_rels.append({'END_KEY': 'hive://gold.test_schema1', 'START_LABEL': 'Cluster',
                                   'END_LABEL': 'Schema', 'START_KEY': 'hive://gold',
                                   'TYPE': 'SCHEMA', 'REVERSE_TYPE': 'SCHEMA_OF'})

        node_row = self.table_metadata.next_node()
        actual = []
        while node_row:
            node_row_serialized = neo4_serializer.serialize_node(node_row)
            actual.append(node_row_serialized)
            node_row = self.table_metadata.next_node()
        for i in range(0, len(self.expected_nodes)):
            self.assertEqual(actual[i], self.expected_nodes[i])

        relation_row = self.table_metadata.next_relation()
        actual = []
        while relation_row:
            relation_row_serialized = neo4_serializer.serialize_relationship(relation_row)
            actual.append(relation_row_serialized)
            relation_row = self.table_metadata.next_relation()
        for i in range(0, len(self.expected_rels)):
            self.assertEqual(actual[i], self.expected_rels[i])

        # 2nd record should not show already serialized database, cluster, and schema
        node_row = self.table_metadata2.next_node()
        actual = []
        while node_row:
            node_row_serialized = neo4_serializer.serialize_node(node_row)
            actual.append(node_row_serialized)
            node_row = self.table_metadata2.next_node()

        self.assertEqual(self.expected_nodes_deduped, actual)

        relation_row = self.table_metadata2.next_relation()
        actual = []
        while relation_row:
            relation_row_serialized = neo4_serializer.serialize_relationship(relation_row)
            actual.append(relation_row_serialized)
            relation_row = self.table_metadata2.next_relation()

        self.assertEqual(self.expected_rels_deduped, actual)

    def test_serialize_neptune(self) -> None:
        node_row = self.table_metadata.next_node()
        actual = []
        while node_row:
            node_row_serialized = neptune_serializer.convert_node(node_row)
            actual.append(node_row_serialized)
            node_row = self.table_metadata.next_node()

        self.assertEqual(EXPECTED_NEPTUNE_NODES, actual)

        relation_row = self.table_metadata.next_relation()
        neptune_actual: List[List[Dict]] = []
        while relation_row:
            relation_row_serialized = neptune_serializer.convert_relationship(relation_row)
            neptune_actual.append(relation_row_serialized)
            relation_row = self.table_metadata.next_relation()
        self.maxDiff = None
        self.assertEqual(EXPECTED_RELATIONSHIPS_NEPTUNE, neptune_actual)

    def test_serialize_mysql(self) -> None:
        actual = []
        record = self.table_metadata.next_record()
        while record:
            serialized_record = mysql_serializer.serialize_record(record)
            actual.append(serialized_record)
            record = self.table_metadata.next_record()

        self.assertEqual(EXPECTED_RECORDS_MYSQL, actual)

    def test_table_attributes(self) -> None:
        self.table_metadata3 = TableMetadata('hive', 'gold', 'test_schema3', 'test_table3', 'test_table3', [
            ColumnMetadata('test_id1', 'description of test_table1', 'bigint', 0),
            ColumnMetadata('test_id2', 'description of test_id2', 'bigint', 1),
            ColumnMetadata('is_active', None, 'boolean', 2),
            ColumnMetadata('source', 'description of source', 'varchar', 3),
            ColumnMetadata('etl_created_at', 'description of etl_created_at', 'timestamp', 4),
            ColumnMetadata('ds', None, 'varchar', 5)], is_view=False, attr1='uri', attr2='attr2')

        node_row = self.table_metadata3.next_node()
        actual = []
        while node_row:
            node_row_serialized = neo4_serializer.serialize_node(node_row)
            actual.append(node_row_serialized)
            node_row = self.table_metadata3.next_node()

        self.assertEqual(actual[0].get('attr1'), 'uri')
        self.assertEqual(actual[0].get('attr2'), 'attr2')

    # TODO NO test can run before serialiable... need to fix
    def test_z_custom_sources(self) -> None:
        self.custom_source = TableMetadata('hive', 'gold', 'test_schema3', 'test_table4', 'test_table4', [
            ColumnMetadata('test_id1', 'description of test_table1', 'bigint', 0),
            ColumnMetadata('test_id2', 'description of test_id2', 'bigint', 1),
            ColumnMetadata('is_active', None, 'boolean', 2),
            ColumnMetadata('source', 'description of source', 'varchar', 3),
            ColumnMetadata('etl_created_at', 'description of etl_created_at', 'timestamp', 4),
            ColumnMetadata('ds', None, 'varchar', 5)], is_view=False, description_source="custom")

        node_row = self.custom_source.next_node()
        actual = []
        while node_row:
            node_row_serialized = neo4_serializer.serialize_node(node_row)
            actual.append(node_row_serialized)
            node_row = self.custom_source.next_node()
        expected = {'LABEL': 'Programmatic_Description',
                    'KEY': 'hive://gold.test_schema3/test_table4/_custom_description',
                    'description_source': 'custom', 'description': 'test_table4'}
        self.assertEqual(actual[1], expected)

    def test_tags_field(self) -> None:
        self.table_metadata4 = TableMetadata('hive', 'gold', 'test_schema4', 'test_table4', 'test_table4', [
            ColumnMetadata('test_id1', 'description of test_table1', 'bigint', 0)],
            is_view=False, tags=['tag1', 'tag2'], attr1='uri', attr2='attr2')

        node_row = self.table_metadata4.next_node()
        actual = []
        while node_row:
            node_row_serialized = neo4_serializer.serialize_node(node_row)
            actual.append(node_row_serialized)
            node_row = self.table_metadata4.next_node()

        self.assertEqual(actual[0].get('attr1'), 'uri')
        self.assertEqual(actual[0].get('attr2'), 'attr2')

        self.assertEqual(actual[2].get('LABEL'), 'Tag')
        self.assertEqual(actual[2].get('KEY'), 'tag1')
        self.assertEqual(actual[3].get('KEY'), 'tag2')

        relation_row = self.table_metadata4.next_relation()
        actual = []
        while relation_row:
            relation_row_serialized = neo4_serializer.serialize_relationship(relation_row)
            actual.append(relation_row_serialized)
            relation_row = self.table_metadata4.next_relation()

        # Table tag relationship
        expected_tab_tag_rel1 = {'END_KEY': 'tag1', 'START_LABEL': 'Table', 'END_LABEL':
                                 'Tag', 'START_KEY': 'hive://gold.test_schema4/test_table4',
                                 'TYPE': 'TAGGED_BY', 'REVERSE_TYPE': 'TAG'}
        expected_tab_tag_rel2 = {'END_KEY': 'tag2', 'START_LABEL': 'Table',
                                 'END_LABEL': 'Tag', 'START_KEY': 'hive://gold.test_schema4/test_table4',
                                 'TYPE': 'TAGGED_BY', 'REVERSE_TYPE': 'TAG'}

        self.assertEqual(actual[2], expected_tab_tag_rel1)
        self.assertEqual(actual[3], expected_tab_tag_rel2)

    def test_col_badge_field(self) -> None:
        self.table_metadata4 = TableMetadata('hive', 'gold', 'test_schema4', 'test_table4', 'test_table4', [
            ColumnMetadata('test_id1', 'description of test_table1', 'bigint', 0, ['col-badge1', 'col-badge2'])],
            is_view=False, attr1='uri', attr2='attr2')

        node_row = self.table_metadata4.next_node()
        actual = []
        while node_row:
            serialized_node_row = neo4_serializer.serialize_node(node_row)
            actual.append(serialized_node_row)
            node_row = self.table_metadata4.next_node()

        self.assertEqual(actual[4].get('KEY'), 'col-badge1')
        self.assertEqual(actual[5].get('KEY'), 'col-badge2')

        relation_row = self.table_metadata4.next_relation()
        actual = []
        while relation_row:
            serialized_relation_row = neo4_serializer.serialize_relationship(relation_row)
            actual.append(serialized_relation_row)
            relation_row = self.table_metadata4.next_relation()

        expected_col_badge_rel1 = {'END_KEY': 'col-badge1', 'START_LABEL': 'Column',
                                   'END_LABEL': 'Badge',
                                   'START_KEY': 'hive://gold.test_schema4/test_table4/test_id1',
                                   'TYPE': 'HAS_BADGE', 'REVERSE_TYPE': 'BADGE_FOR'}
        expected_col_badge_rel2 = {'END_KEY': 'col-badge2', 'START_LABEL': 'Column',
                                   'END_LABEL': 'Badge',
                                   'START_KEY': 'hive://gold.test_schema4/test_table4/test_id1',
                                   'TYPE': 'HAS_BADGE', 'REVERSE_TYPE': 'BADGE_FOR'}

        self.assertEqual(actual[4], expected_col_badge_rel1)
        self.assertEqual(actual[5], expected_col_badge_rel2)

    def test_tags_populated_from_str(self) -> None:
        self.table_metadata5 = TableMetadata('hive', 'gold', 'test_schema5', 'test_table5', 'test_table5', [
            ColumnMetadata('test_id1', 'description of test_table1', 'bigint', 0)], tags="tag3, tag4")

        # Test table tag field populated from str
        node_row = self.table_metadata5.next_node()
        actual = []
        while node_row:
            node_row_serialized = neo4_serializer.serialize_node(node_row)
            actual.append(node_row_serialized)
            node_row = self.table_metadata5.next_node()

        self.assertEqual(actual[2].get('LABEL'), 'Tag')
        self.assertEqual(actual[2].get('KEY'), 'tag3')
        self.assertEqual(actual[3].get('KEY'), 'tag4')

        relation_row = self.table_metadata5.next_relation()
        actual = []
        while relation_row:
            relation_row_serialized = neo4_serializer.serialize_relationship(relation_row)
            actual.append(relation_row_serialized)
            relation_row = self.table_metadata5.next_relation()

        # Table tag relationship
        expected_tab_tag_rel3 = {'END_KEY': 'tag3', 'START_LABEL': 'Table', 'END_LABEL':
                                 'Tag', 'START_KEY': 'hive://gold.test_schema5/test_table5',
                                 'TYPE': 'TAGGED_BY', 'REVERSE_TYPE': 'TAG'}
        expected_tab_tag_rel4 = {'END_KEY': 'tag4', 'START_LABEL': 'Table',
                                 'END_LABEL': 'Tag', 'START_KEY': 'hive://gold.test_schema5/test_table5',
                                 'TYPE': 'TAGGED_BY', 'REVERSE_TYPE': 'TAG'}
        self.assertEqual(actual[2], expected_tab_tag_rel3)
        self.assertEqual(actual[3], expected_tab_tag_rel4)

    def test_tags_arent_populated_from_empty_list_and_str(self) -> None:
        self.table_metadata6 = TableMetadata('hive', 'gold', 'test_schema6', 'test_table6', 'test_table6', [
            ColumnMetadata('test_id1', 'description of test_table1', 'bigint', 0)], tags=[])

        self.table_metadata7 = TableMetadata('hive', 'gold', 'test_schema7', 'test_table7', 'test_table7', [
            ColumnMetadata('test_id1', 'description of test_table1', 'bigint', 0)], tags="")

        # Test table tag fields are not populated from empty List
        node_row = self.table_metadata6.next_node()
        while node_row:
            node_row_serialized = neo4_serializer.serialize_node(node_row)
            self.assertNotEqual(node_row_serialized.get('LABEL'), 'Tag')
            node_row = self.table_metadata6.next_node()

        # Test table tag fields are not populated from empty str
        node_row = self.table_metadata7.next_node()
        while node_row:
            node_row_serialized = neo4_serializer.serialize_node(node_row)
            self.assertNotEqual(node_row_serialized.get('LABEL'), 'Tag')
            node_row = self.table_metadata7.next_node()


if __name__ == '__main__':
    unittest.main()
