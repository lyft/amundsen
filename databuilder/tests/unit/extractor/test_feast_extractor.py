# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import json
import re
import unittest

from feast.entity import Entity
from feast.feature_table import FeatureTable
from mock import MagicMock, call
from pyhocon import ConfigFactory

from databuilder import Scoped
from databuilder.extractor.feast_extractor import FeastExtractor
from databuilder.models.table_metadata import (
    ColumnMetadata, DescriptionMetadata, TableMetadata,
)


class TestFeastExtractor(unittest.TestCase):
    def test_no_feature_tables_registered(self) -> None:
        self._init_extractor()
        self.extractor._client.list_projects.return_value = ["default"]

        self.assertIsNone(self.extractor.extract())

    def test_every_project_is_scanned(self) -> None:
        self._init_extractor()
        self.extractor._client.list_projects.return_value = ["default", "dev", "prod"]
        list_feature_tables_mock = self.extractor._client.list_feature_tables
        list_feature_tables_mock.return_value = []

        self.assertIsNone(self.extractor.extract())
        list_feature_tables_mock.assert_has_calls(
            [
                call(project="default"),
                call(project="dev"),
                call(project="prod"),
            ]
        )

    def test_feature_table_extraction(self) -> None:
        self._init_extractor(programmatic_description_enabled=False)
        self.extractor._client.list_projects.return_value = ["default"]
        self._mock_feature_table()

        table = self.extractor.extract()
        self.extractor._client.get_entity.assert_called_with(
            "driver_id", project="default"
        )
        expected = TableMetadata(
            database="feast",
            cluster="unittest-feast-instance",
            schema="default",
            name="driver_trips",
            description=None,
            columns=[
                ColumnMetadata(
                    "driver_id", "Internal identifier of the driver", "INT64", 0
                ),
                ColumnMetadata("trips_today", None, "INT32", 1),
            ],
        )

        self.assertEqual(expected.__repr__(), table.__repr__())
        self.assertIsNone(self.extractor.extract())

    def test_feature_table_extraction_with_description_batch(self) -> None:
        self._init_extractor(programmatic_description_enabled=True)
        self.extractor._client.list_projects.return_value = ["default"]
        self._mock_feature_table(labels={"label1": "value1"})

        feature_table_definition = self.extractor.extract()
        assert isinstance(feature_table_definition, TableMetadata)

        description = self.extractor.extract()
        assert isinstance(description, TableMetadata)
        expected = DescriptionMetadata(
            TestFeastExtractor._strip_margin(
                """* Created at **2020-01-01 00:00:00**
                  |* Labels:
                  |    * label1: **value1**
                  |"""
            ),
            "feature_table_details",
        )
        self.assertEqual(expected.__repr__(), description.description.__repr__())

        batch_source = self.extractor.extract()
        assert isinstance(batch_source, TableMetadata)
        expected = DescriptionMetadata(
            TestFeastExtractor._strip_margin(
                """```
                |fileOptions:
                |  fileFormat:
                |    parquetFormat: {}
                |  fileUrl: file:///some/location
                |type: BATCH_FILE
                |```"""
            ),
            "batch_source",
        )
        self.assertEqual(expected.__repr__(), batch_source.description.__repr__())

        self.assertIsNone(self.extractor.extract())

    def test_feature_table_extraction_with_description_stream(self) -> None:
        self._init_extractor(programmatic_description_enabled=True)
        self.extractor._client.list_projects.return_value = ["default"]
        self._mock_feature_table(add_stream_source=True)

        feature_table_definition = self.extractor.extract()
        assert isinstance(feature_table_definition, TableMetadata)

        description = self.extractor.extract()
        assert isinstance(description, TableMetadata)
        expected = DescriptionMetadata(
            TestFeastExtractor._strip_margin(
                """* Created at **2020-01-01 00:00:00**
                  |"""
            ),
            "feature_table_details",
        )
        self.assertEqual(expected.__repr__(), description.description.__repr__())

        batch_source = self.extractor.extract()
        assert isinstance(batch_source, TableMetadata)
        expected = DescriptionMetadata(
            TestFeastExtractor._strip_margin(
                """```
                |fileOptions:
                |  fileFormat:
                |    parquetFormat: {}
                |  fileUrl: file:///some/location
                |type: BATCH_FILE
                |```"""
            ),
            "batch_source",
        )
        self.assertEqual(expected.__repr__(), batch_source.description.__repr__())

        stream_source = self.extractor.extract()
        assert isinstance(stream_source, TableMetadata)
        expected = DescriptionMetadata(
            TestFeastExtractor._strip_margin(
                """```
                 |createdTimestampColumn: datetime
                 |eventTimestampColumn: datetime
                 |kafkaOptions:
                 |  bootstrapServers: broker1
                 |  messageFormat:
                 |    avroFormat:
                 |      schemaJson: '{"type": "record", "name": "DriverTrips", "fields": [{"name": "driver_id",
                 |        "type": "long"}, {"name": "trips_today", "type": "int"}, {"name": "datetime",
                 |        "type": {"type": "long", "logicalType": "timestamp-micros"}}]}'
                 |  topic: driver_trips
                 |type: STREAM_KAFKA
                 |```"""
            ),
            "stream_source",
        )
        self.assertEqual(expected.__repr__(), stream_source.description.__repr__())

        self.assertIsNone(self.extractor.extract())

    def _init_extractor(self, programmatic_description_enabled: bool = True) -> None:
        conf = {
            f'extractor.feast.{FeastExtractor.FEAST_ENDPOINT_CONFIG_KEY}': 'feast-core.example.com:6565',
            f'extractor.feast.{FeastExtractor.FEAST_SERVING_ENDPOINT_CONFIG_KEY}': 'feast-core.example.com:6566',
            f'extractor.feast.{FeastExtractor.FEAST_SERVICE_CONFIG_KEY}': 'unittest-feast-instance',
            f'extractor.feast.{FeastExtractor.DESCRIBE_FEATURE_TABLES}': programmatic_description_enabled,
        }
        self.extractor = FeastExtractor()
        self.extractor.init(
            Scoped.get_scoped_conf(
                conf=ConfigFactory.from_dict(conf), scope=self.extractor.get_scope()
            )
        )
        self.extractor._client = MagicMock(return_value=None)

    @staticmethod
    def _strip_margin(text: str) -> str:
        return re.sub("\n[ \t]*\\|", "\n", text)

    def _mock_feature_table(
            self, labels: dict = {}, add_stream_source: bool = False
    ) -> None:
        table_spec = {
            "name": "driver_trips",
            "entities": ["driver_id"],
            "features": [{"name": "trips_today", "valueType": "INT32"}],
            "labels": labels,
            "batchSource": {
                "type": "BATCH_FILE",
                "fileOptions": {
                    "fileFormat": {"parquetFormat": {}},
                    "fileUrl": "file:///some/location",
                },
            },
        }

        if add_stream_source:
            avro_schema_json = json.dumps(
                {
                    "type": "record",
                    "name": "DriverTrips",
                    "fields": [
                        {"name": "driver_id", "type": "long"},
                        {"name": "trips_today", "type": "int"},
                        {
                            "name": "datetime",
                            "type": {"type": "long", "logicalType": "timestamp-micros"},
                        },
                    ],
                }
            )

            table_spec["streamSource"] = {
                "type": "STREAM_KAFKA",
                "eventTimestampColumn": "datetime",
                "createdTimestampColumn": "datetime",
                "kafkaOptions": {
                    "bootstrapServers": "broker1",
                    "topic": "driver_trips",
                    "messageFormat": {
                        "avroFormat": {
                            "schemaJson": avro_schema_json,
                        }
                    },
                },
            }

        self.extractor._client.list_feature_tables.return_value = [
            FeatureTable.from_dict(
                {
                    "spec": table_spec,
                    "meta": {"createdTimestamp": "2020-01-01T00:00:00Z"},
                }
            )
        ]
        self.extractor._client.get_entity.return_value = Entity.from_dict(
            {
                "spec": {
                    "name": "driver_id",
                    "valueType": "INT64",
                    "description": "Internal identifier of the driver",
                }
            }
        )


if __name__ == "__main__":
    unittest.main()
