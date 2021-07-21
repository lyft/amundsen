# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import logging
import unittest

from mock import call, patch

from databuilder.rest_api.base_rest_api_query import RestApiQuerySeed
from databuilder.rest_api.mode_analytics.mode_paginated_rest_api_query import ModePaginatedRestApiQuery

logging.basicConfig(level=logging.INFO)


class TestModePaginatedRestApiQuery(unittest.TestCase):

    def test_pagination(self) -> None:
        seed_record = [{'foo1': 'bar1'},
                       {'foo2': 'bar2'}]
        seed_query = RestApiQuerySeed(seed_record=seed_record)

        with patch('databuilder.rest_api.rest_api_query.requests.get') as mock_get:
            json_path = 'foo[*].name'
            field_names = ['name_field']

            mock_get.return_value.json.side_effect = [  # need to duplicate for json() is called twice
                {'foo': [{'name': 'v1'}, {'name': 'v2'}]},
                {'foo': [{'name': 'v1'}, {'name': 'v2'}]},
                {'foo': [{'name': 'v3'}]},
                {'foo': [{'name': 'v3'}]},
                {'foo': [{'name': 'v4'}, {'name': 'v5'}]},
                {'foo': [{'name': 'v4'}, {'name': 'v5'}]},
                {},
                {}
            ]

            query = ModePaginatedRestApiQuery(query_to_join=seed_query, url='foobar', params={},
                                              json_path=json_path, field_names=field_names,
                                              skip_no_result=True, pagination_json_path='foo[*]',
                                              max_record_size=2)

            expected_list = [
                {'name_field': 'v1', 'foo1': 'bar1'},
                {'name_field': 'v2', 'foo1': 'bar1'},
                {'name_field': 'v3', 'foo1': 'bar1'},
                {'name_field': 'v4', 'foo2': 'bar2'},
                {'name_field': 'v5', 'foo2': 'bar2'}
            ]
            for actual in query.execute():
                self.assertDictEqual(actual, expected_list.pop(0))

            self.assertEqual(mock_get.call_count, 4)

            calls = [
                call('foobar?page=1'),
                call('foobar?page=2')
            ]
            mock_get.assert_has_calls(calls, any_order=True)

    def test_no_pagination(self) -> None:
        seed_record = [{'foo1': 'bar1'},
                       {'foo2': 'bar2'},
                       {'foo3': 'bar3'}]
        seed_query = RestApiQuerySeed(seed_record=seed_record)

        with patch('databuilder.rest_api.rest_api_query.requests.get') as mock_get:
            json_path = 'foo[*].name'
            field_names = ['name_field']

            mock_get.return_value.json.side_effect = [  # need to duplicate for json() is called twice
                {'foo': [{'name': 'v1'}, {'name': 'v2'}]},
                {'foo': [{'name': 'v1'}, {'name': 'v2'}]},
                {'foo': [{'name': 'v3'}]},
                {'foo': [{'name': 'v3'}]},
                {'foo': [{'name': 'v4'}, {'name': 'v5'}]},
                {'foo': [{'name': 'v4'}, {'name': 'v5'}]},
            ]

            query = ModePaginatedRestApiQuery(query_to_join=seed_query, url='foobar', params={},
                                              json_path=json_path, field_names=field_names,
                                              pagination_json_path='foo[*]',
                                              max_record_size=3)

            expected_list = [
                {'name_field': 'v1', 'foo1': 'bar1'},
                {'name_field': 'v2', 'foo1': 'bar1'},
                {'name_field': 'v3', 'foo2': 'bar2'},
                {'name_field': 'v4', 'foo3': 'bar3'},
                {'name_field': 'v5', 'foo3': 'bar3'}
            ]
            for actual in query.execute():
                self.assertDictEqual(actual, expected_list.pop(0))

            self.assertEqual(mock_get.call_count, 3)
            calls = [
                call('foobar?page=1')
            ]
            mock_get.assert_has_calls(calls, any_order=True)


if __name__ == '__main__':
    unittest.main()
