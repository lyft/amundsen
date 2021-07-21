# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0


from typing import (
    Any, Dict, Iterator, List, Set, Union,
)

from databuilder.extractor.es_base_extractor import ElasticsearchBaseExtractor
from databuilder.models.table_stats import TableColumnStats


class ElasticsearchColumnStatsExtractor(ElasticsearchBaseExtractor):
    """
    Extractor to extract stats for Elasticsearch mapping attributes.
    """

    def get_scope(self) -> str:
        return 'extractor.es_column_stats'

    def _get_index_stats(self, index_name: str, fields: List[str]) -> List[Dict[str, Any]]:
        query = {
            "size": 0,
            "aggs": {
                "stats": {
                    "matrix_stats": {
                        "fields": fields
                    }
                }
            }
        }

        _data = self.es.search(index=index_name, body=query)

        data = _data.get('aggregations', dict()).get('stats', dict()).get('fields', list())

        return data

    def _render_column_stats(self, index_name: str, spec: Dict[str, Any]) -> List[TableColumnStats]:
        result: List[TableColumnStats] = []

        col_name = spec.pop('name')

        for stat_name, stat_val in spec.items():
            if isinstance(stat_val, dict) or isinstance(stat_val, list):
                continue
            elif stat_val == 'NaN':
                continue

            stat = TableColumnStats(table_name=index_name,
                                    col_name=col_name,
                                    stat_name=stat_name,
                                    stat_val=stat_val,
                                    start_epoch='0',
                                    end_epoch='0',
                                    db=self.database,
                                    cluster=self.cluster,
                                    schema=self.schema)

            result.append(stat)

        return result

    @property
    def _allowed_types(self) -> Set[str]:
        return set(['long', 'integer', 'short', 'byte', 'double',
                    'float', 'half_float', 'scaled_float', 'unsigned_long'])

    def _get_extract_iter(self) -> Iterator[Union[TableColumnStats, None]]:
        indexes: Dict = self._get_indexes()
        for index_name, index_metadata in indexes.items():
            properties = self._get_index_mapping_properties(index_metadata) or dict()

            fields = [name for name, spec in properties.items() if spec['type'] in self._allowed_types]

            specifications = self._get_index_stats(index_name, fields)

            for spec in specifications:
                stats = self._render_column_stats(index_name, spec)

                for stat in stats:
                    yield stat
