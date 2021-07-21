# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import flask
import json
import unittest

from http import HTTPStatus
from amundsen_application.models.preview_data import (
    PreviewData,
)

from amundsen_application.base.base_bigquery_preview_client import BaseBigqueryPreviewClient
from google.cloud.bigquery import SchemaField, Row
from flatten_dict import flatten

app = flask.Flask(__name__)
app.config.from_object('amundsen_application.config.LocalConfig')

test_schema = [
    SchemaField('test_row', 'STRING', 'NULLABLE', 'Some data', (), None),
    SchemaField('test_row1', 'INTEGER', 'NULLABLE', 'Some other data', (), None),
    SchemaField('enrichments', 'RECORD', 'NULLABLE', None, (
        SchemaField('geo_ip', 'RECORD', 'NULLABLE', None, (
            SchemaField('country_code', 'STRING', 'NULLABLE', None, (), None),
            SchemaField('region', 'STRING', 'NULLABLE', None, (), None),
            SchemaField('city', 'STRING', 'NULLABLE', None, (), None),
            SchemaField('coordinates', 'RECORD', 'NULLABLE', None, (
                SchemaField('latitude', 'FLOAT', 'REQUIRED', None, (), None),
                SchemaField('longitude', 'FLOAT', 'REQUIRED', None, (), None)), None)), None),), None),
]

test_rows = [
    Row(('testdata', 7357,
         {'geo_ip': {'country_code': 'US', 'region': '', 'city': '', }}), {
        'test_row': 0, 'test_row1': 1, 'enrichments': 2}),
    Row(('testdata_1', 7357,
         {'geo_ip': {'country_code': 'US', 'region': '', 'city': '', }}), {
        'test_row': 0, 'test_row1': 1, 'enrichments': 2}),
]

expected_results = {'columns': [{'column_name': 'test_row', 'column_type': 'STRING'},
                                {'column_name': 'test_row1', 'column_type': 'INTEGER'},
                                {'column_name': 'enrichments.geo_ip.country_code',
                                 'column_type': 'STRING'},
                                {'column_name': 'enrichments.geo_ip.region',
                                 'column_type': 'STRING'},
                                {'column_name': 'enrichments.geo_ip.city',
                                 'column_type': 'STRING'},
                                {'column_name': 'enrichments.geo_ip.coordinates.latitude',
                                 'column_type': 'FLOAT'},
                                {'column_name': 'enrichments.geo_ip.coordinates.longitude',
                                 'column_type': 'FLOAT'}],
                    'data': [{'enrichments.geo_ip.city': '',
                              'enrichments.geo_ip.coordinates.latitude': None,
                              'enrichments.geo_ip.coordinates.longitude': None,
                              'enrichments.geo_ip.country_code': 'US',
                              'enrichments.geo_ip.region': '',
                              'test_row': 'testdata',
                              'test_row1': 7357},
                             {'enrichments.geo_ip.city': '',
                              'enrichments.geo_ip.coordinates.latitude': None,
                              'enrichments.geo_ip.coordinates.longitude': None,
                              'enrichments.geo_ip.country_code': 'US',
                              'enrichments.geo_ip.region': '',
                              'test_row': 'testdata_1',
                              'test_row1': 7357}],
                    'error_text': ''}


class BigQueryMockClient():
    pass


class MockClient(BaseBigqueryPreviewClient):
    def __init__(self) -> None:
        super().__init__(bq_client=BigQueryMockClient)

    def _bq_list_rows(
        self, gcp_project_id: str, table_project_name: str, table_name: str
    ) -> PreviewData:
        columns = []
        for field in test_schema:
            extend_with = self._column_item_from_bq_schema(field)
            columns.extend(extend_with)
        column_data = []
        for row in test_rows:
            flat_row = flatten(dict(row), reducer="dot")
            for key in columns:
                if key.column_name not in flat_row:
                    flat_row[key.column_name] = None
            column_data.append(flat_row)

        return PreviewData(columns, column_data)


class MockClientNonPreviewableDataset(BaseBigqueryPreviewClient):
    def __init__(self) -> None:
        super().__init__(bq_client=BigQueryMockClient, previewable_projects=['test-project-y'])

    def _bq_list_rows(
        self, gcp_project_id: str, table_project_name: str, table_name: str
    ) -> PreviewData:
        return PreviewData()


class BigqueryPreviewClientTest(unittest.TestCase):
    def test_bigquery_get_preview_data_correct_data_shape(self) -> None:
        """
        Test _bq_list_rows(), which should result in
        a response with 200 and previeable data.
        :return:
        """
        with app.test_request_context():
            response = MockClient().get_preview_data(
                params={"cluster": "test-project-x", "schema": "test-schema", "tableName": "foo"})
            self.assertEqual(json.loads(response.data).get('preview_data'), expected_results)
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_bigquery_get_preview_data_non_previable_dataset(self) -> None:
        """
        Test _bq_list_rows(), which should result in
        a response with 403 due to trying to preview a dataset that is not
        approved for previewing.
        :return:
        """
        with app.test_request_context():
            response = MockClientNonPreviewableDataset().get_preview_data(
                params={"cluster": "test-project-x", "schema": "test-schema", "tableName": "foo"})
            self.assertEqual(json.loads(response.data).get('preview_data'), {})
            self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
