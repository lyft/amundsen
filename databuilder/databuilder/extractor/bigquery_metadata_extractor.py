# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import logging
from typing import (
    Any, Dict, List, Set, cast,
)

from pyhocon import ConfigTree

from databuilder.extractor.base_bigquery_extractor import BaseBigQueryExtractor, DatasetRef
from databuilder.models.table_metadata import ColumnMetadata, TableMetadata

LOGGER = logging.getLogger(__name__)


class BigQueryMetadataExtractor(BaseBigQueryExtractor):

    """ A metadata extractor for bigquery tables, taking the schema metadata
    from the google cloud bigquery API's. This extractor goes through all visible
    datasets in the project identified by project_id and iterates over all tables
    it finds. A separate account is configurable through the key_path parameter,
    which should point to a valid json file corresponding to a service account.

    This extractor supports nested columns, which are delimited by a dot (.) in the
    column name.
    """

    def init(self, conf: ConfigTree) -> None:
        BaseBigQueryExtractor.init(self, conf)
        self.iter = iter(self._iterate_over_tables())

    def _retrieve_tables(self, dataset: DatasetRef) -> Any:
        grouped_tables: Set[str] = set([])

        for page in self._page_table_list_results(dataset):
            if 'tables' not in page:
                continue

            for table in page['tables']:
                tableRef = table['tableReference']
                table_id = tableRef['tableId']

                # BigQuery tables that have numeric suffix starting with a date string will be
                # considered date range tables.
                # ( e.g. ga_sessions_20190101, ga_sessions_20190102, etc. )
                if self._is_sharded_table(table_id):
                    # Sharded tables have numeric suffix starting with a date string
                    # and then we only need one schema definition
                    table_prefix = table_id[:-len(self._get_sharded_table_suffix(table_id))]
                    if table_prefix in grouped_tables:
                        # If one table in the date range is processed, then ignore other ones
                        # (it adds too much metadata)
                        continue

                    table_id = table_prefix
                    grouped_tables.add(table_prefix)

                table = self.bigquery_service.tables().get(
                    projectId=tableRef['projectId'],
                    datasetId=tableRef['datasetId'],
                    tableId=tableRef['tableId']).execute(num_retries=BigQueryMetadataExtractor.NUM_RETRIES)

                # BigQuery tables also have interesting metadata about partitioning
                # data location (EU/US), mod/create time, etc... Extract that some other time?
                cols: List[ColumnMetadata] = []
                # Not all tables have schemas
                if 'schema' in table:
                    schema = table['schema']
                    if 'fields' in schema:
                        total_cols = 0
                        for column in schema['fields']:
                            # TRICKY: this mutates :cols:
                            total_cols = self._iterate_over_cols('', column, cols, total_cols + 1)

                table_meta = TableMetadata(
                    database='bigquery',
                    cluster=tableRef['projectId'],
                    schema=tableRef['datasetId'],
                    name=table_id,
                    description=table.get('description', ''),
                    columns=cols,
                    is_view=table['type'] == 'VIEW')

                yield(table_meta)

    def _iterate_over_cols(self,
                           parent: str,
                           column: Dict[str, str],
                           cols: List[ColumnMetadata],
                           total_cols: int) -> int:
        if len(parent) > 0:
            col_name = f'{parent}.{column["name"]}'
        else:
            col_name = column['name']

        if column['type'] == 'RECORD':
            col = ColumnMetadata(
                name=col_name,
                description=column.get('description', ''),
                col_type=column['type'],
                sort_order=total_cols)
            cols.append(col)
            total_cols += 1
            for field in column['fields']:
                # TODO field is actually a TableFieldSchema, per
                # https://cloud.google.com/bigquery/docs/reference/rest/v2/tables#TableFieldSchema
                # however it's typed as str, which is incorrect. Work-around by casting.
                field_casted = cast(Dict[str, str], field)
                total_cols = self._iterate_over_cols(col_name, field_casted, cols, total_cols)
            return total_cols
        else:
            col = ColumnMetadata(
                name=col_name,
                description=column.get('description', ''),
                col_type=column['type'],
                sort_order=total_cols)
            cols.append(col)
            return total_cols + 1

    def get_scope(self) -> str:
        return 'extractor.bigquery_table_metadata'
