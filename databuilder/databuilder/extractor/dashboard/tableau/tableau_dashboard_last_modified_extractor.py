# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import logging
from typing import (
    Any, Dict, Iterator, List,
)

from pyhocon import ConfigFactory, ConfigTree

import databuilder.extractor.dashboard.tableau.tableau_dashboard_constants as const
from databuilder import Scoped
from databuilder.extractor.base_extractor import Extractor
from databuilder.extractor.dashboard.tableau.tableau_dashboard_utils import (
    TableauDashboardUtils, TableauGraphQLApiExtractor,
)
from databuilder.extractor.restapi.rest_api_extractor import STATIC_RECORD_DICT
from databuilder.transformer.base_transformer import ChainedTransformer, Transformer
from databuilder.transformer.dict_to_model import MODEL_CLASS, DictToModel
from databuilder.transformer.timestamp_string_to_epoch import FIELD_NAME, TimestampStringToEpoch

LOGGER = logging.getLogger(__name__)


class TableauGraphQLApiLastModifiedExtractor(TableauGraphQLApiExtractor):
    """
    Implements the extraction-time logic for parsing the GraphQL result and transforming into a dict
    that fills the DashboardLastModifiedTimestamp model. Allows workbooks to be exlcuded based on their project.
    """

    CLUSTER = const.CLUSTER
    EXCLUDED_PROJECTS = const.EXCLUDED_PROJECTS

    def execute(self) -> Iterator[Dict[str, Any]]:
        response = self.execute_query()

        workbooks_data = [workbook for workbook in response['workbooks']
                          if workbook['projectName'] not in
                          self._conf.get_list(TableauGraphQLApiLastModifiedExtractor.EXCLUDED_PROJECTS, [])]

        for workbook in workbooks_data:
            if None in (workbook['projectName'], workbook['name']):
                LOGGER.warning(f'Ignoring workbook (ID:{workbook["vizportalUrlId"]}) ' +
                               f'in project (ID:{workbook["projectVizportalUrlId"]}) because of a lack of permission')
                continue
            data = {
                'dashboard_group_id': workbook['projectName'],
                'dashboard_id': TableauDashboardUtils.sanitize_workbook_name(workbook['name']),
                'last_modified_timestamp': workbook['updatedAt'],
                'cluster': self._conf.get_string(TableauGraphQLApiLastModifiedExtractor.CLUSTER)
            }
            yield data


class TableauDashboardLastModifiedExtractor(Extractor):
    """
    Extracts metadata about the time of last update for Tableau dashboards.
    For the purposes of this extractor, Tableau "workbooks" are mapped to Amundsen dashboards, and the
    top-level project in which these workbooks preside is the dashboard group. The metadata it gathers is:
        Dashboard last modified timestamp (Workbook last modified timestamp)
    """

    API_BASE_URL = const.API_BASE_URL
    API_VERSION = const.API_VERSION
    CLUSTER = const.CLUSTER
    EXCLUDED_PROJECTS = const.EXCLUDED_PROJECTS
    SITE_NAME = const.SITE_NAME
    TABLEAU_ACCESS_TOKEN_NAME = const.TABLEAU_ACCESS_TOKEN_NAME
    TABLEAU_ACCESS_TOKEN_SECRET = const.TABLEAU_ACCESS_TOKEN_SECRET
    VERIFY_REQUEST = const.VERIFY_REQUEST

    def init(self, conf: ConfigTree) -> None:
        self._conf = conf
        self.query = """query {
            workbooks {
                id
                name
                projectName
                updatedAt
                projectVizportalUrlId
                vizportalUrlId
            }
        }"""

        self._extractor = self._build_extractor()

        transformers: List[Transformer] = []
        timestamp_str_to_epoch_transformer = TimestampStringToEpoch()
        timestamp_str_to_epoch_transformer.init(
            conf=Scoped.get_scoped_conf(self._conf, timestamp_str_to_epoch_transformer.get_scope()).with_fallback(
                ConfigFactory.from_dict({FIELD_NAME: 'last_modified_timestamp', })))
        transformers.append(timestamp_str_to_epoch_transformer)

        dict_to_model_transformer = DictToModel()
        dict_to_model_transformer.init(
            conf=Scoped.get_scoped_conf(self._conf, dict_to_model_transformer.get_scope()).with_fallback(
                ConfigFactory.from_dict(
                    {MODEL_CLASS:
                     'databuilder.models.dashboard.dashboard_last_modified.DashboardLastModifiedTimestamp'})))
        transformers.append(dict_to_model_transformer)

        self._transformer = ChainedTransformer(transformers=transformers)

    def extract(self) -> Any:
        record = self._extractor.extract()
        if not record:
            return None

        return next(self._transformer.transform(record=record), None)

    def get_scope(self) -> str:
        return 'extractor.tableau_dashboard_last_modified'

    def _build_extractor(self) -> TableauGraphQLApiLastModifiedExtractor:
        """
        Builds a TableauGraphQLApiExtractor. All data required can be retrieved with a single GraphQL call.
        :return: A TableauGraphQLApiLastModifiedExtractor that provides dashboard update metadata.
        """
        extractor = TableauGraphQLApiLastModifiedExtractor()
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
