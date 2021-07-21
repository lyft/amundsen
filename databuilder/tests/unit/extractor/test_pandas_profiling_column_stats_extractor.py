import unittest
from typing import Any

from mock import MagicMock
from pyhocon import ConfigFactory

from databuilder import Scoped
from databuilder.extractor.pandas_profiling_column_stats_extractor import PandasProfilingColumnStatsExtractor
from databuilder.models.table_stats import TableColumnStats


class TestPandasProfilingColumnStatsExtractor(unittest.TestCase):
    report_data = {
        'analysis': {
            'date_start': '2021-05-17 10:10:15.142044'
        },
        'variables': {
            'column_1': {
                'mean': 5.120,
                'max': 15.23456
            },
            'column_2': {
                'mean': 10
            }
        }
    }

    def setUp(self) -> None:
        config = {'extractor.pandas_profiling.file_path': None}
        config = ConfigFactory.from_dict({**config, **self._common_params()})

        self.config = config

    @staticmethod
    def _common_params() -> Any:
        return {'extractor.pandas_profiling.table_name': 'table_name',
                'extractor.pandas_profiling.schema_name': 'schema_name',
                'extractor.pandas_profiling.database_name': 'database_name',
                'extractor.pandas_profiling.cluster_name': 'cluster_name'}

    def _get_extractor(self) -> Any:
        extractor = PandasProfilingColumnStatsExtractor()
        extractor.init(Scoped.get_scoped_conf(conf=self.config, scope=extractor.get_scope()))

        return extractor

    def test_extractor(self) -> None:
        extractor = self._get_extractor()

        extractor._load_report = MagicMock(return_value=self.report_data)

        common = {
            'db': self._common_params().get('extractor.pandas_profiling.database_name'),
            'schema': self._common_params().get('extractor.pandas_profiling.schema_name'),
            'table_name': self._common_params().get('extractor.pandas_profiling.table_name'),
            'cluster': self._common_params().get('extractor.pandas_profiling.cluster_name'),
            'start_epoch': '1621246215',
            'end_epoch': '0'
        }
        compare_params = {'table', 'schema', 'db', 'col_name', 'start_epoch',
                          'end_epoch', 'cluster', 'stat_type', 'stat_val'}
        expected = [
            {x: spec[x] for x in compare_params if x in spec} for spec in
            [
                TableColumnStats(**{**dict(stat_name='Mean', stat_val='5.12', col_name='column_1'), **common}).__dict__,
                TableColumnStats(
                    **{**dict(stat_name='Maximum', stat_val='15.235', col_name='column_1'), **common}).__dict__,
                TableColumnStats(**{**dict(stat_name='Mean', stat_val='10.0', col_name='column_2'), **common}).__dict__,
            ]
        ]

        result = []

        while True:
            stat = extractor.extract()

            if stat:
                result.append(stat)
            else:
                break

        result_spec = [{x: spec.__dict__[x] for x in compare_params if x in spec.__dict__} for spec in result]

        for r in result:
            self.assertIsInstance(r, TableColumnStats)

        self.assertListEqual(expected, result_spec)
