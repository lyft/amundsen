# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import unittest

from amundsen_application.api.utils.search_utils import generate_query_json, has_filters, transform_filters


class SearchUtilsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.test_filters = {
            'invalid_option': 'invalid',
            'column': 'column_name',
            'database': {
                'db1': True,
                'db2': False,
                'db3': True,
            },
            'schema': 'schema_name',
            'table': 'table_name',
            'tag': 'tag_name',
        }
        self.expected_transformed_filters = {
            'column': ['column_name'],
            'database': ['db1', 'db3'],
            'schema': ['schema_name'],
            'table': ['table_name'],
            'tag': ['tag_name'],
        }
        self.test_page_index = 1
        self.test_term = 'hello'

    def test_transform_filters(self) -> None:
        """
        Verify that the given filters are correctly transformed
        :return:
        """
        self.assertEqual(transform_filters(filters=self.test_filters, resource='table'),
                         self.expected_transformed_filters)

    def test_generate_query_json(self) -> None:
        """
        Verify that the returned diction correctly transforms the parameters
        :return:
        """
        query_json = generate_query_json(filters=self.expected_transformed_filters,
                                         page_index=self.test_page_index,
                                         search_term=self.test_term)
        self.assertEqual(query_json.get('page_index'), int(self.test_page_index))
        self.assertEqual(query_json.get('search_request'), {
            'type': 'AND',
            'filters': self.expected_transformed_filters
        })
        self.assertEqual(query_json.get('query_term'), self.test_term)

    def test_has_filters_return_true(self) -> None:
        """
        Returns true if called with a dictionary that has values for a valid filter category
        :return:
        """
        self.assertTrue(has_filters(filters=self.expected_transformed_filters, resource='table'))

    def test_has_filters_return_false(self) -> None:
        """
        Returns false if called with a dictionary that has no values for a valid filter category
        :return:
        """
        self.assertFalse(has_filters(filters={'fake_category': ['db1']}, resource='table'))
        self.assertFalse(has_filters(filters={'tag': []}, resource='table'))
        self.assertFalse(has_filters())
