# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import unittest

from databuilder.models.query.base import QueryBase


class TestQueryBase(unittest.TestCase):
    def test_normalize_mixed_case(self) -> None:
        query = 'SELECT foo from BAR'
        expected = 'select foo from bar'
        self.assertEqual(QueryBase._normalize(query), expected)

    def test_normalize_mixed_case_string(self) -> None:
        query = "SELECT 'foo BaR'"
        expected = "select 'foo BaR'"
        self.assertEqual(QueryBase._normalize(query), expected)

    def test_normalize_lots_of_space(self) -> None:
        query = '''
        SELECT foo AS   bar
          FROM baz'''
        expected = 'select foo as bar from baz'
        self.assertEqual(QueryBase._normalize(query), expected)

    def test_trailing_semicolon(self) -> None:
        query = "select 'a;b;c';"
        expected = "select 'a;b;c'"
        self.assertEqual(QueryBase._normalize(query), expected)
