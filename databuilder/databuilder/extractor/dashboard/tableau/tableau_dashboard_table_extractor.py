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
from databuilder.extractor.restapi.rest_api_extractor import STATIC_RECORD_DICT
from databuilder.models.table_metadata import TableMetadata
from databuilder.transformer.base_transformer import ChainedTransformer
from databuilder.transformer.dict_to_model import MODEL_CLASS, DictToModel

LOGGER = logging.getLogger(__name__)


class TableauGraphQLDashboardTableExtractor(TableauGraphQLApiExtractor):
    """
    Implements the extraction-time logic for parsing the GraphQL result and transforming into a dict
    that fills the DashboardTable model. Allows workbooks to be exlcuded based on their project.
    """

    CLUSTER = const.CLUSTER
    DATABASE = const.DATABASE
    EXCLUDED_PROJECTS = const.EXCLUDED_PROJECTS
    EXTERNAL_CLUSTER_NAME = const.EXTERNAL_CLUSTER_NAME

    def execute(self) -> Iterator[Dict[str, Any]]:
        response = self.execute_query()

        workbooks_data = [workbook for workbook in response['workbooks']
                          if workbook['projectName'] not in
                          self._conf.get_list(TableauGraphQLDashboardTableExtractor.EXCLUDED_PROJECTS, [])]

        for workbook in workbooks_data:
            data = {
                'dashboard_group_id': workbook['projectName'],
                'dashboard_id': TableauDashboardUtils.sanitize_workbook_name(workbook['name']),
                'cluster': self._conf.get_string(TableauGraphQLDashboardTableExtractor.CLUSTER),
                'table_ids': []
            }

            for table in workbook['upstreamTables']:

                # external tables have no schema, so they must be parsed differently
                # see TableauExternalTableExtractor for more specifics
                if table['schema'] != '':
                    cluster = self._conf.get_string(TableauGraphQLDashboardTableExtractor.CLUSTER)
                    database = self._conf.get_string(TableauGraphQLDashboardTableExtractor.DATABASE)

                    # Tableau sometimes incorrectly assigns the "schema" value
                    # based on how the datasource connection is used in a workbook.
                    # It will hide the real schema inside the table name, like "real_schema.real_table",
                    # and set the "schema" value to "wrong_schema". In every case discovered so far, the schema
                    # key is incorrect, so the "inner" schema from the table name is used instead.
                    if '.' in table['name']:
                        schema, name = table['name'].split('.')
                    else:
                        schema, name = table['schema'], table['name']
                    schema = TableauDashboardUtils.sanitize_schema_name(schema)
                    name = TableauDashboardUtils.sanitize_table_name(name)
                else:
                    cluster = self._conf.get_string(TableauGraphQLDashboardTableExtractor.EXTERNAL_CLUSTER_NAME)
                    database = TableauDashboardUtils.sanitize_database_name(
                        table['database']['connectionType']
                    )
                    schema = TableauDashboardUtils.sanitize_schema_name(table['database']['name'])
                    name = TableauDashboardUtils.sanitize_table_name(table['name'])

                table_id = TableMetadata.TABLE_KEY_FORMAT.format(
                    db=database,
                    cluster=cluster,
                    schema=schema,
                    tbl=name,
                )
                data['table_ids'].append(table_id)

            yield data


class TableauDashboardTableExtractor(Extractor):
    """
    Extracts metadata about the tables associated with Tableau workbooks.
    It can handle both "regular" database tables as well as "external" tables
    (see TableauExternalTableExtractor for more info on external tables).
    Assumes that all the nodes for both the dashboards and the tables have already been created.
    """

    API_BASE_URL = const.API_BASE_URL
    API_VERSION = const.API_VERSION
    CLUSTER = const.CLUSTER
    DATABASE = const.DATABASE
    EXCLUDED_PROJECTS = const.EXCLUDED_PROJECTS
    EXTERNAL_CLUSTER_NAME = const.EXTERNAL_CLUSTER_NAME
    SITE_NAME = const.SITE_NAME
    TABLEAU_ACCESS_TOKEN_NAME = const.TABLEAU_ACCESS_TOKEN_NAME
    TABLEAU_ACCESS_TOKEN_SECRET = const.TABLEAU_ACCESS_TOKEN_SECRET
    VERIFY_REQUEST = const.VERIFY_REQUEST

    def init(self, conf: ConfigTree) -> None:
        self._conf = conf
        self.query = """query {
          workbooks {
            name
            projectName
            upstreamTables {
              name
              schema
              database {
                name
                connectionType
              }
            }
          }
        }"""
        self._extractor = self._build_extractor()

        transformers = []
        dict_to_model_transformer = DictToModel()
        dict_to_model_transformer.init(
            conf=Scoped.get_scoped_conf(self._conf, dict_to_model_transformer.get_scope()).with_fallback(
                ConfigFactory.from_dict(
                    {MODEL_CLASS: 'databuilder.models.dashboard.dashboard_table.DashboardTable'})))
        transformers.append(dict_to_model_transformer)
        self._transformer = ChainedTransformer(transformers=transformers)

    def extract(self) -> Any:
        record = self._extractor.extract()
        if not record:
            return None

        return next(self._transformer.transform(record=record), None)

    def get_scope(self) -> str:
        return 'extractor.tableau_dashboard_table'

    def _build_extractor(self) -> TableauGraphQLDashboardTableExtractor:
        """
        Builds a TableauGraphQLDashboardTableExtractor. All data required can be retrieved with a single GraphQL call.
        :return: A TableauGraphQLDashboardTableExtractor that creates dashboard <> table relationships.
        """
        extractor = TableauGraphQLDashboardTableExtractor()
        tableau_extractor_conf = \
            Scoped.get_scoped_conf(self._conf, extractor.get_scope())\
                  .with_fallback(self._conf)\
                  .with_fallback(ConfigFactory.from_dict({TableauGraphQLApiExtractor.QUERY: self.query,
                                                          STATIC_RECORD_DICT: {'product': 'tableau'}
                                                          }
                                                         )
                                 )
        extractor.init(conf=tableau_extractor_conf)
        return extractor
