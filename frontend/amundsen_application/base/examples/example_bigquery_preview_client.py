# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from amundsen_application.base.base_bigquery_preview_client import BaseBigqueryPreviewClient
from amundsen_application.models.preview_data import (
    PreviewData,
)
from google.cloud import bigquery
from flatten_dict import flatten


class BigqueryPreviewClient(BaseBigqueryPreviewClient):
    """
    Returns a Response object, where the response data represents a json object
    with the preview data accessible on 'preview_data' key. The preview data should
    match amundsen_application.models.preview_data.PreviewDataSchema
    """

    def __init__(self) -> None:
        # Requires access to a service account eg.
        # GOOGLE_APPLICATION_CREDENTIALS=path/serviceaccount.json or a mounted service kubernetes service account.
        super().__init__(bq_client=bigquery.Client("your project here"))

    def _bq_list_rows(
        self, gcp_project_id: str, table_project_name: str, table_name: str
    ) -> PreviewData:
        """
        Returns PreviewData from bigquery list rows api.
        """
        table_id = f"{gcp_project_id}.{table_project_name}.{table_name}"
        rows = self.bq_client.list_rows(table_id, max_results=self.preview_limit)

        # Make flat key ColumnItems from table schema.
        columns = []
        for field in rows.schema:
            extend_with = self._column_item_from_bq_schema(field)
            columns.extend(extend_with)

        # Flatten rows and set missing empty keys to None, to avoid errors with undefined values
        # in frontend
        column_data = []
        for row in rows:
            flat_row = flatten(dict(row), reducer="dot")
            for key in columns:
                if key.column_name not in flat_row:
                    flat_row[key.column_name] = None
            column_data.append(flat_row)

        return PreviewData(columns, column_data)
