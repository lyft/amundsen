# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from typing import Optional, Tuple

from pyhocon import ConfigTree

from databuilder.extractor.bigquery_usage_extractor import TableColumnUsageTuple
from databuilder.models.table_column_usage import ColumnReader, TableColumnUsage
from databuilder.transformer.base_transformer import Transformer


class BigqueryUsageTransformer(Transformer):

    def init(self, conf: ConfigTree) -> None:
        """
        Transformer to convert TableColumnUsageTuple data to bigquery usage data
        which can be uploaded to Neo4j
        """
        self.conf = conf

    def transform(self, record: Tuple[TableColumnUsageTuple, int]) -> Optional[TableColumnUsage]:
        if not record:
            return None

        (key, count) = record

        if not isinstance(key, TableColumnUsageTuple):
            raise Exception("BigqueryUsageTransformer expects record of type TableColumnUsageTuple")

        col_readers = []
        col_readers.append(ColumnReader(database=key.database,
                                        cluster=key.cluster,
                                        schema=key.schema,
                                        table=key.table,
                                        column=key.column,
                                        user_email=key.email,
                                        read_count=count))

        return TableColumnUsage(col_readers=col_readers)

    def get_scope(self) -> str:
        return 'transformer.bigquery_usage'
