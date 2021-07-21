# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import unittest
from unittest.mock import ANY

from databuilder.models.application import Application
from databuilder.models.graph_serializable import (
    NODE_KEY, NODE_LABEL, RELATION_END_KEY, RELATION_END_LABEL, RELATION_REVERSE_TYPE, RELATION_START_KEY,
    RELATION_START_LABEL, RELATION_TYPE,
)
from databuilder.models.table_metadata import TableMetadata
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


class TestApplication(unittest.TestCase):

    def setUp(self) -> None:
        super(TestApplication, self).setUp()

        self.application = Application(task_id='hive.default.test_table',
                                       dag_id='event_test',
                                       schema='default',
                                       table_name='test_table',
                                       application_url_template='airflow_host.net/admin/airflow/tree?dag_id={dag_id}')

        self.expected_node_results = [{
            NODE_KEY: 'application://gold.airflow/event_test/hive.default.test_table',
            NODE_LABEL: 'Application',
            'application_url': 'airflow_host.net/admin/airflow/tree?dag_id=event_test',
            'id': 'event_test/hive.default.test_table',
            'name': 'Airflow',
            'description': 'Airflow with id event_test/hive.default.test_table'
        }]

        self.expected_relation_results = [{
            RELATION_START_KEY: 'hive://gold.default/test_table',
            RELATION_START_LABEL: TableMetadata.TABLE_NODE_LABEL,
            RELATION_END_KEY: 'application://gold.airflow/event_test/hive.default.test_table',
            RELATION_END_LABEL: 'Application',
            RELATION_TYPE: 'DERIVED_FROM',
            RELATION_REVERSE_TYPE: 'GENERATES'
        }]

    def test_get_table_model_key(self) -> None:
        table = self.application.get_table_model_key()
        self.assertEqual(table, 'hive://gold.default/test_table')

    def test_get_application_model_key(self) -> None:
        application = self.application.get_application_model_key()
        self.assertEqual(application, self.expected_node_results[0][NODE_KEY])

    def test_create_nodes(self) -> None:
        actual = []
        node = self.application.create_next_node()
        while node:
            serialized_next_node = neo4_serializer.serialize_node(node)
            actual.append(serialized_next_node)
            node = self.application.create_next_node()

        self.assertEqual(actual, self.expected_node_results)

    def test_create_nodes_neptune(self) -> None:
        actual = []
        next_node = self.application.create_next_node()
        while next_node:
            serialized_next_node = neptune_serializer.convert_node(next_node)
            actual.append(serialized_next_node)
            next_node = self.application.create_next_node()

        node_id = 'Application:application://gold.airflow/event_test/hive.default.test_table'
        node_key = 'application://gold.airflow/event_test/hive.default.test_table'
        neptune_expected = [{
            NEPTUNE_HEADER_ID: node_id,
            METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: node_key,
            NEPTUNE_HEADER_LABEL: 'Application',
            NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
            NEPTUNE_CREATION_TYPE_NODE_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB,
            'application_url:String(single)': 'airflow_host.net/admin/airflow/tree?dag_id=event_test',
            'id:String(single)': 'event_test/hive.default.test_table',
            'name:String(single)': 'Airflow',
            'description:String(single)': 'Airflow with id event_test/hive.default.test_table',
        }]
        self.assertEqual(neptune_expected, actual)

    def test_create_relation(self) -> None:
        actual = []
        relation = self.application.create_next_relation()
        while relation:
            serialized_relation = neo4_serializer.serialize_relationship(relation)
            actual.append(serialized_relation)
            relation = self.application.create_next_relation()

        self.assertEqual(actual, self.expected_relation_results)

    def test_create_relations_neptune(self) -> None:
        application_id = 'Application:application://gold.airflow/event_test/hive.default.test_table'
        table_id = 'Table:hive://gold.default/test_table'
        neptune_forward_expected = {
            NEPTUNE_HEADER_ID: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                from_vertex_id=table_id,
                to_vertex_id=application_id,
                label='DERIVED_FROM'
            ),
            METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                from_vertex_id=table_id,
                to_vertex_id=application_id,
                label='DERIVED_FROM'
            ),
            NEPTUNE_RELATIONSHIP_HEADER_FROM: table_id,
            NEPTUNE_RELATIONSHIP_HEADER_TO: application_id,
            NEPTUNE_HEADER_LABEL: 'DERIVED_FROM',
            NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
            NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB
        }

        neptune_reversed_expected = {
            NEPTUNE_HEADER_ID: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                from_vertex_id=application_id,
                to_vertex_id=table_id,
                label='GENERATES'
            ),
            METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                from_vertex_id=application_id,
                to_vertex_id=table_id,
                label='GENERATES'
            ),
            NEPTUNE_RELATIONSHIP_HEADER_FROM: application_id,
            NEPTUNE_RELATIONSHIP_HEADER_TO: table_id,
            NEPTUNE_HEADER_LABEL: 'GENERATES',
            NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
            NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB
        }
        neptune_expected = [[neptune_forward_expected, neptune_reversed_expected]]

        actual = []
        next_relation = self.application.create_next_relation()
        while next_relation:
            serialized_next_relation = neptune_serializer.convert_relationship(next_relation)
            actual.append(serialized_next_relation)
            next_relation = self.application.create_next_relation()

        self.assertEqual(actual, neptune_expected)

    def test_create_records(self) -> None:
        expected_application_record = {
            'rk': 'application://gold.airflow/event_test/hive.default.test_table',
            'application_url': 'airflow_host.net/admin/airflow/tree?dag_id=event_test',
            'id': 'event_test/hive.default.test_table',
            'name': 'Airflow',
            'description': 'Airflow with id event_test/hive.default.test_table'
        }
        expected_application_table_record = {
            'rk': 'hive://gold.default/test_table',
            'application_rk': 'application://gold.airflow/event_test/hive.default.test_table'
        }
        expected = [expected_application_record, expected_application_table_record]

        actual = []
        record = self.application.create_next_record()
        while record:
            serialized_record = mysql_serializer.serialize_record(record)
            actual.append(serialized_record)
            record = self.application.create_next_record()

        self.assertEqual(expected, actual)
