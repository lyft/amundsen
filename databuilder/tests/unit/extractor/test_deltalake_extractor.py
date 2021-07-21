# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import logging
import tempfile
import unittest
from typing import Dict

from pyhocon import ConfigFactory
# patch whole class to avoid actually calling for boto3.client during tests
from pyspark.sql import SparkSession
from pyspark.sql.catalog import Table

from databuilder import Scoped
from databuilder.extractor.delta_lake_metadata_extractor import (
    DeltaLakeMetadataExtractor, ScrapedColumnMetadata, ScrapedTableMetadata,
)
from databuilder.models.table_metadata import ColumnMetadata, TableMetadata


class TestDeltaLakeExtractor(unittest.TestCase):

    def setUp(self) -> None:
        logging.basicConfig(level=logging.INFO)
        self.spark = SparkSession.builder \
            .appName("Amundsen Delta Lake Metadata Extraction") \
            .master("local") \
            .config("spark.jars.packages", "io.delta:delta-core_2.12:0.7.0") \
            .config("spark.sql.warehouse.dir", tempfile.TemporaryDirectory()) \
            .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
            .config("spark.driver.host", "127.0.0.1") \
            .config("spark.driver.bindAddress", "127.0.0.1") \
            .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
            .getOrCreate()
        self.config_dict = {
            f'extractor.delta_lake_table_metadata.{DeltaLakeMetadataExtractor.CLUSTER_KEY}': 'test_cluster',
            f'extractor.delta_lake_table_metadata.{DeltaLakeMetadataExtractor.SCHEMA_LIST_KEY}': [],
            f'extractor.delta_lake_table_metadata.{DeltaLakeMetadataExtractor.EXCLUDE_LIST_SCHEMAS_KEY}': [],
            f'extractor.delta_lake_table_metadata.{DeltaLakeMetadataExtractor.DATABASE_KEY}': 'test_database',
            f'extractor.delta_lake_table_metadata.{DeltaLakeMetadataExtractor.DELTA_TABLES_ONLY}': False
        }
        conf = ConfigFactory.from_dict(self.config_dict)
        self.dExtractor = DeltaLakeMetadataExtractor()
        self.dExtractor.init(Scoped.get_scoped_conf(conf=conf, scope=self.dExtractor.get_scope()))
        self.dExtractor.set_spark(self.spark)
        self.setUpSchemas()

    def setUpSchemas(self) -> None:
        self.spark.sql("create schema if not exists test_schema1")
        self.spark.sql("create schema if not exists test_schema2")
        self.spark.sql("create table if not exists test_schema1.test_table1 (a string, b int) using delta")
        self.spark.sql("create table if not exists "
                       "test_schema1.test_table3 (c boolean, d float) using delta partitioned by (c)")
        self.spark.sql("create table if not exists test_schema2.test_parquet (a string) using parquet")
        self.spark.sql("create table if not exists test_schema2.test_table2 (a2 string, b2 double) using delta")
        # TODO do we even need to support views and none delta tables in this case?
        self.spark.sql("create view if not exists test_schema2.test_view1 as (select * from test_schema2.test_table2)")

        # Nested/Complex schemas
        self.spark.sql("create schema if not exists complex_schema")
        self.spark.sql("create table if not exists complex_schema.struct_table (a int, struct_col struct<b:string,"
                       "c:double>) using delta")
        self.spark.sql("create table if not exists complex_schema.nested_struct_table (a int, struct_col "
                       "struct<nested_struct_col:struct<b:string,c:double>>) using delta")
        self.spark.sql("create table if not exists complex_schema.array_table (a int, arr_col array<string>) using "
                       "delta")
        self.spark.sql("create table if not exists complex_schema.array_complex_elem_table (a int, arr_col "
                       "array<struct<b:string,c:double>>) using delta")
        self.spark.sql("create table if not exists complex_schema.map_table (a int, map_col map<int,string>) using "
                       "delta")
        self.spark.sql("create table if not exists complex_schema.map_complex_key_table (a int, map_col "
                       "map<struct<b:array<struct<c:int,d:string>>,e:double>,int>) using delta")
        self.spark.sql("create table if not exists complex_schema.map_complex_value_table (a int, map_col map<int,"
                       "struct<b:array<struct<c:int,d:string>>,e:double>>) using delta")
        self.spark.sql("create table if not exists complex_schema.map_complex_key_and_value_table (a int, map_col "
                       "map<struct<b:array<struct<c:int,d:string>>,e:double>,struct<f:array<struct<g:int,h:string>>,"
                       "i:double>>) using delta")

    def test_get_all_schemas(self) -> None:
        '''Tests getting all schemas'''
        actual_schemas = self.dExtractor.get_schemas([])
        self.assertEqual(["complex_schema", "default", "test_schema1", "test_schema2"], actual_schemas)

    def test_get_all_schemas_with_exclude(self) -> None:
        '''Tests the exclude list'''
        actual_schemas = self.dExtractor.get_schemas(["complex_schema", "default"])
        self.assertEqual(["test_schema1", "test_schema2"], actual_schemas)

    def test_get_all_tables(self) -> None:
        '''Tests table fetching'''
        actual = [x.name for x in self.dExtractor.get_all_tables(["test_schema1", "default"])]
        self.assertEqual(["test_table1", "test_table3"], actual)

    def test_scrape_table_detail(self) -> None:
        '''Test Table Detail Scraping'''
        actual = self.dExtractor.scrape_table_detail("test_schema1.test_table1")
        expected: Dict = {'createdAt': None,
                          'description': None,
                          'format': 'delta',
                          'id': None,
                          'lastModified': None,
                          'location': None,
                          'minReaderVersion': 1,
                          'minWriterVersion': 2,
                          'name': 'test_schema1.test_table1',
                          'numFiles': 0,
                          'partitionColumns': [],
                          'properties': {},
                          'sizeInBytes': 0}
        self.assertIsNotNone(actual)
        if actual:
            self.assertEqual(actual.keys(), expected.keys())
            self.assertEqual(actual['name'], expected['name'])
            self.assertEqual(actual['format'], expected['format'])

    def test_scrape_view_detail(self) -> None:
        actual = self.dExtractor.scrape_view_detail("test_schema2.test_view1")
        self.assertIsNotNone(actual)
        expected = {'Created By': 'Spark 3.0.1',
                    'Created Time': None,
                    'Database': 'test_schema2',
                    'Last Access': 'UNKNOWN',
                    'Table': 'test_view1',
                    'Table Properties': '[view.catalogAndNamespace.numParts=2, '
                                        'view.query.out.col.0=a2, view.query.out.numCols=2, '
                                        'view.query.out.col.1=b2, '
                                        'view.catalogAndNamespace.part.0=spark_catalog, '
                                        'view.catalogAndNamespace.part.1=default]',
                    'Type': 'VIEW',
                    'View Catalog and Namespace': 'spark_catalog.default',
                    'View Original Text': '(select * from test_schema2.test_table2)',
                    'View Query Output Columns': '[a2, b2]',
                    'View Text': '(select * from test_schema2.test_table2)'}
        if actual:
            actual['Created Time'] = None
            self.assertEqual(actual, expected)

    def test_fetch_partitioned_delta_columns(self) -> None:
        actual = self.dExtractor.fetch_columns("test_schema1", "test_table3")
        partition_column = ScrapedColumnMetadata(name="c", description=None, data_type="boolean", sort_order=0)
        partition_column.set_is_partition(True)
        expected = [partition_column,
                    ScrapedColumnMetadata(name="d", description=None, data_type="float", sort_order=1)]
        for a, b in zip(actual, expected):
            self.assertEqual(a, b)

    def test_fetch_delta_columns(self) -> None:
        actual = self.dExtractor.fetch_columns("test_schema1", "test_table1")
        expected = [ScrapedColumnMetadata(name="a", description=None, data_type="string", sort_order=0),
                    ScrapedColumnMetadata(name="b", description=None, data_type="int", sort_order=1)]
        for a, b in zip(actual, expected):
            self.assertEqual(a, b)

    def test_scrape_tables(self) -> None:
        table = Table(name="test_table1", database="test_schema1", description=None,
                      tableType="delta", isTemporary=False)
        actual = self.dExtractor.scrape_table(table)

        expected = ScrapedTableMetadata(schema="test_schema1", table="test_table1")
        expected.set_columns([ScrapedColumnMetadata(name="a", description=None, data_type="string", sort_order=0),
                              ScrapedColumnMetadata(name="b", description=None, data_type="int", sort_order=1)])
        if actual is not None:
            self.assertEqual(expected.schema, actual.schema)
            self.assertEqual(expected.table, actual.table)
            self.assertEqual(expected.columns, actual.columns)
            self.assertEqual(expected.failed_to_scrape, actual.failed_to_scrape)
            self.assertEqual(expected.is_view, actual.is_view)
            self.assertIsNotNone(actual.table_detail)
        else:
            self.assertIsNotNone(actual)

    def test_create_table_metadata(self) -> None:
        scraped = ScrapedTableMetadata(schema="test_schema1", table="test_table1")
        scraped.set_columns([ScrapedColumnMetadata(name="a", description=None, data_type="string", sort_order=0),
                             ScrapedColumnMetadata(name="b", description=None, data_type="int", sort_order=1)])
        created_metadata = self.dExtractor.create_table_metadata(scraped)
        expected = TableMetadata("test_database", "test_cluster", "test_schema1", "test_table1", description=None,
                                 columns=[ColumnMetadata("a", None, "string", 0),
                                          ColumnMetadata("b", None, "int", 1)])
        self.assertEqual(str(expected), str(created_metadata))

    def test_create_last_updated(self) -> None:
        scraped_table = self.dExtractor.scrape_table(Table("test_table1", "test_schema1", None, "delta", False))
        actual_last_updated = None
        if scraped_table:
            actual_last_updated = self.dExtractor.create_table_last_updated(scraped_table)
        self.assertIsNotNone(actual_last_updated)

    def test_extract(self) -> None:
        ret = []
        data = self.dExtractor.extract()
        while data is not None:
            ret.append(data)
            data = self.dExtractor.extract()
        self.assertEqual(len(ret), 24)

    def test_extract_with_only_specific_schemas(self) -> None:
        self.config_dict = {
            f'extractor.delta_lake_table_metadata.{DeltaLakeMetadataExtractor.CLUSTER_KEY}': 'test_cluster',
            f'extractor.delta_lake_table_metadata.{DeltaLakeMetadataExtractor.SCHEMA_LIST_KEY}': ['test_schema2'],
            f'extractor.delta_lake_table_metadata.{DeltaLakeMetadataExtractor.EXCLUDE_LIST_SCHEMAS_KEY}': [],
            f'extractor.delta_lake_table_metadata.{DeltaLakeMetadataExtractor.DATABASE_KEY}': 'test_database'
        }
        conf = ConfigFactory.from_dict(self.config_dict)
        self.dExtractor.init(Scoped.get_scoped_conf(conf=conf,
                                                    scope=self.dExtractor.get_scope()))
        ret = []
        data = self.dExtractor.extract()
        while data is not None:
            ret.append(data)
            data = self.dExtractor.extract()
        self.assertEqual(len(ret), 2)

    def test_extract_when_excluding(self) -> None:
        self.config_dict = {
            f'extractor.delta_lake_table_metadata.{DeltaLakeMetadataExtractor.CLUSTER_KEY}': 'test_cluster',
            f'extractor.delta_lake_table_metadata.{DeltaLakeMetadataExtractor.SCHEMA_LIST_KEY}': [],
            f'extractor.delta_lake_table_metadata.{DeltaLakeMetadataExtractor.EXCLUDE_LIST_SCHEMAS_KEY}':
                ['test_schema2'],
            f'extractor.delta_lake_table_metadata.{DeltaLakeMetadataExtractor.DATABASE_KEY}': 'test_database'
        }
        conf = ConfigFactory.from_dict(self.config_dict)
        self.dExtractor.init(Scoped.get_scoped_conf(conf=conf,
                                                    scope=self.dExtractor.get_scope()))
        ret = []
        data = self.dExtractor.extract()
        while data is not None:
            ret.append(data)
            data = self.dExtractor.extract()
        self.assertEqual(len(ret), 20)

    def test_table_does_not_exist(self) -> None:
        table = Table(name="test_table5", database="test_schema1", description=None,
                      tableType="delta", isTemporary=False)
        actual = self.dExtractor.scrape_table(table)
        self.assertIsNone(actual)

    def test_scrape_all_tables(self) -> None:
        tables = [Table(name="test_table1", database="test_schema1", description=None,
                        tableType="delta", isTemporary=False),
                  Table(name="test_table3", database="test_schema1", description=None,
                        tableType="delta", isTemporary=False)]
        actual = self.dExtractor.scrape_all_tables(tables)
        self.assertEqual(2, len(actual))

    def test_scrape_complex_schema_no_config(self) -> None:
        # Don't set the extract_nested_columns config to verify backwards compatibility
        actual = self.dExtractor.fetch_columns(schema="complex_schema", table="struct_table")
        self.assertEqual(actual, [
            ScrapedColumnMetadata(name="a", description=None, data_type="int", sort_order=0),
            ScrapedColumnMetadata(name="struct_col", description=None, data_type="struct<b:string,c:double>",
                                  sort_order=1),
        ])

    def test_scrape_complex_schema_columns(self) -> None:
        # set extract_nested_columns to True to test complex column extraction
        self.dExtractor.extract_nested_columns = True
        expected_dict = {
            "struct_table": [
                ScrapedColumnMetadata(name="a", description=None, data_type="int", sort_order=0),
                ScrapedColumnMetadata(name="struct_col", description=None, data_type="struct<b:string,c:double>",
                                      sort_order=1),
                ScrapedColumnMetadata(name="struct_col.b", description=None, data_type="string", sort_order=2),
                ScrapedColumnMetadata(name="struct_col.c", description=None, data_type="double", sort_order=3),
            ],
            "nested_struct_table": [
                ScrapedColumnMetadata(name="a", description=None, data_type="int", sort_order=0),
                ScrapedColumnMetadata(name="struct_col", description=None,
                                      data_type="struct<nested_struct_col:struct<b:string,c:double>>", sort_order=1),
                ScrapedColumnMetadata(name="struct_col.nested_struct_col", description=None,
                                      data_type="struct<b:string,c:double>", sort_order=2),
                ScrapedColumnMetadata(name="struct_col.nested_struct_col.b", description=None, data_type="string",
                                      sort_order=3),
                ScrapedColumnMetadata(name="struct_col.nested_struct_col.c", description=None, data_type="double",
                                      sort_order=4),
            ],
            "array_table": [
                ScrapedColumnMetadata(name="a", description=None, data_type="int", sort_order=0),
                ScrapedColumnMetadata(name="arr_col", description=None, data_type="array<string>", sort_order=1),
            ],
            "array_complex_elem_table": [
                ScrapedColumnMetadata(name="a", description=None, data_type="int", sort_order=0),
                ScrapedColumnMetadata(name="arr_col", description=None, data_type="array<struct<b:string,c:double>>",
                                      sort_order=1),
                ScrapedColumnMetadata(name="arr_col.b", description=None, data_type="string", sort_order=2),
                ScrapedColumnMetadata(name="arr_col.c", description=None, data_type="double", sort_order=3),
            ],
            "map_table": [
                ScrapedColumnMetadata(name="a", description=None, data_type="int", sort_order=0),
                ScrapedColumnMetadata(name="map_col", description=None, data_type="map<int,string>", sort_order=1),
            ],
            "map_complex_key_table": [
                ScrapedColumnMetadata(name="a", description=None, data_type="int", sort_order=0),
                ScrapedColumnMetadata(name="map_col", description=None,
                                      data_type="map<struct<b:array<struct<c:int,d:string>>,e:double>,int>",
                                      sort_order=1),
            ],
            "map_complex_value_table": [
                ScrapedColumnMetadata(name="a", description=None, data_type="int", sort_order=0),
                ScrapedColumnMetadata(name="map_col", description=None, data_type="map<int,"
                                                                                  "struct<b:array<struct<c:int,"
                                                                                  "d:string>>,e:double>>",
                                      sort_order=1),
                ScrapedColumnMetadata(name="map_col.b", description=None, data_type="array<struct<c:int,d:string>>",
                                      sort_order=2),
                ScrapedColumnMetadata(name="map_col.b.c", description=None, data_type="int", sort_order=3),
                ScrapedColumnMetadata(name="map_col.b.d", description=None, data_type="string", sort_order=4),
                ScrapedColumnMetadata(name="map_col.e", description=None, data_type="double", sort_order=5),
            ],
            "map_complex_key_and_value_table": [
                ScrapedColumnMetadata(name="a", description=None, data_type="int", sort_order=0),
                ScrapedColumnMetadata(name="map_col", description=None,
                                      data_type="map<struct<b:array<struct<c:int,d:string>>,e:double>,"
                                                "struct<f:array<struct<g:int,h:string>>,i:double>>",
                                      sort_order=1),
                ScrapedColumnMetadata(name="map_col.f", description=None, data_type="array<struct<g:int,h:string>>",
                                      sort_order=2),
                ScrapedColumnMetadata(name="map_col.f.g", description=None, data_type="int", sort_order=3),
                ScrapedColumnMetadata(name="map_col.f.h", description=None, data_type="string", sort_order=4),
                ScrapedColumnMetadata(name="map_col.i", description=None, data_type="double", sort_order=5),
            ],
        }
        for table_name, expected in expected_dict.items():
            actual = self.dExtractor.fetch_columns(schema="complex_schema", table=table_name)
            self.assertEqual(len(expected), len(actual), f"{table_name} failed")
            self.assertListEqual(expected, actual, f"{table_name} failed")


if __name__ == '__main__':
    unittest.main()
