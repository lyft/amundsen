# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import unittest
from typing import Dict

from amundsen_application import create_app
from amundsen_application.api.utils.metadata_utils import _convert_prog_descriptions, _sort_prog_descriptions, \
    _parse_editable_rule, is_table_editable, TableUri
from amundsen_application.config import MatchRuleObject

local_app = create_app('amundsen_application.config.TestConfig', 'tests/templates')


class ProgrammaticDescriptionsTest(unittest.TestCase):
    def setUp(self) -> None:
        pass

    def test_convert_prog_descriptions(self) -> None:
        with local_app.app_context():
            # mock config
            test_config = {
                'RIGHT': {
                    'test3': {},
                    'test2': {'display_order': 0},
                },
                'LEFT': {
                    'test1': {'display_order': 1},
                    'test0': {'display_order': 0},
                },
                'test4': {'display_order': 0},
            }
            # test data
            test_desc = [
                {'source': 'test0', 'text': 'test'},
                {'source': 'test1', 'text': 'test'},
                {'source': 'test2', 'text': 'test'},
                {'source': 'test3', 'text': 'test'},
                {'source': 'test5', 'text': 'test'},
                {'source': 'test4', 'text': 'test'},
            ]
            # expected order based on mock
            expected_programmatic_desc = {
                'left': [
                    {'source': 'test0', 'text': 'test'},
                    {'source': 'test1', 'text': 'test'},
                ],
                'right': [
                    {'source': 'test2', 'text': 'test'},
                    {'source': 'test3', 'text': 'test'},
                ],
                'other': [
                    {'source': 'test4', 'text': 'test'},
                    {'source': 'test5', 'text': 'test'},
                ]
            }
            local_app.config['PROGRAMMATIC_DISPLAY'] = test_config

            result = _convert_prog_descriptions(test_desc)
            self.assertEqual(result.get('left'), expected_programmatic_desc.get('left'))
            self.assertEqual(result.get('right'), expected_programmatic_desc.get('right'))
            self.assertEqual(result.get('other'), expected_programmatic_desc.get('other'))

    def test_sort_prog_descriptions_returns_value_from_config(self) -> None:
        """
        Verify the method will return the display order from the programmtic description
        configuration if it exists for the given source
        :return:
        """
        with local_app.app_context():
            mock_order = 1
            mock_config = {
                "c_1": {
                    "display_order": mock_order
                }
            }
            in_config_value = {'source': 'c_1', 'text': 'I am a test'}
            self.assertEqual(_sort_prog_descriptions(mock_config, in_config_value), mock_order)

    def test_convert_prog_descriptions_without_config(self) -> None:
        with local_app.app_context():
            # mock config
            test_config = None
            # test data
            test_desc = [
                {'source': 'test4', 'text': 'test'},
                {'source': 'test5', 'text': 'test'},
            ]
            # expected order based on mock
            expected_programmatic_desc = {
                'other': [
                    {'source': 'test4', 'text': 'test'},
                    {'source': 'test5', 'text': 'test'},
                ]
            }
            local_app.config['PROGRAMMATIC_DISPLAY'] = test_config

            result = _convert_prog_descriptions(test_desc)
            self.assertEqual(len(result['left']), 0)
            self.assertEqual(len(result['right']), 0)
            self.assertEqual(result.get('other'), expected_programmatic_desc.get('other'))

    def test_sort_prog_descriptions_returns_default_value(self) -> None:
        """
        Verify the method will return the expected default value if programmtic decsription
        source is not included in teh configuration
        :return:
        """
        with local_app.app_context():
            mock_config = {
                "c_1": {
                    "display_order": 0
                }
            }
            not_in_config_value = {'source': 'test', 'text': 'I am a test'}
            self.assertEqual(_sort_prog_descriptions(mock_config, not_in_config_value), len(mock_config))


class UneditableTableDescriptionTest(unittest.TestCase):
    def setUp(self) -> None:
        pass

    def test_table_desc_match_rule_schema_only(self) -> None:
        # Mock match rule, table name and schema
        test_match_rule = MatchRuleObject(schema_regex=r"^(schema1)")

        # assert result for given schema and match rule
        self.assertEqual(_parse_editable_rule(test_match_rule, 'schema1', 'test_table'), False)
        self.assertEqual(_parse_editable_rule(test_match_rule, 'schema2', 'test_table'), True)

    def test_table_desc_match_rule_table_only(self) -> None:
        # Mock match rule, table name and schema
        test_match_rule = MatchRuleObject(table_name_regex=r"^noedit_([a-zA-Z_0-9]+)")

        # assert result for given table name and match rule
        self.assertEqual(_parse_editable_rule(test_match_rule, 'schema', 'noedit_test_table'), False)
        self.assertEqual(_parse_editable_rule(test_match_rule, 'schema', 'editable_test_table'), True)

    def test_table_desc_match_rule_schema_and_table(self) -> None:
        # Mock match rule, table name and schema
        test_match_rule = MatchRuleObject(schema_regex=r"^(schema1|schema2)",
                                          table_name_regex=r"^other_([a-zA-Z_0-9]+)")
        # assert result for given schema, table name and match rule
        self.assertEqual(_parse_editable_rule(test_match_rule, 'schema1', 'other_test_table'), False)
        self.assertEqual(_parse_editable_rule(test_match_rule, 'schema1', 'test_table'), True)
        self.assertEqual(_parse_editable_rule(test_match_rule, 'schema3', 'other_test_table'), True)
        self.assertEqual(_parse_editable_rule(test_match_rule, 'schema3', 'test_table'), True)


