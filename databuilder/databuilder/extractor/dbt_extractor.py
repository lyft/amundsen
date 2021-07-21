# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import json
import logging
import os
from enum import Enum
from typing import (
    Dict, Iterator, List, Optional, Tuple, Union,
)

from pyhocon import ConfigTree

from databuilder.extractor.base_extractor import Extractor
from databuilder.models.badge import Badge, BadgeMetadata
from databuilder.models.table_lineage import TableLineage
from databuilder.models.table_metadata import ColumnMetadata, TableMetadata
from databuilder.models.table_source import TableSource

LOGGER = logging.getLogger(__name__)


DBT_CATALOG_REQD_KEYS = ['nodes']
DBT_MANIFEST_REQD_KEYS = ['nodes', 'child_map']
DBT_MODEL_TYPE = 'model'
DBT_MODEL_PREFIX = 'model.'
DBT_TEST_PREFIX = 'test.'


class DBT_TAG_AS(Enum):
    BADGE = 'badge'
    TAG = 'tag'


class DBT_MODEL_NAME_KEY(Enum):
    ALIAS = 'alias'
    NAME = 'name'


class InvalidDbtInputs(Exception):
    pass


class DbtExtractor(Extractor):
    """
    Extracts metadata from the dbt manifest.json and catalog.json files.
    At least one of a manifest or a catalog (or both) must be provided.
    The location of the file or a valid Python dictionary of the content
    can be provided.

    Currently the following assets are extracted from these files:

    - Tables
    - Columns
    - Definitions
    - Table lineage
    - Tags (converted to Amundsen Badges)

    Additional metadagta exists and may be extracted in the future:

    - Run / test outcomes
    - Freshness
    - Hooks (as programatic description?)
    - Analysis (as queries for a table??)
    - Table / column level statistics
    - Table comments (as programatic descriptoins)
    """

    CATALOG_JSON = "catalog_json"
    MANIFEST_JSON = "manifest_json"
    DATABASE_NAME = 'database_name'

    # Dbt Extract Options
    EXTRACT_TABLES = 'extract_tables'
    EXTRACT_DESCRIPTIONS = 'extract_descriptions'
    EXTRACT_TAGS = 'extract_tags'
    EXTRACT_LINEAGE = 'extract_lineage'
    SOURCE_URL = 'source_url'  # Base source code URL for the repo containing dbt workflows
    IMPORT_TAGS_AS = 'import_tags_as'
    SCHEMA_FILTER = 'schema_filter'  # Only extract dbt models from this schema, defaults to all models
    MODEL_NAME_KEY = 'model_name_key'  # Whether to use the "name" or "alias" from dbt as the Amundsen name

    # Makes all db, schema, cluster and table names lowercase. This is done so that table metadata from dbt
    # with the default key `Sample://Cluster/Schema/Table` match existing metadata that Amundsen has from
    # the database, which may be `sample://cluster/schema/table`.
    # Most databases that dbt integrates with either use lowercase by default in the information schema
    # or the default Amundsen extractor applies a `lower(...)` function to the result (e.g. snowflake).
    # However, Amundsen does not currently enforce a consistent convention and some databases do support
    # upper and lowercase naming conventions (e.g. Redshift). It may be useful to set this False in the
    # config if the table metadata keys in your database are not all lowercase and to then use a transformer to
    # properly format the string value.
    FORCE_TABLE_KEY_LOWER = 'force_table_key_lower'

    def init(self, conf: ConfigTree) -> None:
        self._conf = conf
        self._database_name = conf.get_string(DbtExtractor.DATABASE_NAME)
        self._dbt_manifest = conf.get_string(DbtExtractor.MANIFEST_JSON)
        self._dbt_catalog = conf.get_string(DbtExtractor.CATALOG_JSON)
        # Extract options
        self._extract_tables = conf.get_bool(DbtExtractor.EXTRACT_TABLES, True)
        self._extract_descriptions = conf.get_bool(DbtExtractor.EXTRACT_DESCRIPTIONS, True)
        self._extract_tags = conf.get_bool(DbtExtractor.EXTRACT_TAGS, True)
        self._extract_lineage = conf.get_bool(DbtExtractor.EXTRACT_LINEAGE, True)
        self._source_url = conf.get_string(DbtExtractor.SOURCE_URL, None)
        self._force_table_key_lower = conf.get_bool(DbtExtractor.FORCE_TABLE_KEY_LOWER, True)
        self._dbt_tag_as = DBT_TAG_AS(conf.get_string(DbtExtractor.IMPORT_TAGS_AS, DBT_TAG_AS.BADGE.value))
        self._schema_filter = conf.get_string(DbtExtractor.SCHEMA_FILTER, '')
        self._model_name_key = DBT_MODEL_NAME_KEY(
            conf.get_string(DbtExtractor.MODEL_NAME_KEY, DBT_MODEL_NAME_KEY.NAME.value)).value
        self._clean_inputs()

        self._extract_iter: Union[None, Iterator] = None

    def get_scope(self) -> str:
        return "extractor.dbt"

    def _validate_catalog(self) -> None:
        # Load the catalog file if needed and run basic validation on the content
        try:
            self._dbt_catalog = json.loads(self._dbt_catalog)
        except Exception:
            try:
                with open(self._dbt_catalog, 'rb') as f:
                    self._dbt_catalog = json.load(f)
            except Exception as e:
                raise InvalidDbtInputs(
                    'Invalid content for a dbt catalog was provided. Must be a valid Python '
                    'dictionary or the location of a file. Error received: %s' % e
                )
        for catalog_key in DBT_CATALOG_REQD_KEYS:
            if catalog_key not in self._dbt_catalog:
                raise InvalidDbtInputs(
                    "Dbt catalog file must contain keys: %s, found keys: %s"
                    % (DBT_CATALOG_REQD_KEYS, self._dbt_catalog.keys())
                )

    def _validate_manifest(self) -> None:
        # Load the manifest file if needed and run basic validation on the content
        try:
            self._dbt_manifest = json.loads(self._dbt_manifest)
        except Exception:
            try:
                with open(self._dbt_manifest, 'rb') as f:
                    self._dbt_manifest = json.load(f)
            except Exception as e:
                raise InvalidDbtInputs(
                    'Invalid content for a dbt manifest was provided. Must be a valid Python '
                    'dictionary or the location of a file. Error received: %s' % e
                )
        for manifest_key in DBT_MANIFEST_REQD_KEYS:
            if manifest_key not in self._dbt_manifest:
                raise InvalidDbtInputs(
                    "Dbt manifest file must contain keys: %s, found keys: %s"
                    % (DBT_MANIFEST_REQD_KEYS, self._dbt_manifest.keys())
                )

    def _clean_inputs(self) -> None:
        """
        Validates the dbt input to ensure that at least one of the inputs
        (manifest.json or catalog.json) are provided. Once validated, the
        inputs are sanitized to ensure that the `self._dbt_manifest` and
        `self._dbt_catalog` are valid Python dictionaries.
        """
        if self._database_name is None:
            raise InvalidDbtInputs(
                'Must provide a database name that corresponds to this dbt catalog and manifest.'
            )

        if not self._dbt_manifest or not self._dbt_catalog:
            raise InvalidDbtInputs(
                'Must provide a dbt manifest file and dbt catalog file.'
            )

        self._validate_catalog()
        self._validate_manifest()

    def extract(self) -> Union[TableMetadata, None]:
        """
        For every feature table from Feast, a multiple objets are extracted:

        1. TableMetadata with feature table description
        2. Programmatic Description of the feature table, containing
           metadata - date of creation and labels
        3. Programmatic Description with Batch Source specification
        4. (if applicable) Programmatic Description with Stream Source
           specification
        """
        if not self._extract_iter:
            self._extract_iter = self._get_extract_iter()
        try:
            return next(self._extract_iter)
        except StopIteration:
            return None

    def _default_sanitize(self, s: str) -> str:
        """
        Default function that will be run to convert the value of a string to lowercase.
        """
        if s and self._force_table_key_lower:
            s = s.lower()
        return s

    def _get_table_descriptions(self, manifest_content: Dict) -> Tuple[Optional[str], Optional[str]]:
        """
        Gets a description and description source for a table.
        """
        desc, desc_src = None, None
        if self._extract_descriptions:
            desc = manifest_content.get('description')
            desc_src = 'dbt description'
        return desc, desc_src

    def _get_table_tags_badges(self, manifest_content: Dict) -> Tuple[Optional[List[str]], Optional[List[str]]]:
        """
        Gets tags or badges for a given table. At most one of these values will not be null.
        """
        tags, tbl_badges = None, None
        if self._extract_tags:
            if self._dbt_tag_as == DBT_TAG_AS.BADGE:
                tbl_badges = manifest_content.get('tags')
            elif self._dbt_tag_as == DBT_TAG_AS.TAG:
                tags = manifest_content.get('tags')
        return tags, tbl_badges

    def _can_yield_schema(self, schema: str) -> bool:
        """
        Whether or not the schema can be yielded based on the schema filter criteria.
        """
        return (not self._schema_filter) or (self._schema_filter.lower() == schema.lower())

    def _get_extract_iter(self) -> Iterator[Union[TableMetadata, BadgeMetadata, TableSource, TableLineage]]:
        """
        Generates the extract iterator for all of the model types created by the dbt files.
        """
        dbt_id_to_table_key = {}
        for tbl_node, manifest_content in self._dbt_manifest['nodes'].items():

            if manifest_content['resource_type'] == DBT_MODEL_TYPE and tbl_node in self._dbt_catalog['nodes']:
                LOGGER.info(
                    'Extracting dbt {}.{}'.format(manifest_content['schema'], manifest_content[self._model_name_key])
                )

                catalog_content = self._dbt_catalog['nodes'][tbl_node]

                tbl_columns: List[ColumnMetadata] = self._get_column_values(
                    manifest_columns=manifest_content['columns'], catalog_columns=catalog_content['columns']
                )

                desc, desc_src = self._get_table_descriptions(manifest_content)
                tags, tbl_badges = self._get_table_tags_badges(manifest_content)

                tbl_metadata = TableMetadata(
                    database=self._default_sanitize(self._database_name),
                    # The dbt "database" is the cluster here
                    cluster=self._default_sanitize(manifest_content['database']),
                    schema=self._default_sanitize(manifest_content['schema']),
                    name=self._default_sanitize(manifest_content[self._model_name_key]),
                    is_view=catalog_content['metadata']['type'] == 'VIEW',
                    columns=tbl_columns,
                    tags=tags,
                    description=desc,
                    description_source=desc_src
                )
                # Keep track for Lineage
                dbt_id_to_table_key[tbl_node] = tbl_metadata._get_table_key()

                # Optionally filter schemas in the output
                yield_schema = self._can_yield_schema(manifest_content['schema'])

                if self._extract_tables and yield_schema:
                    yield tbl_metadata

                if self._extract_tags and tbl_badges and yield_schema:
                    yield BadgeMetadata(start_label=TableMetadata.TABLE_NODE_LABEL,
                                        start_key=tbl_metadata._get_table_key(),
                                        badges=[Badge(badge, 'table') for badge in tbl_badges])

                if self._source_url and yield_schema:
                    yield TableSource(db_name=tbl_metadata.database,
                                      cluster=tbl_metadata.cluster,
                                      schema=tbl_metadata.schema,
                                      table_name=tbl_metadata.name,
                                      source=os.path.join(self._source_url, manifest_content.get('original_file_path')))

        if self._extract_lineage:
            for upstream, downstreams in self._dbt_manifest['child_map'].items():
                valid_downstreams = [
                    dbt_id_to_table_key[k] for k in downstreams if k.startswith(DBT_MODEL_PREFIX)
                ]
                if valid_downstreams:
                    yield TableLineage(
                        table_key=dbt_id_to_table_key[upstream],
                        downstream_deps=valid_downstreams
                    )

    def _get_column_values(self, manifest_columns: Dict, catalog_columns: Dict) -> List[ColumnMetadata]:
        """
        Iterates over the columns in the manifest file and creates a `ColumnMetadata` object
        with the combined information from the manifest file as well as the catalog file.

        :params manifest_columns: A dictionary of values from the manifest.json, the keys
            are column names and the values are column metadata
        :params catalog_columns: A dictionary of values from the catalog.json, the keys
            are column names and the values are column metadata
        :returns: A list of `ColumnMetadata` in Amundsen.
        """
        tbl_columns = []
        for manifest_col_name, manifest_col_content in manifest_columns.items():
            catalog_col_content = catalog_columns.get(manifest_col_name.upper())

            if catalog_col_content:
                col_desc = None
                if self._extract_descriptions:
                    col_desc = manifest_col_content.get('description')

                # Only extract column-level tags IF converting to badges, Amundsen does not have column-level tags
                badges = None
                if self._extract_tags and self._dbt_tag_as == DBT_TAG_AS.BADGE:
                    badges = manifest_col_content.get('tags')

                col_metadata = ColumnMetadata(
                    name=self._default_sanitize(catalog_col_content['name']),
                    description=col_desc,
                    col_type=catalog_col_content['type'],
                    sort_order=catalog_col_content['index'],
                    badges=badges
                )
                tbl_columns.append(col_metadata)
        return tbl_columns
