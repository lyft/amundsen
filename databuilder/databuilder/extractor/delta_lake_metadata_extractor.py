# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import concurrent.futures
import logging
from collections import namedtuple
from datetime import datetime
from typing import (  # noqa: F401
    Any, Dict, Iterator, List, Optional, Union,
)

from pyhocon import ConfigFactory, ConfigTree  # noqa: F401
from pyspark.sql import SparkSession
from pyspark.sql.catalog import Table
from pyspark.sql.types import (
    ArrayType, MapType, StructType,
)
from pyspark.sql.utils import AnalysisException

from databuilder.extractor.base_extractor import Extractor
from databuilder.models.table_last_updated import TableLastUpdated
from databuilder.models.table_metadata import ColumnMetadata, TableMetadata

TableKey = namedtuple('TableKey', ['schema', 'table_name'])

LOGGER = logging.getLogger(__name__)


# TODO once column tags work properly, consider deprecating this for TableMetadata directly
class ScrapedColumnMetadata(object):
    def __init__(self, name: str, data_type: str, description: Optional[str], sort_order: int):
        self.name = name
        self.data_type = data_type
        self.description = description
        self.sort_order = sort_order
        self.is_partition = False
        self.attributes: Dict[str, str] = {}

    def set_is_partition(self, is_partition: bool) -> None:
        self.is_partition = is_partition

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ScrapedColumnMetadata):
            return False
        return (self.name == other.name and
                self.data_type == other.data_type and
                self.description == other.description and
                self.sort_order == other.sort_order and
                self.is_partition == other.is_partition and
                self.attributes == other.attributes)

    def __repr__(self) -> str:
        return f'{self.name}:{self.data_type}'


# TODO consider deprecating this for using TableMetadata directly
class ScrapedTableMetadata(object):
    LAST_MODIFIED_KEY = 'lastModified'
    DESCRIPTION_KEY = 'description'
    TABLE_FORMAT_KEY = 'format'

    def __init__(self, schema: str, table: str):
        self.schema: str = schema
        self.table: str = table
        self.table_detail: Optional[Dict] = None
        self.view_detail: Optional[Dict] = None
        self.is_view: bool = False
        self.failed_to_scrape: bool = False
        self.columns: Optional[List[ScrapedColumnMetadata]] = None

    def set_table_detail(self, table_detail: Dict) -> None:
        self.table_detail = table_detail
        self.is_view = False
        self.failed_to_scrape = False

    def set_view_detail(self, view_detail: Dict) -> None:
        self.view_detail = view_detail
        self.is_view = True
        self.failed_to_scrape = False

    def get_details(self) -> Optional[Dict]:
        if self.is_view:
            return self.view_detail
        else:
            return self.table_detail

    def get_full_table_name(self) -> str:
        return self.schema + "." + self.table

    def set_failed_to_scrape(self) -> None:
        self.failed_to_scrape = True

    def set_columns(self, column_list: List[ScrapedColumnMetadata]) -> None:
        self.columns = column_list

    def get_last_modified(self) -> Optional[datetime]:
        details = self.get_details()
        if details and self.LAST_MODIFIED_KEY in details:
            return details[self.LAST_MODIFIED_KEY]
        else:
            return None

    def get_table_description(self) -> Optional[str]:
        details = self.get_details()
        if details and self.DESCRIPTION_KEY in details:
            return details[self.DESCRIPTION_KEY]
        else:
            return None

    def is_delta_table(self) -> bool:
        details = self.get_details()
        if details and self.TABLE_FORMAT_KEY in details:
            return details[self.TABLE_FORMAT_KEY].lower() == 'delta'
        else:
            return False

    def __repr__(self) -> str:
        return f'{self.schema}.{self.table}'


