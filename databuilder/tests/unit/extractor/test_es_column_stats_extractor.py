import unittest
from typing import Any

from elasticsearch import Elasticsearch
from mock import MagicMock
from pyhocon import ConfigFactory

from databuilder import Scoped
from databuilder.extractor.es_column_stats_extractor import ElasticsearchColumnStatsExtractor
from databuilder.models.table_stats import TableColumnStats


class TestElasticsearchColumnStatsExtractor(unittest.TestCase):
    indices = {
        '.technical_index': {
            'mappings': {
                'doc': {
                    'properties': {
                        'keyword_property': {
                            'type': 'keyword'
                        },
                        'long_property': {
                            'type': 'long'
                        }
                    }
                }
            },
            'aliases': {
                'search_index': {}
            },
            'settings': {
                'number_of_repliacs': 1
            }
        },
        'proper_index': {
            'mappings': {
                'doc': {
                    'properties': {
                        'keyword_property': {
                            'type': 'keyword'
                        },
                        'long_property': {
                            'type': 'long'
                        }
                    }
                }
            },
            'aliases': {
                'search_index': {}
            },
            'settings': {
                'number_of_repliacs': 1
            }
        }
    }

    stats = {
        'aggregations': {
            'stats': {
                'fields': [
                    {
                        'name': 'long_property',
                        'avg': 5,
                        'sum': 10,
                        'count': 2
                    }
                ]
            }
        }
    }

    def setUp(self) -> None:
        params = {'extractor.es_column_stats.schema': 'schema_name',
                  'extractor.es_column_stats.cluster': 'cluster_name',
                  'extractor.es_column_stats.client': Elasticsearch()}

        config = ConfigFactory.from_dict(params)

        self.config = config

    def _get_extractor(self) -> Any:
        extractor = ElasticsearchColumnStatsExtractor()
        extractor.init(Scoped.get_scoped_conf(conf=self.config, scope=extractor.get_scope()))

        return extractor

    def test_extractor_without_technical_data(self) -> None:
        extractor = self._get_extractor()

        extractor.es.indices.get = MagicMock(return_value=self.indices)
        extractor.es.search = MagicMock(return_value=self.stats)

        common = {
            'db': 'elasticsearch',
            'schema': 'schema_name',
            'table_name': 'proper_index',
            'cluster': 'cluster_name',
            'start_epoch': '0',
            'end_epoch': '0'
        }

        compare_params = {'table', 'schema', 'db', 'col_name', 'start_epoch',
                          'end_epoch', 'cluster', 'stat_type', 'stat_val'}
        expected = [
            {x: spec[x] for x in compare_params if x in spec} for spec in
            [
                TableColumnStats(
                    **{**dict(stat_name='avg', stat_val='5', col_name='long_property'), **common}).__dict__,
                TableColumnStats(
                    **{**dict(stat_name='sum', stat_val='10', col_name='long_property'), **common}).__dict__,
                TableColumnStats(
                    **{**dict(stat_name='count', stat_val='2', col_name='long_property'), **common}).__dict__,
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
