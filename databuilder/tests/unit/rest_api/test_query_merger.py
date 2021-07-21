# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import unittest

from mock import patch

from databuilder.rest_api.base_rest_api_query import RestApiQuerySeed
from databuilder.rest_api.query_merger import QueryMerger
from databuilder.rest_api.rest_api_query import RestApiQuery


class TestQueryMerger(unittest.TestCase):
    def setUp(self) -> None:
        query_to_join_seed_record = [
            {'foo1': 'bar1', 'dashboard_id': 'd1'},
            {'foo2': 'bar2', 'dashboard_id': 'd3'}
        ]
        self.query_to_join = RestApiQuerySeed(seed_record=query_to_join_seed_record)
        self.json_path = 'foo.name'
        self.field_names = ['name_field']
        self.url = 'foobar'

    def test_ensure_record_get_updated(self) -> None:
        query_to_merge_seed_record = [
            {'organization': 'amundsen', 'dashboard_id': 'd1'},
            {'organization': 'amundsen-databuilder', 'dashboard_id': 'd2'},
            {'organization': 'amundsen-dashboard', 'dashboard_id': 'd3'},
        ]
        query_to_merge = RestApiQuerySeed(seed_record=query_to_merge_seed_record)
        query_merger = QueryMerger(query_to_merge=query_to_merge, merge_key='dashboard_id')

        with patch('databuilder.rest_api.rest_api_query.requests.get') as mock_get:
            mock_get.return_value.json.side_effect = [
                {'foo': {'name': 'john'}},
                {'foo': {'name': 'doe'}},
            ]
            query = RestApiQuery(query_to_join=self.query_to_join, url=self.url, params={},
                                 json_path=self.json_path, field_names=self.field_names,
                                 query_merger=query_merger)
            results = list(query.execute())
            self.assertEqual(len(results), 2)
            self.assertDictEqual(
                {'dashboard_id': 'd1', 'foo1': 'bar1', 'name_field': 'john', 'organization': 'amundsen'},
                results[0],
            )
            self.assertDictEqual(
                {'dashboard_id': 'd3', 'foo2': 'bar2', 'name_field': 'doe', 'organization': 'amundsen-dashboard'},
                results[1],
            )

    def test_exception_rasied_with_duplicate_merge_key(self) -> None:
        """
         Two records in query_to_merge results have {'dashboard_id': 'd2'},
         exception should be raised
        """
        query_to_merge_seed_record = [
            {'organization': 'amundsen', 'dashboard_id': 'd1'},
            {'organization': 'amundsen-databuilder', 'dashboard_id': 'd2'},
            {'organization': 'amundsen-dashboard', 'dashboard_id': 'd2'},
        ]
        query_to_merge = RestApiQuerySeed(seed_record=query_to_merge_seed_record)
        query_merger = QueryMerger(query_to_merge=query_to_merge, merge_key='dashboard_id')

        with patch('databuilder.rest_api.rest_api_query.requests.get') as mock_get:
            mock_get.return_value.json.side_effect = [
                {'foo': {'name': 'john'}},
                {'foo': {'name': 'doe'}},
            ]
            query = RestApiQuery(query_to_join=self.query_to_join, url=self.url, params={},
                                 json_path=self.json_path, field_names=self.field_names,
                                 query_merger=query_merger)
            self.assertRaises(Exception, query.execute())

    def test_exception_raised_with_missing_merge_key(self) -> None:
        """
         No record in query_to_merge results contains {'dashboard_id': 'd3'},
         exception should be raised
        """
        query_to_merge_seed_record = [
            {'organization': 'amundsen', 'dashboard_id': 'd1'},
            {'organization': 'amundsen-databuilder', 'dashboard_id': 'd2'},
        ]
        query_to_merge = RestApiQuerySeed(seed_record=query_to_merge_seed_record)
        query_merger = QueryMerger(query_to_merge=query_to_merge, merge_key='dashboard_id')

        with patch('databuilder.rest_api.rest_api_query.requests.get') as mock_get:
            mock_get.return_value.json.side_effect = [
                {'foo': {'name': 'john'}},
                {'foo': {'name': 'doe'}},
            ]
            query = RestApiQuery(query_to_join=self.query_to_join, url=self.url, params={},
                                 json_path=self.json_path, field_names=self.field_names,
                                 query_merger=query_merger)
            self.assertRaises(Exception, query.execute())


if __name__ == '__main__':
    unittest.main()
