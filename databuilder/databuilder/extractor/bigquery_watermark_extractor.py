# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import datetime
import logging
import textwrap
import time
from calendar import timegm
from collections import namedtuple
from typing import (
    Any, Dict, Iterator, List, Tuple, Union,
)

from pyhocon import ConfigTree

from databuilder.extractor.base_bigquery_extractor import BaseBigQueryExtractor, DatasetRef
from databuilder.models.watermark import Watermark

PartitionInfo = namedtuple('PartitionInfo', ['partition_id', 'epoch_created'])

LOGGER = logging.getLogger(__name__)


class BigQueryWatermarkExtractor(BaseBigQueryExtractor):

    def init(self, conf: ConfigTree) -> None:
        BaseBigQueryExtractor.init(self, conf)
        self.iter: Iterator[Watermark] = iter(self._iterate_over_tables())

    def get_scope(self) -> str:
        return 'extractor.bigquery_watermarks'

    def _retrieve_tables(self,
                         dataset: DatasetRef
                         ) -> Iterator[Watermark]:
        sharded_table_watermarks: Dict[str, Dict[str, Union[str, Any]]] = {}
        cutoff_time_in_epoch = timegm(time.strptime(self.cutoff_time, BigQueryWatermarkExtractor.DATE_TIME_FORMAT))

        for page in self._page_table_list_results(dataset):
            if 'tables' not in page:
                continue

            for table in page['tables']:
                tableRef = table['tableReference']
                table_id = tableRef['tableId']
                table_creation_time = float(table['creationTime']) / 1000
                # only extract watermark metadata for tables created before the cut-off time
                if table_creation_time < cutoff_time_in_epoch:
                    # BigQuery tables that have numeric suffix starts with a date are
                    # considered date range tables.
                    # ( e.g. ga_sessions_20190101, ga_sessions_20190102, etc. )
                    # We use these dates in the suffixes to determine high and low watermarks
                    if self._is_sharded_table(table_id):
                        suffix = self._get_sharded_table_suffix(table_id)
                        prefix = table_id[:-len(suffix)]
                        date = suffix[:BaseBigQueryExtractor.DATE_LENGTH]

                        if prefix in sharded_table_watermarks:
                            sharded_table_watermarks[prefix]['low'] = min(
                                sharded_table_watermarks[prefix]['low'], date)
                            sharded_table_watermarks[prefix]['high'] = max(
                                sharded_table_watermarks[prefix]['high'], date)
                        else:
                            sharded_table_watermarks[prefix] = {'high': date, 'low': date, 'table': table}
                    else:
                        partitions = self._get_partitions(table, tableRef)
                        if not partitions:
                            continue
                        low, high = self._get_partition_watermarks(table, tableRef, partitions)
                        yield low
                        yield high

            for prefix, td in sharded_table_watermarks.items():
                table = td['table']
                tableRef = table['tableReference']

                yield Watermark(
                    datetime.datetime.fromtimestamp(float(table['creationTime']) / 1000).strftime('%Y-%m-%d %H:%M:%S'),
                    'bigquery',
                    tableRef['datasetId'],
                    prefix,
                    f'__table__={td["low"]}',
                    part_type="low_watermark",
                    cluster=tableRef['projectId']
                )

                yield Watermark(
                    datetime.datetime.fromtimestamp(float(table['creationTime']) / 1000).strftime('%Y-%m-%d %H:%M:%S'),
                    'bigquery',
                    tableRef['datasetId'],
                    prefix,
                    f'__table__={td["high"]}',
                    part_type="high_watermark",
                    cluster=tableRef['projectId']
                )

    def _get_partitions(self,
                        table: str,
                        tableRef: Dict[str, str]
                        ) -> List[PartitionInfo]:
        if 'timePartitioning' not in table:
            return []

        query = textwrap.dedent("""
        SELECT partition_id,
               TIMESTAMP(creation_time/1000) AS creation_time
        FROM   [{project}:{dataset}.{table}$__PARTITIONS_SUMMARY__]
        WHERE  partition_id <> '__UNPARTITIONED__'
               AND partition_id <> '__NULL__'
        """)
        body = {
            'query': query.format(
                project=tableRef['projectId'],
                dataset=tableRef['datasetId'],
                table=tableRef['tableId']),
            'useLegacySql': True
        }
        result = self.bigquery_service.jobs().query(projectId=self.project_id, body=body).execute()

        if 'rows' not in result:
            return []

        return [PartitionInfo(row['f'][0]['v'], row['f'][1]['v']) for row in result['rows']]

    def _get_partition_watermarks(self,
                                  table: Dict[str, Any],
                                  tableRef: Dict[str, str],
                                  partitions: List[PartitionInfo]
                                  ) -> Tuple[Watermark, Watermark]:
        if 'field' in table['timePartitioning']:
            field = table['timePartitioning']['field']
        else:
            field = '_PARTITIONTIME'

        low = min(partitions, key=lambda t: t.partition_id)
        low_wm = Watermark(
            datetime.datetime.fromtimestamp(float(low.epoch_created)).strftime('%Y-%m-%d %H:%M:%S'),
            'bigquery',
            tableRef['datasetId'],
            tableRef['tableId'],
            f'{field}={low.partition_id}',
            part_type="low_watermark",
            cluster=tableRef['projectId']
        )

        high = max(partitions, key=lambda t: t.partition_id)
        high_wm = Watermark(
            datetime.datetime.fromtimestamp(float(high.epoch_created)).strftime('%Y-%m-%d %H:%M:%S'),
            'bigquery',
            tableRef['datasetId'],
            tableRef['tableId'],
            f'{field}={high.partition_id}',
            part_type="high_watermark",
            cluster=tableRef['projectId']
        )

        return low_wm, high_wm
