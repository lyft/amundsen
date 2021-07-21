# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import unittest
from unittest.mock import ANY

from databuilder.models.schema.schema import SchemaModel
from databuilder.serializers import (
    mysql_serializer, neo4_serializer, neptune_serializer,
)
from databuilder.serializers.neptune_serializer import (
    METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT, NEPTUNE_CREATION_TYPE_JOB,
    NEPTUNE_CREATION_TYPE_NODE_PROPERTY_NAME_BULK_LOADER_FORMAT,
    NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT, NEPTUNE_HEADER_ID, NEPTUNE_HEADER_LABEL,
    NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT, NEPTUNE_RELATIONSHIP_HEADER_FROM,
    NEPTUNE_RELATIONSHIP_HEADER_TO,
)


class TestSchemaDescription(unittest.TestCase):
    def setUp(self) -> None:
        self.schema = SchemaModel(
            schema_key='db://cluster.schema',
            schema='schema_name',
            description='foo'
        )

    def test_create_nodes(self) -> None:
        schema_node = self.schema.create_next_node()
        serialized_schema_node = neo4_serializer.serialize_node(schema_node)
        schema_desc_node = self.schema.create_next_node()
        serialized_schema_desc_node = neo4_serializer.serialize_node(schema_desc_node)
        self.assertDictEqual(
            serialized_schema_node,
            {'name': 'schema_name', 'KEY': 'db://cluster.schema', 'LABEL': 'Schema'}
        )
        self.assertDictEqual(serialized_schema_desc_node,
                             {'description_source': 'description', 'description': 'foo',
                              'KEY': 'db://cluster.schema/_description', 'LABEL': 'Description'}
                             )
        self.assertIsNone(self.schema.create_next_node())

    def test_create_nodes_neptune(self) -> None:
        schema_node = self.schema.create_next_node()
        expected_serialized_schema_node = {
            NEPTUNE_HEADER_ID: 'Schema:db://cluster.schema',
            METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: 'db://cluster.schema',
            NEPTUNE_HEADER_LABEL: 'Schema',
            NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
            NEPTUNE_CREATION_TYPE_NODE_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB,
            'name:String(single)': 'schema_name',
        }
        serialized_schema_node = neptune_serializer.convert_node(schema_node)
        self.assertDictEqual(
            expected_serialized_schema_node,
            serialized_schema_node
        )
        schema_desc_node = self.schema.create_next_node()
        excepted_serialized_schema_desc_node = {
            NEPTUNE_HEADER_ID: 'Description:db://cluster.schema/_description',
            METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: 'db://cluster.schema/_description',
            NEPTUNE_HEADER_LABEL: 'Description',
            NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
            NEPTUNE_CREATION_TYPE_NODE_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB,
            'description_source:String(single)': 'description',
            'description:String(single)': 'foo',
        }
        serialized_schema_desc_node = neptune_serializer.convert_node(schema_desc_node)
        self.assertDictEqual(
            excepted_serialized_schema_desc_node,
            serialized_schema_desc_node
        )

    def test_create_nodes_no_description(self) -> None:

        schema = SchemaModel(schema_key='db://cluster.schema',
                             schema='schema_name')

        schema_node = schema.create_next_node()
        serialized_schema_node = neo4_serializer.serialize_node(schema_node)

        self.assertDictEqual(serialized_schema_node,
                             {'name': 'schema_name', 'KEY': 'db://cluster.schema', 'LABEL': 'Schema'})
        self.assertIsNone(schema.create_next_node())

    def test_create_nodes_programmatic_description(self) -> None:

        schema = SchemaModel(schema_key='db://cluster.schema',
                             schema='schema_name',
                             description='foo',
                             description_source='bar')

        schema_node = schema.create_next_node()
        serialized_schema_node = neo4_serializer.serialize_node(schema_node)
        schema_desc_node = schema.create_next_node()
        serialized_schema_prod_desc_node = neo4_serializer.serialize_node(schema_desc_node)

        self.assertDictEqual(serialized_schema_node,
                             {'name': 'schema_name', 'KEY': 'db://cluster.schema', 'LABEL': 'Schema'})
        self.assertDictEqual(serialized_schema_prod_desc_node,
                             {'description_source': 'bar', 'description': 'foo',
                              'KEY': 'db://cluster.schema/_bar_description', 'LABEL': 'Programmatic_Description'})
        self.assertIsNone(schema.create_next_node())

    def test_create_relation(self) -> None:
        actual = self.schema.create_next_relation()
        serialized_actual = neo4_serializer.serialize_relationship(actual)
        expected = {'END_KEY': 'db://cluster.schema/_description', 'START_LABEL': 'Schema', 'END_LABEL': 'Description',
                    'START_KEY': 'db://cluster.schema', 'TYPE': 'DESCRIPTION', 'REVERSE_TYPE': 'DESCRIPTION_OF'}

        self.assertEqual(expected, serialized_actual)
        self.assertIsNone(self.schema.create_next_relation())

    def test_create_relation_neptune(self) -> None:
        actual = self.schema.create_next_relation()
        serialized_actual = neptune_serializer.convert_relationship(actual)
        forward_header_id = "{label}:{from_vertex_id}_{to_vertex_id}".format(
            from_vertex_id='Schema:db://cluster.schema',
            to_vertex_id='Description:db://cluster.schema/_description',
            label='DESCRIPTION'
        )
        reverse_header_id = "{label}:{from_vertex_id}_{to_vertex_id}".format(
            from_vertex_id='Description:db://cluster.schema/_description',
            to_vertex_id='Schema:db://cluster.schema',
            label='DESCRIPTION_OF'
        )

        neptune_forward_expected = {
            NEPTUNE_HEADER_ID: forward_header_id,
            METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: forward_header_id,
            NEPTUNE_RELATIONSHIP_HEADER_FROM: 'Schema:db://cluster.schema',
            NEPTUNE_RELATIONSHIP_HEADER_TO: 'Description:db://cluster.schema/_description',
            NEPTUNE_HEADER_LABEL: 'DESCRIPTION',
            NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
            NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB
        }

        neptune_reversed_expected = {
            NEPTUNE_HEADER_ID: reverse_header_id,
            METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: reverse_header_id,
            NEPTUNE_RELATIONSHIP_HEADER_FROM: 'Description:db://cluster.schema/_description',
            NEPTUNE_RELATIONSHIP_HEADER_TO: 'Schema:db://cluster.schema',
            NEPTUNE_HEADER_LABEL: 'DESCRIPTION_OF',
            NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
            NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB
        }

        self.maxDiff = None
        self.assertDictEqual(serialized_actual[0], neptune_forward_expected)
        self.assertDictEqual(serialized_actual[1], neptune_reversed_expected)

    def test_create_relation_no_description(self) -> None:
        schema = SchemaModel(schema_key='db://cluster.schema',
                             schema='schema_name')

        self.assertIsNone(schema.create_next_relation())

    def test_create_relation_programmatic_description(self) -> None:
        schema = SchemaModel(schema_key='db://cluster.schema',
                             schema='schema_name',
                             description='foo',
                             description_source='bar')

        actual = schema.create_next_relation()
        serialized_actual = neo4_serializer.serialize_relationship(actual)
        expected = {
            'END_KEY': 'db://cluster.schema/_bar_description', 'START_LABEL': 'Schema',
            'END_LABEL': 'Programmatic_Description', 'START_KEY': 'db://cluster.schema', 'TYPE': 'DESCRIPTION',
            'REVERSE_TYPE': 'DESCRIPTION_OF'
        }

        self.assertEqual(expected, serialized_actual)
        self.assertIsNone(schema.create_next_relation())

    def test_create_records(self) -> None:
        schema_record = self.schema.create_next_record()
        serialized_schema_record = mysql_serializer.serialize_record(schema_record)
        schema_desc_record = self.schema.create_next_record()
        serialized_schema_desc_record = mysql_serializer.serialize_record(schema_desc_record)
        self.assertDictEqual(serialized_schema_record, {'rk': 'db://cluster.schema', 'name': 'schema_name',
                                                        'cluster_rk': 'db://cluster'})
        self.assertDictEqual(serialized_schema_desc_record, {'rk': 'db://cluster.schema/_description',
                                                             'description_source': 'description', 'description': 'foo',
                                                             'schema_rk': 'db://cluster.schema'})

    def test_create_records_no_description(self) -> None:
        schema = SchemaModel(schema_key='db://cluster.schema',
                             schema='schema_name')
        schema_record = schema.create_next_record()
        serialized_schema_record = mysql_serializer.serialize_record(schema_record)
        self.assertDictEqual(serialized_schema_record, {'rk': 'db://cluster.schema', 'name': 'schema_name',
                                                        'cluster_rk': 'db://cluster'})
        self.assertIsNone(schema.create_next_record())

    def test_create_records_programmatic_description(self) -> None:
        schema = SchemaModel(schema_key='db://cluster.schema',
                             schema='schema_name',
                             description='foo',
                             description_source='bar')

        schema_record = schema.create_next_record()
        serialized_schema_record = mysql_serializer.serialize_record(schema_record)
        schema_prog_desc_record = schema.create_next_record()
        serialized_schema_prog_desc_record = mysql_serializer.serialize_record(schema_prog_desc_record)
        self.assertDictEqual(serialized_schema_record, {'rk': 'db://cluster.schema', 'name': 'schema_name',
                                                        'cluster_rk': 'db://cluster'})
        self.assertDictEqual(serialized_schema_prog_desc_record, {'rk': 'db://cluster.schema/_bar_description',
                                                                  'description_source': 'bar',
                                                                  'description': 'foo',
                                                                  'schema_rk': 'db://cluster.schema'})

    def test_get_cluster_key(self) -> None:
        schema_key = 'a123b_staging://cluster.schema'
        schema_name = 'schema_name'
        schema = SchemaModel(schema_key=schema_key, schema=schema_name)
        assert schema._get_cluster_key(schema_key) == 'a123b_staging://cluster'

        failed_schema_key_1 = 'a123b.staging://cluster.schema'
        self.assertRaises(Exception, SchemaModel, schema_key=failed_schema_key_1, schema_name=schema_name)

        failed_schema_key_2 = 'a123b-staging://cluster.schema'
        self.assertRaises(Exception, SchemaModel, schema_key=failed_schema_key_2, schema_name=schema_name)
