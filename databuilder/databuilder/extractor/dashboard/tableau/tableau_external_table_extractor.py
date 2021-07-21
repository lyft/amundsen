# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import logging
from typing import (
    Any, Dict, Iterator,
)

from pyhocon import ConfigFactory, ConfigTree

import databuilder.extractor.dashboard.tableau.tableau_dashboard_constants as const
from databuilder import Scoped
from databuilder.extractor.base_extractor import Extractor
from databuilder.extractor.dashboard.tableau.tableau_dashboard_utils import (
    TableauDashboardUtils, TableauGraphQLApiExtractor,
)
from databuilder.transformer.base_transformer import ChainedTransformer
from databuilder.transformer.dict_to_model import MODEL_CLASS, DictToModel

LOGGER = logging.getLogger(__name__)


class TableauGraphQLExternalTableExtractor(TableauGraphQLApiExtractor):
    """
    Implements the extraction-time logic for parsing the GraphQL result and transforming into a dict
    that fills the TableMetadata model.
    """

    EXTERNAL_CLUSTER_NAME = const.EXTERNAL_CLUSTER_NAME
    EXTERNAL_SCHEMA_NAME = const.EXTERNAL_SCHEMA_NAME

    def execute(self) -> Iterator[Dict[str, Any]]:
        response = self.execute_query()

        for table in response['databases']:
            if table['connectionType'] in ['google-sheets', 'salesforce', 'excel-direct']:
                for downstreamTable in table['tables']:
                    data = {
                        'cluster': self._conf.get_string(TableauGraphQLExternalTableExtractor.EXTERNAL_CLUSTER_NAME),
                        'database': TableauDashboardUtils.sanitize_database_name(
                            table['connectionType']
                        ),
                        'schema': TableauDashboardUtils.sanitize_schema_name(table['name']),
                        'name': TableauDashboardUtils.sanitize_table_name(downstreamTable['name']),
                        'description': table['description']
                    }
                    yield data
            else:
                data = {
                    'cluster': self._conf.get_string(TableauGraphQLExternalTableExtractor.EXTERNAL_CLUSTER_NAME),
                    'database': TableauDashboardUtils.sanitize_database_name(table['connectionType']),
                    'schema': self._conf.get_string(TableauGraphQLExternalTableExtractor.EXTERNAL_SCHEMA_NAME),
                    'name': TableauDashboardUtils.sanitize_table_name(table['name']),
                    'description': table['description']
                }
                yield data


class TableauDashboardExternalTableExtractor(Extractor):
    """
    Creates the "external" Tableau tables.
    In this context, "external" tables are "tables" that are not from a typical database, and are loaded
    using some other data format, like CSV files.
    This extractor has been tested with the following types of external tables:
        Excel spreadsheets
        Text files (including CSV files)
        Salesforce connections
        Google Sheets connections

    Excel spreadsheets, Salesforce connections, and Google Sheets connections are all classified as
    "databases" in terms of Tableau's Metadata API, with their "subsheets" forming their "tables" when
    present. However, these tables are not assigned a schema, this extractor chooses to use the name
    parent sheet as the schema, and assign a new table to each subsheet. The connection type is
    always used as the database, and for text files, the schema is set using the EXTERNAL_SCHEMA_NAME
    config option. Since these external tables are usually named for human consumption only and often
    contain a wider range of characters, all inputs are transformed to remove any problematic
    occurences before they are inserted: see the sanitize methods TableauDashboardUtils for specifics.

    A more concrete example: if one had a Google Sheet titled "Growth by Region & County" with 2 subsheets called
    "FY19 Report" and "FY20 Report", two tables would be generated with the following keys:
    googlesheets://external.growth_by_region_county/FY_19_Report
    googlesheets://external.growth_by_region_county/FY_20_Report
    """

    API_BASE_URL = const.API_BASE_URL
    API_VERSION = const.API_VERSION
    CLUSTER = const.CLUSTER
    EXCLUDED_PROJECTS = const.EXCLUDED_PROJECTS
    EXTERNAL_CLUSTER_NAME = const.EXTERNAL_CLUSTER_NAME
    EXTERNAL_SCHEMA_NAME = const.EXTERNAL_SCHEMA_NAME
    EXTERNAL_TABLE_TYPES = const.EXTERNAL_TABLE_TYPES
    SITE_NAME = const.SITE_NAME
    TABLEAU_ACCESS_TOKEN_NAME = const.TABLEAU_ACCESS_TOKEN_NAME
    TABLEAU_ACCESS_TOKEN_SECRET = const.TABLEAU_ACCESS_TOKEN_SECRET
    VERIFY_REQUEST = const.VERIFY_REQUEST

    def init(self, conf: ConfigTree) -> None:
        self._conf = conf
        self.query = """query externalTables($externalTableTypes: [String]) {
          databases (filter: {connectionTypeWithin: $externalTableTypes}) {
            name
            connectionType
            description
            tables {
                name
            }
          }
        }"""
        self.query_variables = {
            'externalTableTypes': self._conf.get_list(TableauDashboardExternalTableExtractor.EXTERNAL_TABLE_TYPES)}
        self._extractor = self._build_extractor()

        transformers = []
        dict_to_model_transformer = DictToModel()
        dict_to_model_transformer.init(
            conf=Scoped.get_scoped_conf(self._conf, dict_to_model_transformer.get_scope()).with_fallback(
                ConfigFactory.from_dict(
                    {MODEL_CLASS: 'databuilder.models.table_metadata.TableMetadata'})))
        transformers.append(dict_to_model_transformer)
        self._transformer = ChainedTransformer(transformers=transformers)

    def extract(self) -> Any:
        record = self._extractor.extract()
        if not record:
            return None

        return self._transformer.transform(record=record)

    def get_scope(self) -> str:
        return 'extractor.tableau_external_table'

    def _build_extractor(self) -> TableauGraphQLExternalTableExtractor:
        """
        Builds a TableauGraphQLExternalTableExtractor. All data required can be retrieved with a single GraphQL call.
        :return: A TableauGraphQLExternalTableExtractor that creates external table metadata entities.
        """
        extractor = TableauGraphQLExternalTableExtractor()

        config_dict = {
            TableauGraphQLApiExtractor.QUERY_VARIABLES: self.query_variables,
            TableauGraphQLApiExtractor.QUERY: self.query}
        tableau_extractor_conf = \
            Scoped.get_scoped_conf(self._conf, extractor.get_scope())\
                  .with_fallback(self._conf)\
                  .with_fallback(ConfigFactory.from_dict(config_dict))
        extractor.init(conf=tableau_extractor_conf)
        return extractor
