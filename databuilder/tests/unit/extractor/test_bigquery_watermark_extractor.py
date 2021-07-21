# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import logging
import unittest
from datetime import datetime
from typing import Any

from mock import Mock, patch
from pyhocon import ConfigFactory

from databuilder import Scoped
from databuilder.extractor.bigquery_watermark_extractor import BigQueryWatermarkExtractor

logging.basicConfig(level=logging.INFO)

NO_DATASETS = {'kind': 'bigquery#datasetList', 'etag': '1B2M2Y8AsgTpgAmY7PhCfg=='}
ONE_DATASET = {
    'kind': 'bigquery#datasetList', 'etag': 'yScH5WIHeNUBF9b/VKybXA==',
    'datasets': [{
        'kind': 'bigquery#dataset',
        'id': 'your-project-here:empty',
        'datasetReference': {'datasetId': 'empty', 'projectId': 'your-project-here'},
        'location': 'US'
    }]
}  # noqa
NO_TABLES = {'kind': 'bigquery#tableList', 'etag': '1B2M2Y8AsgTpgAmY7PhCfg==', 'totalItems': 0}
ONE_TABLE = {
    'kind': 'bigquery#tableList', 'etag': 'Iaqrz2TCDIANAOD/Xerkjw==',
    'tables': [{
        'kind': 'bigquery#table',
        'id': 'your-project-here:fdgdfgh.nested_recs',
        'tableReference': {'projectId': 'your-project-here', 'datasetId': 'fdgdfgh', 'tableId': 'nested_recs'},
        'type': 'TABLE',
        'creationTime': '1557578974009'
    }],
    'totalItems': 1
}  # noqa
TIME_PARTITIONED = {
    'kind': 'bigquery#tableList', 'etag': 'Iaqrz2TCDIANAOD/Xerkjw==',
    'tables': [{
        'kind': 'bigquery#table',
        'id': 'your-project-here:fdgdfgh.other',
        'tableReference': {'projectId': 'your-project-here', 'datasetId': 'fdgdfgh', 'tableId': 'other'},
        'type': 'TABLE',
        'timePartitioning': {'type': 'DAY', 'requirePartitionFilter': False},
        'creationTime': '1557577779306'
    }],
    'totalItems': 1
}  # noqa
TIME_PARTITIONED_WITH_FIELD = {
    'kind': 'bigquery#tableList', 'etag': 'Iaqrz2TCDIANAOD/Xerkjw==',
    'tables': [{
        'kind': 'bigquery#table',
        'id': 'your-project-here:fdgdfgh.other',
        'tableReference': {'projectId': 'your-project-here', 'datasetId': 'fdgdfgh', 'tableId': 'other'},
        'type': 'TABLE',
        'timePartitioning': {'type': 'DAY', 'field': 'processed_date', 'requirePartitionFilter': False},
        'creationTime': '1557577779306'
    }],
    'totalItems': 1
}  # noqa
TABLE_DATE_RANGE = {
    'kind': 'bigquery#tableList', 'etag': 'Iaqrz2TCDIANAOD/Xerkjw==',
    'tables': [{
        'kind': 'bigquery#table',
        'id': 'your-project-here:fdgdfgh.other_20190101',
        'tableReference': {'projectId': 'your-project-here', 'datasetId': 'fdgdfgh', 'tableId': 'date_range_20190101'},
        'type': 'TABLE',
        'creationTime': '1557577779306'
    }, {
        'kind': 'bigquery#table',
        'id': 'your-project-here:fdgdfgh.other_20190102',
        'tableReference': {'projectId': 'your-project-here', 'datasetId': 'fdgdfgh', 'tableId': 'date_range_20190102'},
        'type': 'TABLE',
        'creationTime': '1557577779306'
    }],
    'totalItems': 2
}  # noqa
PARTITION_DATA = {
    'kind': 'bigquery#queryResponse',
    'schema': {
        'fields': [{
            'name': 'partition_id',
            'type': 'STRING',
            'mode': 'NULLABLE'
        }, {
            'name': 'creation_time',
            'type': 'TIMESTAMP',
            'mode': 'NULLABLE'
        }]
    },
    'jobReference': {'projectId': 'your-project-here', 'jobId': 'job_bfTRGj3Lv0tRjcrotXbZSgMCpNhY', 'location': 'EU'},
    'totalRows': '3',
    'rows': [{'f': [{'v': '20180802'}, {'v': '1.547512241348E9'}]},
             {'f': [{'v': '20180803'}, {'v': '1.547512241348E9'}]},
             {'f': [{'v': '20180804'}, {'v': '1.547512241348E9'}]}],
    'totalBytesProcessed': '0',
    'jobComplete': True,
    'cacheHit': False
}  # noqa

