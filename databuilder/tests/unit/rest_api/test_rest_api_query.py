# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import unittest

from mock import patch

from databuilder.rest_api.base_rest_api_query import EmptyRestApiQuerySeed, RestApiQuerySeed
from databuilder.rest_api.rest_api_query import RestApiQuery


class TestRestApiQuery(unittest.TestCase):

    def test_rest_api_query_seed(self) -> None:
        rest_api_query = RestApiQuerySeed(seed_record=[
            {'foo': 'bar'},
            {'john': 'doe'}
        ])

        result = [v for v in rest_api_query.execute()]
        expected = [
            {'foo': 'bar'},
            {'john': 'doe'}
        ]

        self.assertListEqual(expected, result)

    def test_empty_rest_api_query_seed(self) -> None:
        rest_api_query = EmptyRestApiQuerySeed()

        result = [v for v in rest_api_query.execute()]
        assert len(result) == 1

    def test_rest_api_query(self) -> None:

        seed_record = [{'foo1': 'bar1'},
                       {'foo2': 'bar2'}]
        seed_query = RestApiQuerySeed(seed_record=seed_record)

        with patch('databuilder.rest_api.rest_api_query.requests.get') as mock_get:
            json_path = 'foo.name'
            field_names = ['name_field']

            mock_get.return_value.json.side_effect = [
                {'foo': {'name': 'john'}},
                {'foo': {'name': 'doe'}},
            ]
            query = RestApiQuery(query_to_join=seed_query, url='foobar', params={},
                                 json_path=json_path, field_names=field_names)

            expected = [
                {'name_field': 'john', 'foo1': 'bar1'},
                {'name_field': 'doe', 'foo2': 'bar2'}
            ]

            for actual in query.execute():
                self.assertDictEqual(expected.pop(0), actual)

    def test_rest_api_query_multiple_fields(self) -> None:

        seed_record = [{'foo1': 'bar1'},
                       {'foo2': 'bar2'}]
        seed_query = RestApiQuerySeed(seed_record=seed_record)

        with patch('databuilder.rest_api.rest_api_query.requests.get') as mock_get:
            json_path = 'foo.[name,hobby]'
            field_names = ['name_field', 'hobby']

            mock_get.return_value.json.side_effect = [
                {'foo': {'name': 'john', 'hobby': 'skiing'}},
                {'foo': {'name': 'doe', 'hobby': 'snowboarding'}},
            ]
            query = RestApiQuery(query_to_join=seed_query, url='foobar', params={},
                                 json_path=json_path, field_names=field_names)

            expected = [
                {'name_field': 'john', 'hobby': 'skiing', 'foo1': 'bar1'},
                {'name_field': 'doe', 'hobby': 'snowboarding', 'foo2': 'bar2'}
            ]

            for actual in query.execute():
                self.assertDictEqual(expected.pop(0), actual)

    def test_compute_subresult_single_field(self) -> None:
        sub_records = RestApiQuery._compute_sub_records(result_list=['1', '2', '3'], field_names=['foo'])

        expected_records = [
            ['1'], ['2'], ['3']
        ]

        assert expected_records == sub_records

        sub_records = RestApiQuery._compute_sub_records(result_list=['1', '2', '3'], field_names=['foo'],
                                                        json_path_contains_or=True)

        assert expected_records == sub_records

    def test_compute_subresult_multiple_fields_json_path_and_expression(self) -> None:
        sub_records = RestApiQuery._compute_sub_records(
            result_list=['1', 'a', '2', 'b', '3', 'c'], field_names=['foo', 'bar'])

        expected_records = [
            ['1', 'a'], ['2', 'b'], ['3', 'c']
        ]

        assert expected_records == sub_records

        sub_records = RestApiQuery._compute_sub_records(
            result_list=['1', 'a', 'x', '2', 'b', 'y', '3', 'c', 'z'], field_names=['foo', 'bar', 'baz'])

        expected_records = [
            ['1', 'a', 'x'], ['2', 'b', 'y'], ['3', 'c', 'z']
        ]

        assert expected_records == sub_records

    def test_compute_subresult_multiple_fields_json_path_or_expression(self) -> None:
        sub_records = RestApiQuery._compute_sub_records(
            result_list=['1', '2', '3', 'a', 'b', 'c'],
            field_names=['foo', 'bar'],
            json_path_contains_or=True
        )

        expected_records = [
            ['1', 'a'], ['2', 'b'], ['3', 'c']
        ]

        self.assertEqual(expected_records, sub_records)

        sub_records = RestApiQuery._compute_sub_records(
            result_list=['1', '2', '3', 'a', 'b', 'c', 'x', 'y', 'z'],
            field_names=['foo', 'bar', 'baz'],
            json_path_contains_or=True)

        expected_records = [
            ['1', 'a', 'x'], ['2', 'b', 'y'], ['3', 'c', 'z']
        ]

        self.assertEqual(expected_records, sub_records)


if __name__ == '__main__':
    unittest.main()
