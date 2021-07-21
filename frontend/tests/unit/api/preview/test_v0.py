# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import unittest
import json
from http import HTTPStatus

from flask import Response

from amundsen_application import create_app
from amundsen_application.api.preview import v0
from tests.unit.base.test_superset_preview_client import good_json_data, bad_json_data

local_app = create_app('amundsen_application.config.TestConfig', 'tests/templates')
PREVIEW_CLIENT_CLASS = 'amundsen_application.base.examples.example_superset_preview_client.SupersetPreviewClient'


class PreviewTest(unittest.TestCase):

    def setUp(self) -> None:
        local_app.config['PREVIEW_CLIENT_ENABLED'] = True

    def test_no_client_class(self) -> None:
        """
        Test that Not Implemented error is raised when PREVIEW_CLIENT is None
        :return:
        """
        # Reset side effects of other tests to ensure that the results are the
        # same regardless of execution order
        v0.PREVIEW_CLIENT_CLASS = None
        v0.PREVIEW_CLIENT_INSTANCE = None

        local_app.config['PREVIEW_CLIENT'] = None
        with local_app.test_client() as test:
            response = test.post('/api/preview/v0/')
            self.assertEqual(response.status_code, HTTPStatus.NOT_IMPLEMENTED)

    @unittest.mock.patch(PREVIEW_CLIENT_CLASS + '.get_preview_data')
    def test_good_client_response(self, mock_get_preview_data: unittest.mock.Mock) -> None:
        """
        """
        expected_response_json = {
            'msg': 'Success',
            'previewData': {
                'columns': [{}, {}],
                'data': [{'id': 1, 'name': 'Admin'}, {'id': 2, 'name': 'Public'}, {'id': 3, 'name': 'Alpha'}]}
        }

        local_app.config['PREVIEW_CLIENT'] = PREVIEW_CLIENT_CLASS
        response = json.dumps({'preview_data': good_json_data})
        mock_get_preview_data.return_value = Response(response=response,
                                                      status=HTTPStatus.OK)
        with local_app.test_client() as test:
            post_response = test.post('/api/preview/v0/')
            self.assertEqual(post_response.status_code, HTTPStatus.OK)
            self.assertEqual(post_response.json, expected_response_json)

    @unittest.mock.patch(PREVIEW_CLIENT_CLASS + '.get_preview_data')
    def test_bad_client_response(self, mock_get_preview_data: unittest.mock.Mock) -> None:
        """
        """
        expected_response_json = {
            'msg': 'Encountered exception: The preview client did not return a valid PreviewData object',
            'previewData': {}
        }

        local_app.config['PREVIEW_CLIENT'] = PREVIEW_CLIENT_CLASS
        response = json.dumps({'preview_data': bad_json_data})
        mock_get_preview_data.return_value = Response(response=response,
                                                      status=HTTPStatus.OK)
        with local_app.test_client() as test:
            post_response = test.post('/api/preview/v0/')
            self.assertEqual(post_response.status_code,
                             HTTPStatus.INTERNAL_SERVER_ERROR)
            self.assertEqual(post_response.json, expected_response_json)

    @unittest.mock.patch(PREVIEW_CLIENT_CLASS + '.get_feature_preview_data')
    def test_good_client_response_feature(self, mock_get_preview_data: unittest.mock.Mock) -> None:
        """
        """
        expected_response_json = {
            'msg': 'Success',
            'previewData': {
                'columns': [{}, {}],
                'data': [{'id': 1, 'name': 'Admin'}, {'id': 2, 'name': 'Public'}, {'id': 3, 'name': 'Alpha'}]}
        }

        local_app.config['PREVIEW_CLIENT'] = PREVIEW_CLIENT_CLASS
        response = json.dumps({'preview_data': good_json_data})
        mock_get_preview_data.return_value = Response(response=response,
                                                      status=HTTPStatus.OK)
        with local_app.test_client() as test:
            post_response = test.post('/api/preview/v0/feature_preview')
            self.assertEqual(post_response.status_code, HTTPStatus.OK)
            self.assertEqual(post_response.json, expected_response_json)

    @unittest.mock.patch(PREVIEW_CLIENT_CLASS + '.get_feature_preview_data')
    def test_bad_client_response_feature(self, mock_get_preview_data: unittest.mock.Mock) -> None:
        """
        """
        expected_response_json = {
            'msg': 'Encountered exception: The preview client did not return a valid PreviewData object',
            'previewData': {}
        }

        local_app.config['PREVIEW_CLIENT'] = PREVIEW_CLIENT_CLASS
        response = json.dumps({'preview_data': bad_json_data})
        mock_get_preview_data.return_value = Response(response=response,
                                                      status=HTTPStatus.OK)
        with local_app.test_client() as test:
            post_response = test.post('/api/preview/v0/feature_preview')
            self.assertEqual(post_response.status_code,
                             HTTPStatus.INTERNAL_SERVER_ERROR)
            self.assertEqual(post_response.json, expected_response_json)