try:
    FileNotFoundError
except NameError:
    FileNotFoundError = IOError


class MockBigQueryClient():
    def __init__(self,
                 dataset_list_data: Any,
                 table_list_data: Any,
                 partition_data: Any
                 ) -> None:
        self.list_execute = Mock()
        self.list_execute.execute.return_value = table_list_data
        self.tables_method = Mock()
        self.tables_method.list.return_value = self.list_execute
        self.ds_execute = Mock()
        self.ds_execute.execute.return_value = dataset_list_data
        self.ds_list = Mock()
        self.ds_list.list.return_value = self.ds_execute
        self.query_execute = Mock()
        self.query_execute.execute.return_value = partition_data
        self.jobs_query = Mock()
        self.jobs_query.query.return_value = self.query_execute

    def datasets(self) -> Any:
        return self.ds_list

    def tables(self) -> Any:
        return self.tables_method

    def jobs(self) -> Any:
        return self.jobs_query


# Patch fallback auth method to avoid actually calling google API
@patch('google.auth.default', lambda scopes: ['dummy', 'dummy'])
class TestBigQueryWatermarkExtractor(unittest.TestCase):
    def setUp(self) -> None:
        config_dict = {
            f'extractor.bigquery_watermarks.{BigQueryWatermarkExtractor.PROJECT_ID_KEY}':
                'your-project-here'}
        self.conf = ConfigFactory.from_dict(config_dict)

    @patch('databuilder.extractor.base_bigquery_extractor.build')
    def test_can_handle_no_datasets(self, mock_build: Any) -> None:
        mock_build.return_value = MockBigQueryClient(NO_DATASETS, None, None)
        extractor = BigQueryWatermarkExtractor()
        extractor.init(Scoped.get_scoped_conf(conf=self.conf,
                                              scope=extractor.get_scope()))
        result = extractor.extract()
        self.assertIsNone(result)

    @patch('databuilder.extractor.base_bigquery_extractor.build')
    def test_empty_dataset(self, mock_build: Any) -> None:
        mock_build.return_value = MockBigQueryClient(ONE_DATASET, NO_TABLES, None)
        extractor = BigQueryWatermarkExtractor()
        extractor.init(Scoped.get_scoped_conf(conf=self.conf,
                                              scope=extractor.get_scope()))
        result = extractor.extract()
        self.assertIsNone(result)

    @patch('databuilder.extractor.base_bigquery_extractor.build')
    def test_table_without_partitions(self, mock_build: Any) -> None:
        mock_build.return_value = MockBigQueryClient(ONE_DATASET, ONE_TABLE, None)
        extractor = BigQueryWatermarkExtractor()
        extractor.init(Scoped.get_scoped_conf(conf=self.conf,
                                              scope=extractor.get_scope()))
        result = extractor.extract()
        self.assertIsNone(result)

    @patch('databuilder.extractor.base_bigquery_extractor.build')
    def test_table_with_default_partitions(self, mock_build: Any) -> None:
        mock_build.return_value = MockBigQueryClient(ONE_DATASET, TIME_PARTITIONED, PARTITION_DATA)
        extractor = BigQueryWatermarkExtractor()
        extractor.init(Scoped.get_scoped_conf(conf=self.conf,
                                              scope=extractor.get_scope()))
        result = extractor.extract()
        self.assertEqual(result.part_type, 'low_watermark')
        self.assertEqual(result.database, 'bigquery')
        self.assertEqual(result.schema, 'fdgdfgh')
        self.assertEqual(result.table, 'other')
        self.assertEqual(result.cluster, 'your-project-here')
        self.assertEqual(result.create_time, datetime.fromtimestamp(1547512241).strftime('%Y-%m-%d %H:%M:%S'))
        self.assertEqual(result.parts, [('_PARTITIONTIME', '20180802')])

        result = extractor.extract()
        self.assertEqual(result.part_type, 'high_watermark')
        self.assertEqual(result.database, 'bigquery')
        self.assertEqual(result.schema, 'fdgdfgh')
        self.assertEqual(result.table, 'other')
        self.assertEqual(result.cluster, 'your-project-here')
        self.assertEqual(result.create_time, datetime.fromtimestamp(1547512241).strftime('%Y-%m-%d %H:%M:%S'))
        self.assertEqual(result.parts, [('_PARTITIONTIME', '20180804')])

    @patch('databuilder.extractor.base_bigquery_extractor.build')
    def test_table_with_field_partitions(self, mock_build: Any) -> None:
        mock_build.return_value = MockBigQueryClient(ONE_DATASET, TIME_PARTITIONED_WITH_FIELD, PARTITION_DATA)
        extractor = BigQueryWatermarkExtractor()
        extractor.init(Scoped.get_scoped_conf(conf=self.conf,
                                              scope=extractor.get_scope()))
        result = extractor.extract()
        assert result is not None
        self.assertEqual(result.part_type, 'low_watermark')
        self.assertEqual(result.database, 'bigquery')
        self.assertEqual(result.schema, 'fdgdfgh')
        self.assertEqual(result.table, 'other')
        self.assertEqual(result.cluster, 'your-project-here')
        self.assertEqual(result.create_time, datetime.fromtimestamp(1547512241).strftime('%Y-%m-%d %H:%M:%S'))
        self.assertEqual(result.parts, [('processed_date', '20180802')])

        result = extractor.extract()
        assert result is not None
        self.assertEqual(result.part_type, 'high_watermark')
        self.assertEqual(result.database, 'bigquery')
        self.assertEqual(result.schema, 'fdgdfgh')
        self.assertEqual(result.table, 'other')
        self.assertEqual(result.cluster, 'your-project-here')
        self.assertEqual(result.create_time, datetime.fromtimestamp(1547512241).strftime('%Y-%m-%d %H:%M:%S'))
        self.assertEqual(result.parts, [('processed_date', '20180804')])

    @patch('databuilder.extractor.base_bigquery_extractor.build')
    def test_keypath_can_be_set(self, mock_build: Any) -> None:
        config_dict = {
            f'extractor.bigquery_watermarks.{BigQueryWatermarkExtractor.PROJECT_ID_KEY}': 'your-project-here',
            f'extractor.bigquery_watermarks.{BigQueryWatermarkExtractor.KEY_PATH_KEY}': '/tmp/doesnotexist',
        }
        conf = ConfigFactory.from_dict(config_dict)

        mock_build.return_value = MockBigQueryClient(ONE_DATASET, ONE_TABLE, None)
        extractor = BigQueryWatermarkExtractor()

        with self.assertRaises(FileNotFoundError):
            extractor.init(Scoped.get_scoped_conf(conf=conf,
                                                  scope=extractor.get_scope()))

    @patch('databuilder.extractor.base_bigquery_extractor.build')
    def test_table_part_of_table_date_range(self, mock_build: Any) -> None:
        mock_build.return_value = MockBigQueryClient(ONE_DATASET, TABLE_DATE_RANGE, None)
        extractor = BigQueryWatermarkExtractor()
        extractor.init(Scoped.get_scoped_conf(conf=self.conf,
                                              scope=extractor.get_scope()))

        result = extractor.extract()
        assert result is not None
        self.assertEqual(result.part_type, 'low_watermark')
        self.assertEqual(result.database, 'bigquery')
        self.assertEqual(result.schema, 'fdgdfgh')
        self.assertEqual(result.table, 'date_range_')
        self.assertEqual(result.cluster, 'your-project-here')
        self.assertEqual(result.create_time, datetime.fromtimestamp(1557577779).strftime('%Y-%m-%d %H:%M:%S'))
        self.assertEqual(result.parts, [('__table__', '20190101')])

        result = extractor.extract()
        assert result is not None
        self.assertEqual(result.part_type, 'high_watermark')
        self.assertEqual(result.database, 'bigquery')
        self.assertEqual(result.schema, 'fdgdfgh')
        self.assertEqual(result.table, 'date_range_')
        self.assertEqual(result.cluster, 'your-project-here')
        self.assertEqual(result.create_time, datetime.fromtimestamp(1557577779).strftime('%Y-%m-%d %H:%M:%S'))
        self.assertEqual(result.parts, [('__table__', '20190102')])

    @patch('databuilder.extractor.base_bigquery_extractor.build')
    def test_table_creation_time_after_cutoff_time(self, mock_build: Any) -> None:
        config_dict = {
            f'extractor.bigquery_watermarks.{BigQueryWatermarkExtractor.PROJECT_ID_KEY}': 'your-project-here',
            f'extractor.bigquery_watermarks.{BigQueryWatermarkExtractor.CUTOFF_TIME_KEY}': '2019-05-10T20:10:22Z'
        }
        conf = ConfigFactory.from_dict(config_dict)
        mock_build.return_value = MockBigQueryClient(ONE_DATASET, TIME_PARTITIONED, PARTITION_DATA)
        extractor = BigQueryWatermarkExtractor()
        extractor.init(Scoped.get_scoped_conf(conf=conf,
                                              scope=extractor.get_scope()))
        result = extractor.extract()
        self.assertIsNone(result)

    @patch('databuilder.extractor.base_bigquery_extractor.build')
    def test_table_creation_time_before_cutoff_time(self, mock_build: Any) -> None:
        config_dict = {
            f'extractor.bigquery_watermarks.{BigQueryWatermarkExtractor.PROJECT_ID_KEY}': 'your-project-here',
            f'extractor.bigquery_watermarks.{BigQueryWatermarkExtractor.CUTOFF_TIME_KEY}': '2021-04-27T20:10:22Z'
        }
        conf = ConfigFactory.from_dict(config_dict)
        mock_build.return_value = MockBigQueryClient(ONE_DATASET, TIME_PARTITIONED, PARTITION_DATA)
        extractor = BigQueryWatermarkExtractor()
        extractor.init(Scoped.get_scoped_conf(conf=conf,
                                              scope=extractor.get_scope()))
        result = extractor.extract()
        assert result is not None
        self.assertEqual(result.part_type, 'low_watermark')
        self.assertEqual(result.database, 'bigquery')
        self.assertEqual(result.schema, 'fdgdfgh')
        self.assertEqual(result.table, 'other')
        self.assertEqual(result.cluster, 'your-project-here')
        self.assertEqual(result.create_time, datetime.fromtimestamp(1547512241).strftime('%Y-%m-%d %H:%M:%S'))
        self.assertEqual(result.parts, [('_PARTITIONTIME', '20180802')])

        result = extractor.extract()
        self.assertEqual(result.part_type, 'high_watermark')
        self.assertEqual(result.database, 'bigquery')
        self.assertEqual(result.schema, 'fdgdfgh')
        self.assertEqual(result.table, 'other')
        self.assertEqual(result.cluster, 'your-project-here')
        self.assertEqual(result.create_time, datetime.fromtimestamp(1547512241).strftime('%Y-%m-%d %H:%M:%S'))
        self.assertEqual(result.parts, [('_PARTITIONTIME', '20180804')])
