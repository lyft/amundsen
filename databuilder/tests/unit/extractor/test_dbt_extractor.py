# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import json
import unittest
from typing import (
    Any, Optional, Union, no_type_check,
)

import pyhocon
import pytest
from pyhocon import ConfigFactory

from databuilder import Scoped
from databuilder.extractor.dbt_extractor import DbtExtractor, InvalidDbtInputs
from databuilder.models.badge import Badge, BadgeMetadata
from databuilder.models.table_lineage import TableLineage
from databuilder.models.table_metadata import TableMetadata
from databuilder.models.table_source import TableSource


def _extract_until_not_these(extractor: DbtExtractor,
                             classes: Any) -> Optional[Union[BadgeMetadata, TableLineage, TableMetadata, TableSource]]:
    # Move to the next type of extracted class:
    r = extractor.extract()
    while isinstance(r, tuple(classes)):
        r = extractor.extract()
    return r


class TestCsvExtractor(unittest.TestCase):

    database_name = 'snowflake'
    catalog_file_loc = 'example/sample_data/dbt/catalog.json'
    manifest_data = 'example/sample_data/dbt/manifest.json'
    source_url = 'test_url'

    @no_type_check
    def test_extraction_with_model_class(self) -> None:
        """
        Test Extraction using model class
        """
        config_dict = {
            f'extractor.dbt.{DbtExtractor.DATABASE_NAME}': self.database_name,
            f'extractor.dbt.{DbtExtractor.CATALOG_JSON}': self.catalog_file_loc,
            f'extractor.dbt.{DbtExtractor.MANIFEST_JSON}': self.manifest_data,
            f'extractor.dbt.{DbtExtractor.SOURCE_URL}': self.source_url
        }
        self.conf = ConfigFactory.from_dict(config_dict)
        extractor = DbtExtractor()
        extractor.init(Scoped.get_scoped_conf(conf=self.conf,
                                              scope=extractor.get_scope()))

        # One block of tests for each type of model created
        extracted_classes = []

        result = extractor.extract()
        self.assertTrue(isinstance(result, TableMetadata))
        self.assertEqual(result.name, 'fact_third_party_performance')
        self.assertEqual(result.description.text, 'The performance for third party vendors loss rate by day.')
        self.assertEqual(result.database, self.database_name)
        self.assertEqual(result.cluster, 'dbt_demo')
        self.assertEqual(result.schema, 'public')
        self.assertEqual(result.tags, [])
        self.assertEqual(result.is_view, True)
        extracted_classes.append(TableMetadata)

        result2 = _extract_until_not_these(extractor, extracted_classes)
        self.assertTrue(isinstance(result2, TableSource))
        self.assertEqual(result2.db, self.database_name)
        self.assertEqual(result2.cluster, 'dbt_demo')
        self.assertEqual(result2.schema, 'public')
        self.assertEqual(result2.table, 'fact_third_party_performance')
        self.assertEqual(result2.source, 'test_url/models/call_center/fact_third_party_performance.sql')
        extracted_classes.append(TableSource)

        result3 = _extract_until_not_these(extractor, extracted_classes)
        self.assertTrue(isinstance(result3, BadgeMetadata))
        self.assertEqual(result3.badges, [Badge('finance', 'table'), Badge('certified', 'table')])
        extracted_classes.append(BadgeMetadata)

        result4 = _extract_until_not_these(extractor, extracted_classes)
        self.assertTrue(isinstance(result4, TableLineage))
        self.assertEqual(result4.table_key, 'snowflake://dbt_demo.public/fact_catalog_returns')
        self.assertEqual(result4.downstream_deps, ['snowflake://dbt_demo.public/fact_third_party_performance'])
        extracted_classes.append(TableLineage)

        # Should not be any other unique models created
        result5 = _extract_until_not_these(extractor, extracted_classes)
        self.assertEqual(result5, None)

    @no_type_check
    def test_dbt_file_inputs_as_json_dumps(self) -> None:
        """
        Tests to ensure that the same content can be extracted when the manifest.json
        and catalog.json are provided as a file location or as a json.dumps() object
        """
        config_dict_1 = {
            f'extractor.dbt.{DbtExtractor.DATABASE_NAME}': self.database_name,
            f'extractor.dbt.{DbtExtractor.CATALOG_JSON}': self.catalog_file_loc,
            f'extractor.dbt.{DbtExtractor.MANIFEST_JSON}': self.manifest_data,
            f'extractor.dbt.{DbtExtractor.SOURCE_URL}': self.source_url
        }
        conf_1 = ConfigFactory.from_dict(config_dict_1)
        extractor_1 = DbtExtractor()
        extractor_1.init(Scoped.get_scoped_conf(conf=conf_1, scope=extractor_1.get_scope()))

        with open(self.catalog_file_loc, 'r') as f:
            catalog_as_json = json.dumps(json.load(f))

        with open(self.manifest_data, 'r') as f:
            manifest_as_json = json.dumps(json.load(f))

        config_dict_2 = {
            f'extractor.dbt.{DbtExtractor.DATABASE_NAME}': self.database_name,
            f'extractor.dbt.{DbtExtractor.CATALOG_JSON}': catalog_as_json,
            f'extractor.dbt.{DbtExtractor.MANIFEST_JSON}': manifest_as_json
        }
        conf_2 = ConfigFactory.from_dict(config_dict_2)
        extractor_2 = DbtExtractor()
        extractor_2.init(Scoped.get_scoped_conf(conf=conf_2, scope=extractor_2.get_scope()))

        result_1 = extractor_1.extract()
        result_2 = extractor_2.extract()
        self.assertEqual(result_1.name, result_2.name)
        self.assertEqual(result_1.description.text, result_2.description.text)
        self.assertEqual(result_1.database, result_2.database)
        self.assertEqual(result_1.cluster, result_2.cluster)
        self.assertEqual(result_1.schema, result_2.schema)
        self.assertEqual(result_1.tags, result_2.tags)
        self.assertEqual(result_1.is_view, result_2.is_view)

    @no_type_check
    def test_keys_retain_original_format(self) -> None:
        """
        Test that the database name, cluster name, schema and table name do not
        have lowercase auto applied.
        """
        config_dict = {
            f'extractor.dbt.{DbtExtractor.DATABASE_NAME}': self.database_name.upper(),  # Force upper for test
            f'extractor.dbt.{DbtExtractor.CATALOG_JSON}': self.catalog_file_loc,
            f'extractor.dbt.{DbtExtractor.MANIFEST_JSON}': self.manifest_data,
            f'extractor.dbt.{DbtExtractor.FORCE_TABLE_KEY_LOWER}': False
        }
        conf = ConfigFactory.from_dict(config_dict)
        extractor = DbtExtractor()
        extractor.init(Scoped.get_scoped_conf(conf=conf, scope=extractor.get_scope()))

        result = extractor.extract()

        self.assertEqual(result.name, 'fact_third_party_performance')
        self.assertEqual(result.database, 'SNOWFLAKE')
        self.assertEqual(result.cluster, 'DBT_DEMO')
        self.assertEqual(result.schema, 'PUBLIC')

    def test_do_not_extract_tables(self) -> None:
        """
        Test that tables are not extracted.
        """
        config_dict = {
            f'extractor.dbt.{DbtExtractor.DATABASE_NAME}': self.database_name.upper(),
            f'extractor.dbt.{DbtExtractor.CATALOG_JSON}': self.catalog_file_loc,
            f'extractor.dbt.{DbtExtractor.MANIFEST_JSON}': self.manifest_data,
            f'extractor.dbt.{DbtExtractor.EXTRACT_TABLES}': False
        }
        conf = ConfigFactory.from_dict(config_dict)
        extractor = DbtExtractor()
        extractor.init(Scoped.get_scoped_conf(conf=conf, scope=extractor.get_scope()))

        has_next = True
        while has_next:
            extraction = extractor.extract()
            self.assertFalse(isinstance(extraction, TableMetadata))
            if extraction is None:
                break

    def test_do_not_extract_descriptions(self) -> None:
        """
        Test that tables are not extracted.
        """
        config_dict = {
            f'extractor.dbt.{DbtExtractor.DATABASE_NAME}': self.database_name.upper(),
            f'extractor.dbt.{DbtExtractor.CATALOG_JSON}': self.catalog_file_loc,
            f'extractor.dbt.{DbtExtractor.MANIFEST_JSON}': self.manifest_data,
            f'extractor.dbt.{DbtExtractor.EXTRACT_DESCRIPTIONS}': False
        }
        conf = ConfigFactory.from_dict(config_dict)
        extractor = DbtExtractor()
        extractor.init(Scoped.get_scoped_conf(conf=conf, scope=extractor.get_scope()))

        has_next = True
        while has_next:
            extraction = extractor.extract()
            if isinstance(extraction, TableMetadata):
                # No table descriptions
                self.assertEqual(extraction.description, None)

                # No column descriptions
                for col in extraction.columns:
                    self.assertEqual(col.description, None)

            if extraction is None:
                break

    def test_do_not_extract_dbt_tags(self) -> None:
        """
        Test that tags are not extracted as Badges
        """
        config_dict = {
            f'extractor.dbt.{DbtExtractor.DATABASE_NAME}': self.database_name.upper(),
            f'extractor.dbt.{DbtExtractor.CATALOG_JSON}': self.catalog_file_loc,
            f'extractor.dbt.{DbtExtractor.MANIFEST_JSON}': self.manifest_data,
            f'extractor.dbt.{DbtExtractor.EXTRACT_TAGS}': False
        }
        conf = ConfigFactory.from_dict(config_dict)
        extractor = DbtExtractor()
        extractor.init(Scoped.get_scoped_conf(conf=conf, scope=extractor.get_scope()))

        has_next = True
        while has_next:
            extraction = extractor.extract()
            self.assertFalse(isinstance(extraction, BadgeMetadata))
            if extraction is None:
                break

    def test_import_tags_as_tags(self) -> None:
        """
        Test that dbt tags can be configured to be imported as Amundsen tags.
        """
        config_dict = {
            f'extractor.dbt.{DbtExtractor.DATABASE_NAME}': self.database_name.upper(),
            f'extractor.dbt.{DbtExtractor.CATALOG_JSON}': self.catalog_file_loc,
            f'extractor.dbt.{DbtExtractor.MANIFEST_JSON}': self.manifest_data,
            f'extractor.dbt.{DbtExtractor.IMPORT_TAGS_AS}': 'tag'
        }
        conf = ConfigFactory.from_dict(config_dict)
        extractor = DbtExtractor()
        extractor.init(Scoped.get_scoped_conf(conf=conf, scope=extractor.get_scope()))

        # The 7th table has tags
        extraction = [extractor.extract() for i in range(6)][-1]
        self.assertEqual(extraction.tags, ['finance', 'certified'])  # type: ignore

    def test_do_not_extract_dbt_lineage(self) -> None:
        """
        Test that table level lineage is not extracted from dbt
        """
        config_dict = {
            f'extractor.dbt.{DbtExtractor.DATABASE_NAME}': self.database_name.upper(),
            f'extractor.dbt.{DbtExtractor.CATALOG_JSON}': self.catalog_file_loc,
            f'extractor.dbt.{DbtExtractor.MANIFEST_JSON}': self.manifest_data,
            f'extractor.dbt.{DbtExtractor.EXTRACT_LINEAGE}': False
        }
        conf = ConfigFactory.from_dict(config_dict)
        extractor = DbtExtractor()
        extractor.init(Scoped.get_scoped_conf(conf=conf, scope=extractor.get_scope()))

        has_next = True
        while has_next:
            extraction = extractor.extract()
            self.assertFalse(isinstance(extraction, TableLineage))
            if extraction is None:
                break

    def test_alias_for_table_name(self) -> None:
        """
        Test that table level lineage is not extracted from dbt
        """
        config_dict = {
            f'extractor.dbt.{DbtExtractor.DATABASE_NAME}': self.database_name.upper(),
            f'extractor.dbt.{DbtExtractor.CATALOG_JSON}': self.catalog_file_loc,
            f'extractor.dbt.{DbtExtractor.MANIFEST_JSON}': self.manifest_data,
            f'extractor.dbt.{DbtExtractor.MODEL_NAME_KEY}': 'alias'
        }
        conf = ConfigFactory.from_dict(config_dict)
        extractor = DbtExtractor()
        extractor.init(Scoped.get_scoped_conf(conf=conf,
                                              scope=extractor.get_scope()))

        result = extractor.extract()
        known_alias = 'cost_summary'  # One table aliased as "cost_summary"
        known_alias_cnt = 0
        while result:
            if isinstance(result, TableMetadata):
                self.assertNotEqual(result.name, 'fact_daily_expenses')
                if result.name == known_alias:
                    known_alias_cnt += 1
            result = extractor.extract()
        self.assertEqual(known_alias_cnt, 1)

    def test_filter_schema_name(self) -> None:
        """
        Test that table level lineage is not extracted from dbt
        """
        config_dict = {
            f'extractor.dbt.{DbtExtractor.DATABASE_NAME}': self.database_name.upper(),
            f'extractor.dbt.{DbtExtractor.CATALOG_JSON}': self.catalog_file_loc,
            f'extractor.dbt.{DbtExtractor.MANIFEST_JSON}': self.manifest_data,
            f'extractor.dbt.{DbtExtractor.EXTRACT_LINEAGE}': False,
            f'extractor.dbt.{DbtExtractor.SCHEMA_FILTER}': 'other_schema_value'
        }
        conf = ConfigFactory.from_dict(config_dict)
        extractor = DbtExtractor()
        extractor.init(Scoped.get_scoped_conf(conf=conf,
                                              scope=extractor.get_scope()))

        # Tests currently have 1 schema defined
        result = extractor.extract()
        self.assertEqual(result, None)

    def test_invalid_dbt_inputs(self) -> None:
        """
        Test that table level lineage is not extracted from dbt
        """
        missing_inputs = [
            {
                # f'extractor.dbt.{DbtExtractor.DATABASE_NAME}': self.database_name.upper(),
                f'extractor.dbt.{DbtExtractor.CATALOG_JSON}': self.catalog_file_loc,
                f'extractor.dbt.{DbtExtractor.MANIFEST_JSON}': self.manifest_data
            },
            {
                f'extractor.dbt.{DbtExtractor.DATABASE_NAME}': self.database_name.upper(),
                # f'extractor.dbt.{DbtExtractor.CATALOG_JSON}': self.catalog_file_loc,
                f'extractor.dbt.{DbtExtractor.MANIFEST_JSON}': self.manifest_data
            },
            {
                f'extractor.dbt.{DbtExtractor.DATABASE_NAME}': self.database_name.upper(),
                f'extractor.dbt.{DbtExtractor.CATALOG_JSON}': self.catalog_file_loc,
                # f'extractor.dbt.{DbtExtractor.MANIFEST_JSON}': self.manifest_data
            }
        ]
        for missing_input_config in missing_inputs:
            conf = ConfigFactory.from_dict(missing_input_config)
            extractor = DbtExtractor()
            with pytest.raises(pyhocon.exceptions.ConfigMissingException):
                extractor.init(Scoped.get_scoped_conf(conf=conf, scope=extractor.get_scope()))

        # Invalid manifest.json and invalid catalog.json
        invalid_file_jsons = [
            {
                f'extractor.dbt.{DbtExtractor.DATABASE_NAME}': self.database_name.upper(),
                f'extractor.dbt.{DbtExtractor.CATALOG_JSON}': 'not a real file location or json',
                f'extractor.dbt.{DbtExtractor.MANIFEST_JSON}': self.manifest_data
            },
            {
                f'extractor.dbt.{DbtExtractor.DATABASE_NAME}': self.database_name.upper(),
                f'extractor.dbt.{DbtExtractor.CATALOG_JSON}': self.catalog_file_loc,
                f'extractor.dbt.{DbtExtractor.MANIFEST_JSON}': 'not a real file location or json'
            }
        ]
        for invalid_conf in invalid_file_jsons:
            conf = ConfigFactory.from_dict(invalid_conf)
            extractor = DbtExtractor()
            with pytest.raises(InvalidDbtInputs):
                extractor.init(Scoped.get_scoped_conf(conf=conf, scope=extractor.get_scope()))