class DeltaLakeMetadataExtractor(Extractor):
    """
    Extracts Delta Lake Metadata.
    This requires a spark session to run that has a hive metastore populated with all of the delta tables
    that you are interested in.

    By default, the extractor does not extract nested columns. Set the EXTRACT_NESTED_COLUMNS conf to True
    if you would like nested columns extracted
    """
    # CONFIG KEYS
    DATABASE_KEY = "database"
    # If you want to exclude specific schemas
    EXCLUDE_LIST_SCHEMAS_KEY = "exclude_list"
    # If you want to only include specific schemas
    SCHEMA_LIST_KEY = "schema_list"
    CLUSTER_KEY = "cluster"
    # By default, this will only process and emit delta-lake tables, but it can support all hive table types.
    DELTA_TABLES_ONLY = "delta_tables_only"
    DEFAULT_CONFIG = ConfigFactory.from_dict({DATABASE_KEY: "delta",
                                              EXCLUDE_LIST_SCHEMAS_KEY: [],
                                              SCHEMA_LIST_KEY: [],
                                              DELTA_TABLES_ONLY: True})
    PARTITION_COLUMN_TAG = 'is_partition'

    # For backwards compatibility, the delta lake extractor does not extract nested columns for indexing
    # Set this to true in the conf if you would like nested columns & complex types fully extracted
    EXTRACT_NESTED_COLUMNS = "extract_nested_columns"

    def init(self, conf: ConfigTree) -> None:
        self.conf = conf.with_fallback(DeltaLakeMetadataExtractor.DEFAULT_CONFIG)
        self._extract_iter = None  # type: Union[None, Iterator]
        self._cluster = self.conf.get_string(DeltaLakeMetadataExtractor.CLUSTER_KEY)
        self._db = self.conf.get_string(DeltaLakeMetadataExtractor.DATABASE_KEY)
        self.exclude_list = self.conf.get_list(DeltaLakeMetadataExtractor.EXCLUDE_LIST_SCHEMAS_KEY)
        self.schema_list = self.conf.get_list(DeltaLakeMetadataExtractor.SCHEMA_LIST_KEY)
        self.delta_tables_only = self.conf.get_bool(DeltaLakeMetadataExtractor.DELTA_TABLES_ONLY)
        self.extract_nested_columns = self.conf.get_bool(DeltaLakeMetadataExtractor.EXTRACT_NESTED_COLUMNS,
                                                         default=False)

    def set_spark(self, spark: SparkSession) -> None:
        self.spark = spark

    def extract(self) -> Union[TableMetadata, TableLastUpdated, None]:
        if not self._extract_iter:
            self._extract_iter = self._get_extract_iter()
        try:
            return next(self._extract_iter)
        except StopIteration:
            return None

    def get_scope(self) -> str:
        return 'extractor.delta_lake_table_metadata'

    def _get_extract_iter(self) -> Iterator[Union[TableMetadata, TableLastUpdated, None]]:
        """
        Given either a list of schemas, or a list of exclude schemas,
        it will query hive metastore and then access delta log
        to get all of the metadata for your delta tables. It will produce:
         - table and column metadata
         - last updated information
        """
        if self.schema_list:
            LOGGER.info("working on %s", self.schema_list)
            tables = self.get_all_tables(self.schema_list)
        else:
            LOGGER.info("fetching all schemas")
            LOGGER.info("Excluding: %s", self.exclude_list)
            schemas = self.get_schemas(self.exclude_list)
            LOGGER.info("working on %s", schemas)
            tables = self.get_all_tables(schemas)
        # TODO add the programmatic information as well?
        # TODO add watermarks
        scraped_tables = self.scrape_all_tables(tables)
        for scraped_table in scraped_tables:
            if not scraped_table:
                continue
            if self.delta_tables_only and not scraped_table.is_delta_table():
                LOGGER.info("Skipping none delta table %s", scraped_table.table)
                continue
            else:
                yield self.create_table_metadata(scraped_table)
                last_updated = self.create_table_last_updated(scraped_table)
                if last_updated:
                    yield last_updated

    def get_schemas(self, exclude_list: List[str]) -> List[str]:
        '''Returns all schemas.'''
        schemas = self.spark.catalog.listDatabases()
        ret = []
        for schema in schemas:
            if schema.name not in exclude_list:
                ret.append(schema.name)
        return ret

    def get_all_tables(self, schemas: List[str]) -> List[Table]:
        '''Returns all tables.'''
        ret = []
        for schema in schemas:
            ret.extend(self.get_tables_for_schema(schema))
        return ret

    def get_tables_for_schema(self, schema: str) -> List[Table]:
        '''Returns all tables for a specific schema.'''
        return self.spark.catalog.listTables(schema)

    def scrape_all_tables(self, tables: List[Table]) -> List[Optional[ScrapedTableMetadata]]:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [executor.submit(self.scrape_table, table) for table in tables]
        scraped_tables = [f.result() for f in futures]
        return scraped_tables

    def scrape_table(self, table: Table) -> Optional[ScrapedTableMetadata]:
        '''Takes a table object and creates a scraped table metadata object.'''
        met = ScrapedTableMetadata(schema=table.database, table=table.name)
        table_name = met.get_full_table_name()
        if table.tableType and table.tableType.lower() != 'view':
            table_detail = self.scrape_table_detail(table_name)
            if table_detail is None:
                LOGGER.error("Failed to parse table " + table_name)
                met.set_failed_to_scrape()
                return None
            else:
                LOGGER.info("Successfully parsed table " + table_name)
                met.set_table_detail(table_detail)
        else:
            view_detail = self.scrape_view_detail(table_name)
            if view_detail is None:
                LOGGER.error("Failed to parse view " + table_name)
                met.set_failed_to_scrape()
                return None
            else:
                LOGGER.info("Successfully parsed view " + table_name)
                met.set_view_detail(view_detail)
        columns = self.fetch_columns(met.schema, met.table)
        if not columns:
            LOGGER.error("Failed to parse columns for " + table_name)
            return None
        else:
            met.set_columns(columns)
            return met

    def scrape_table_detail(self, table_name: str) -> Optional[Dict]:
        try:
            table_details_df = self.spark.sql(f"describe detail {table_name}")
            table_detail = table_details_df.collect()[0]
            return table_detail.asDict()
        except Exception as e:
            LOGGER.error(e)
            return None

    def scrape_view_detail(self, view_name: str) -> Optional[Dict]:
        # TODO the blanket try catches need to be changed
        describeExtendedOutput = []
        try:
            describeExtendedOutput = self.spark.sql(f"describe extended {view_name}").collect()
        except Exception as e:
            LOGGER.error(e)
            return None
        view_detail = {}
        startAdding = False
        for row in describeExtendedOutput:
            row_dict = row.asDict()
            if startAdding:
                view_detail[row_dict['col_name']] = row_dict['data_type']
            if "# Detailed Table" in row_dict['col_name']:
                # Then start parsing
                startAdding = True
        return view_detail

    def fetch_columns(self, schema: str, table: str) -> List[ScrapedColumnMetadata]:
        '''This fetches delta table columns, which unfortunately
        in the general case cannot rely on spark.catalog.listColumns.'''
        raw_columns = []
        field_dict: Dict[str, Any] = {}
        table_name = f"{schema}.{table}"
        try:
            raw_columns = self.spark.sql(f"describe {table_name}").collect()
            for field in self.spark.table(f"{table_name}").schema:
                field_dict[field.name] = field
        except AnalysisException as e:
            LOGGER.error(e)
            return raw_columns
        parsed_columns: Dict[str, ScrapedColumnMetadata] = {}
        partition_cols = False
        sort_order = 0
        for row in raw_columns:
            col_name = row['col_name']
            # NOTE: the behavior of describe has changed between spark 2 and spark 3
            if col_name == '' or '#' in col_name:
                partition_cols = True
                continue
            if not partition_cols:
                # Attempt to extract nested columns if conf value requests it
                if self.extract_nested_columns \
                        and col_name in field_dict \
                        and self.is_complex_delta_type(field_dict[col_name].dataType):
                    sort_order = self._iterate_nested_columns("", field_dict[col_name], parsed_columns, 1)
                else:
                    column = ScrapedColumnMetadata(
                        name=row['col_name'],
                        description=row['comment'] if row['comment'] else None,
                        data_type=row['data_type'],
                        sort_order=sort_order
                    )
                    parsed_columns[row['col_name']] = column
                    sort_order += 1
            else:
                if row['data_type'] in parsed_columns:
                    LOGGER.debug(f"Adding partition column table for {row['data_type']}")
                    parsed_columns[row['data_type']].set_is_partition(True)
                elif row['col_name'] in parsed_columns:
                    LOGGER.debug(f"Adding partition column table for {row['col_name']}")
                    parsed_columns[row['col_name']].set_is_partition(True)
        return list(parsed_columns.values())

    def _iterate_nested_columns(self,
                                parent: str,
                                curr_field: Union[StructType, ArrayType, MapType],
                                parsed_columns: Dict,
                                total_cols: int) -> int:
        if len(parent) > 0:
            col_name = f"{parent}.{curr_field.name}"
        else:
            col_name = curr_field.name

        if self.is_complex_delta_type(curr_field.dataType):
            parsed_columns[col_name] = ScrapedColumnMetadata(
                name=col_name,
                data_type=curr_field.dataType.simpleString(),
                sort_order=total_cols,
                description=None,
            )
            total_cols += 1
            if self.is_struct_type(curr_field.dataType):
                total_cols = self._iterate_complex_type(curr_field.dataType, col_name, parsed_columns, total_cols)
            elif self.is_array_type(curr_field.dataType) \
                    and self.is_complex_delta_type(curr_field.dataType.elementType):
                total_cols = self._iterate_complex_type(curr_field.dataType.elementType, col_name, parsed_columns,
                                                        total_cols)
            elif self.is_map_type(curr_field.dataType) \
                    and self.is_complex_delta_type(curr_field.dataType.valueType):
                total_cols = self._iterate_complex_type(curr_field.dataType.valueType, col_name, parsed_columns,
                                                        total_cols)

            return total_cols
        else:
            parsed_columns[col_name] = ScrapedColumnMetadata(
                name=col_name,
                data_type=curr_field.dataType.simpleString(),
                sort_order=total_cols,
                description=None,
            )
            return total_cols + 1

    def _iterate_complex_type(self, delta_type: Any, col_name: str, parsed_columns: Dict, total_cols: int) -> int:
        if self.is_struct_type(delta_type):
            for field in delta_type:
                total_cols = self._iterate_nested_columns(col_name, field, parsed_columns, total_cols)
        else:
            total_cols = self._iterate_nested_columns(col_name, delta_type, parsed_columns, total_cols)
        return total_cols

    def create_table_metadata(self, table: ScrapedTableMetadata) -> TableMetadata:
        '''Creates the amundsen table metadata object from the ScrapedTableMetadata object.'''
        amundsen_columns = []
        if table.columns:
            for column in table.columns:
                amundsen_columns.append(
                    ColumnMetadata(name=column.name,
                                   description=column.description,
                                   col_type=column.data_type,
                                   sort_order=column.sort_order)
                )
        description = table.get_table_description()
        return TableMetadata(self._db,
                             self._cluster,
                             table.schema,
                             table.table,
                             description,
                             amundsen_columns,
                             table.is_view)

    def create_table_last_updated(self, table: ScrapedTableMetadata) -> Optional[TableLastUpdated]:
        '''Creates the amundsen table last updated metadata object from the ScrapedTableMetadata object.'''
        last_modified = table.get_last_modified()
        if last_modified:
            return TableLastUpdated(table_name=table.table,
                                    last_updated_time_epoch=int(last_modified.timestamp()),
                                    schema=table.schema,
                                    db=self._db,
                                    cluster=self._cluster)
        else:
            return None

    def is_complex_delta_type(self, delta_type: Any) -> bool:
        return isinstance(delta_type, StructType) or \
            isinstance(delta_type, ArrayType) or \
            isinstance(delta_type, MapType)

    def is_struct_type(self, delta_type: Any) -> bool:
        return isinstance(delta_type, StructType)

    def is_array_type(self, delta_type: Any) -> bool:
        return isinstance(delta_type, ArrayType)

    def is_map_type(self, delta_type: Any) -> bool:
        return isinstance(delta_type, MapType)
