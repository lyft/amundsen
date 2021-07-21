# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from http import HTTPStatus
import logging
from typing import Dict, List
from amundsen_application.base.base_preview_client import BasePreviewClient
from amundsen_application.models.preview_data import (
    ColumnItem,
    PreviewData,
    PreviewDataSchema,
)
from flask import Response, make_response, jsonify
from marshmallow import ValidationError
from google.cloud import bigquery


class BaseBigqueryPreviewClient(BasePreviewClient):
    """
    Returns a Response object, where the response data represents a json object
    with the preview data accessible on 'preview_data' key. The preview data should
    match amundsen_application.models.preview_data.PreviewDataSchema
    """

    def __init__(self, bq_client: bigquery.Client, preview_limit: int = 5, previewable_projects: List = None) -> None:
        # Client passed from custom implementation. See example implementation.
        self.bq_client = bq_client
        self.preview_limit = preview_limit
        # List of projects that are approved for whitelisting. None(Default) approves all google projects.
        self.previewable_projects = previewable_projects

    def _bq_list_rows(
        self, gcp_project_id: str, table_project_name: str, table_name: str
    ) -> PreviewData:
        """
        Returns PreviewData from bigquery list rows api.
        """
        pass  # pragma: no cover

    def _column_item_from_bq_schema(self, schemafield: bigquery.SchemaField, key: str = None) -> List:
        """
        Recursively build ColumnItems from the bigquery schema
        """
        all_fields = []
        if schemafield.field_type != "RECORD":
            name = key + "." + schemafield.name if key else schemafield.name
            return [ColumnItem(name, schemafield.field_type)]
        for field in schemafield.fields:
            if key:
                name = key + "." + schemafield.name
            else:
                name = schemafield.name
            all_fields.extend(self._column_item_from_bq_schema(field, name))
        return all_fields

    def get_preview_data(self, params: Dict, optionalHeaders: Dict = None) -> Response:
        if self.previewable_projects and params["cluster"] not in self.previewable_projects:
            return make_response(jsonify({"preview_data": {}}), HTTPStatus.FORBIDDEN)

        preview_data = self._bq_list_rows(
            params["cluster"],
            params["schema"],
            params["tableName"],
        )
        try:
            data = PreviewDataSchema().dump(preview_data)
            PreviewDataSchema().load(data)  # for validation only
            payload = jsonify({"preview_data": data})
            return make_response(payload, HTTPStatus.OK)
        except ValidationError as err:
            logging.error("PreviewDataSchema serialization error + " + str(err.messages))
            return make_response(
                jsonify({"preview_data": {}}), HTTPStatus.INTERNAL_SERVER_ERROR
            )

    def get_feature_preview_data(self, params: Dict, optionalHeaders: Dict = None) -> Response:
        pass