class TableEditabilityWrapper(unittest.TestCase):
    def setUp(self) -> None:
        pass

    def test_no_schemas_editable(self) -> None:
        mockConfig: Dict = {
            'ALL_UNEDITABLE_SCHEMAS': True,
            'UNEDITABLE_SCHEMAS': [],
            'UNEDITABLE_TABLE_DESCRIPTION_MATCH_RULES': [],
        }

        self.assertFalse(is_table_editable('anyschema', 'anytable', mockConfig))
        self.assertFalse(is_table_editable('anotherschema', 'anothertable', mockConfig))
        self.assertFalse(is_table_editable('athirdschema', 'athirdtable', mockConfig))

    def test_empty_allowed(self) -> None:
        mockConfig: Dict = {
            'ALL_UNEDITABLE_SCHEMAS': False,
            'UNEDITABLE_SCHEMAS': [],
            'UNEDITABLE_TABLE_DESCRIPTION_MATCH_RULES': [],
        }

        self.assertTrue(is_table_editable('anyschema', 'anytable', mockConfig))

    def test_schema(self) -> None:
        mockConfig = {
            'ALL_UNEDITABLE_SCHEMAS': False,
            'UNEDITABLE_SCHEMAS': ['uneditable_schema'],
            'UNEDITABLE_TABLE_DESCRIPTION_MATCH_RULES': [],
        }

        self.assertTrue(is_table_editable('different_schema', 'anytable', mockConfig))
        self.assertFalse(is_table_editable('uneditable_schema', 'anytable', mockConfig))

    def test_schema_match_rule(self) -> None:
        mockConfig = {
            'ALL_UNEDITABLE_SCHEMAS': False,
            'UNEDITABLE_SCHEMAS': [''],
            'UNEDITABLE_TABLE_DESCRIPTION_MATCH_RULES': [
                MatchRuleObject(schema_regex=r"^(uneditable).*"),
            ],
        }

        self.assertTrue(is_table_editable('not_uneditable_schema', 'anytable', mockConfig))
        self.assertFalse(is_table_editable('uneditable_schema', 'anytable', mockConfig))

    def test_schema_table_match_rule(self) -> None:
        mockConfig = {
            'ALL_UNEDITABLE_SCHEMAS': False,
            'UNEDITABLE_SCHEMAS': [''],
            'UNEDITABLE_TABLE_DESCRIPTION_MATCH_RULES': [
                MatchRuleObject(schema_regex=r"^first.*", table_name_regex=r".*bad.*")
            ],
        }

        self.assertFalse(is_table_editable('first', 'bad', mockConfig))
        self.assertFalse(is_table_editable('first', 'also_bad', mockConfig))
        self.assertTrue(is_table_editable('first', 'good', mockConfig))
        self.assertTrue(is_table_editable('not_first', 'bad', mockConfig))
        self.assertTrue(is_table_editable('second', 'bad', mockConfig))


class TableUriObject(unittest.TestCase):
    def test_simple_constructor(self) -> None:
        uri = TableUri("db", "clstr", "schm", "tbl")
        self.assertEqual('db://clstr.schm/tbl', str(uri))

    def test_from_uri_factory(self) -> None:
        params = [
            ('db', 'cluster', 'schema', 'table'),
            ('db_underscore', 'cluster.with.dots', 'schema', 'table/with/slashes'),
            ('db.dot', 'cluster.dot', 'schema', 'table.dot'),
            ('hive_table', 'demo', 'test_schema', 'test_table')
        ]

        for db, cluster, schema, table in params:
            with self.subTest():
                _uri = f'{db}://{cluster}.{schema}/{table}'
                uri = TableUri.from_uri(_uri)
                self.assertEqual(db, uri.database)
                self.assertEqual(cluster, uri.cluster)
                self.assertEqual(schema, uri.schema)
                self.assertEqual(table, uri.table)
