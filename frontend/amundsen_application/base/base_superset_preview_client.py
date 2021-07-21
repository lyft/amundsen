# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import abc
import logging

from flask import Response as FlaskResponse, make_response, jsonify
from http import HTTPStatus
from marshmallow import ValidationError
from requests import Response
from typing import Dict

from amundsen_application.base.base_preview_client import BasePreviewClient
from amundsen_application.models.preview_data import ColumnItem, PreviewData, PreviewDataSchema


class BaseSupersetPreviewClient(BasePreviewClient):
    @abc.abstractmethod
    def __init__(self) -> None:
        self.headers = {}  # type: Dict

    @abc.abstractmethod
    def post_to_sql_json(self, *, params: Dict, headers: Dict) -> Response:
        """
        Returns the post response from Superset's `sql_json` endpoint
        """
        pass  # pragma: no cover

    def get_preview_data(self, params: Dict, optionalHeaders: Dict = None) -> FlaskResponse:
        """
        Returns a FlaskResponse object, where the response data represents a json object
        with the preview data accessible on 'preview_data' key. The preview data should
        match amundsen_application.models.preview_data.PreviewDataSchema
        """
        try:
            # Clone headers so that it does not mutate instance's state
            headers = dict(self.headers)

            # Merge optionalHeaders into headers
            if optionalHeaders is not None:
                headers.update(optionalHeaders)

            # Request preview data
            response = self.post_to_sql_json(params=params, headers=headers)

            # Verify and return the results
            response_dict = response.json()
            columns = [ColumnItem(c['name'], c['type']) for c in response_dict['columns']]
            preview_data = PreviewData(columns, response_dict['data'])
            try:
                data = PreviewDataSchema().dump(preview_data)
                PreviewDataSchema().load(data)  # for validation only
                payload = jsonify({'preview_data': data})
                return make_response(payload, response.status_code)
            except ValidationError as err:
                logging.error("PreviewDataSchema serialization error " + str(err.messages))
                return make_response(jsonify({'preview_data': {}}), HTTPStatus.INTERNAL_SERVER_ERROR)
        except Exception:
            return make_response(jsonify({'preview_data': {}}), HTTPStatus.INTERNAL_SERVER_ERROR)

    def get_feature_preview_data(self, params: Dict, optionalHeaders: Dict = None) -> FlaskResponse:
        pass
