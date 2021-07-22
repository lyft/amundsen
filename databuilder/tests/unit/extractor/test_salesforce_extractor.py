# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import unittest
from collections import OrderedDict
from typing import Any, Dict

from mock import patch
from pyhocon import ConfigFactory

from databuilder import Scoped
from databuilder.extractor.salesforce_extractor import SalesForceExtractor
from databuilder.models.table_metadata import ColumnMetadata, TableMetadata

METADATA = {
    "Account": {
        "fields": [
            {"name": "Id", "inlineHelpText": "The Account Id", "type": "id"},
            {"name": "isDeleted", "inlineHelpText": "Deleted?", "type": "bool"},
        ]
    },
    "Profile": {
        "fields": [
            {"name": "Id", "inlineHelpText": "The Profile Id", "type": "id"},
            {
                "name": "Business",
                "inlineHelpText": "Important Bizness",
                "type": "string",
            },
        ]
    },
}


class MockSalesForce:
    def __init__(self) -> None:
        pass

    def describe(self) -> Dict:
        return {
            "encoding": "UTF-8",
            "maxBatchSize": 200,
            "sobjects": [
                OrderedDict(
                    [
                        ("activateable", False),
                        ("createable", False),
                        ("custom", False),
                        ("customSetting", False),
                        ("deletable", False),
                        ("deprecatedAndHidden", False),
                        ("feedEnabled", False),
                        ("hasSubtypes", False),
                        ("isSubtype", False),
                        ("keyPrefix", None),
                        ("label", object_name),
                        ("labelPlural", object_name),
                        ("layoutable", False),
                        ("mergeable", False),
                        ("mruEnabled", False),
                        ("name", object_name),
                        ("queryable", True),
                        ("replicateable", False),
                        ("retrieveable", True),
                        ("searchable", False),
                        ("triggerable", False),
                        ("undeletable", False),
                        ("updateable", False),
                        (
                            "urls",
                            OrderedDict(
                                [
                                    (
                                        "rowTemplate",
                                        f"/services/data/v42.0/sobjects/{object_name}/" + "{ID}",
                                    ),
                                    (
                                        "describe",
                                        f"/services/data/v42.0/sobjects/{object_name}/describe",
                                    ),
                                    (
                                        "sobject",
                                        f"/services/data/v42.0/sobjects/{object_name}",
                                    ),
                                ]
                            ),
                        ),
                    ]
                )
                for object_name in METADATA.keys()
            ],
        }

    def restful(self, path: str) -> Dict:
        object_name = path.split("/")[1]
        return METADATA[object_name]


class TestSalesForceExtractor(unittest.TestCase):
    def setUp(self) -> None:
        self.config = {
            f"extractor.salesforce_metadata.{SalesForceExtractor.USERNAME_KEY}": "user",
            f"extractor.salesforce_metadata.{SalesForceExtractor.PASSWORD_KEY}": "password",
            f"extractor.salesforce_metadata.{SalesForceExtractor.SECURITY_TOKEN_KEY}": "token",
            f"extractor.salesforce_metadata.{SalesForceExtractor.SCHEMA_KEY}": "default",
            f"extractor.salesforce_metadata.{SalesForceExtractor.CLUSTER_KEY}": "gold",
            f"extractor.salesforce_metadata.{SalesForceExtractor.DATABASE_KEY}": "salesforce",
        }

    @patch("databuilder.extractor.salesforce_extractor.Salesforce")
    def test_extraction_one_object(self, mock_salesforce: Any) -> None:
        mock_salesforce.return_value = MockSalesForce()
        config_dict: Dict = {
            f"extractor.salesforce_metadata.{SalesForceExtractor.OBJECT_NAMES_KEY}": [
                "Account"
            ],
            **self.config,
        }
        conf = ConfigFactory.from_dict(config_dict)

        mock_salesforce.return_value = MockSalesForce()
        extractor = SalesForceExtractor()
        extractor.init(Scoped.get_scoped_conf(conf=conf, scope=extractor.get_scope()))
        result = extractor.extract()
        self.assertIsInstance(result, TableMetadata)

        expected = TableMetadata(
            "salesforce",
            "gold",
            "default",
            "Account",
            None,
            [
                ColumnMetadata("Id", "The Account Id", "id", 0, []),
                ColumnMetadata("isDeleted", "Deleted?", "bool", 1, []),
            ],
            False,
            [],
        )

        self.assertEqual(expected.__repr__(), result.__repr__())

        self.assertIsNone(extractor.extract())

    @patch("databuilder.extractor.salesforce_extractor.Salesforce")
    def test_extraction_multiple_objects(self, mock_salesforce: Any) -> None:
        mock_salesforce.return_value = MockSalesForce()
        config_dict: Dict = {
            f"extractor.salesforce_metadata.{SalesForceExtractor.OBJECT_NAMES_KEY}": [
                "Account",
                "Profile",
            ],
            **self.config,
        }
        conf = ConfigFactory.from_dict(config_dict)

        mock_salesforce.return_value = MockSalesForce()
        extractor = SalesForceExtractor()
        extractor.init(Scoped.get_scoped_conf(conf=conf, scope=extractor.get_scope()))

        results = [extractor.extract(), extractor.extract()]
        for result in results:
            self.assertIsInstance(result, TableMetadata)

        expecteds = [
            TableMetadata(
                "salesforce",
                "gold",
                "default",
                "Account",
                None,
                [
                    ColumnMetadata("Id", "The Account Id", "id", 0, []),
                    ColumnMetadata("isDeleted", "Deleted?", "bool", 1, []),
                ],
                False,
                [],
            ),
            TableMetadata(
                "salesforce",
                "gold",
                "default",
                "Profile",
                None,
                [
                    # These columns are sorted alphabetically
                    ColumnMetadata("Business", "Important Bizness", "string", 0, []),
                    ColumnMetadata("Id", "The Profile Id", "id", 1, []),
                ],
                False,
                [],
            ),
        ]

        for result, expected in zip(results, expecteds):
            self.assertEqual(expected.__repr__(), result.__repr__())

        self.assertIsNone(extractor.extract())
