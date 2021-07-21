import unittest
from typing import Any

from elasticsearch import Elasticsearch
from mock import MagicMock
from pyhocon import ConfigFactory

from databuilder import Scoped
from databuilder.extractor.es_metadata_extractor import ElasticsearchMetadataExtractor
from databuilder.models.table_metadata import ColumnMetadata, TableMetadata


class TestElasticsearchIndexExtractor(unittest.TestCase):
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

    def setUp(self) -> None:
        params = {'extractor.es_metadata.schema': 'schema_name',
                  'extractor.es_metadata.cluster': 'cluster_name',
                  'extractor.es_metadata.client': Elasticsearch()}

        config = ConfigFactory.from_dict(params)

        self.config = config

    def _get_extractor(self) -> Any:
        extractor = ElasticsearchMetadataExtractor()
        extractor.init(Scoped.get_scoped_conf(conf=self.config, scope=extractor.get_scope()))

        return extractor

    def test_extractor_without_technical_data(self) -> None:
        extractor = self._get_extractor()

        extractor.es.indices.get = MagicMock(return_value=self.indices)

        expected = TableMetadata('elasticsearch', 'cluster_name', 'schema_name', 'proper_index',
                                 None, [ColumnMetadata('keyword_property', '', 'keyword', 0, []),
                                        ColumnMetadata('long_property', '', 'long', 0, [])], False, [])

        result = []

        while True:
            entry = extractor.extract()

            if entry:
                result.append(entry)
            else:
                break

        self.assertEqual(1, len(result))
        self.assertEqual(expected.__repr__(), result[0].__repr__())
