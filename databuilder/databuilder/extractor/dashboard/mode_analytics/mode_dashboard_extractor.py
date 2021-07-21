# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import logging
from typing import Any, List

from pyhocon import ConfigFactory, ConfigTree

from databuilder import Scoped
from databuilder.extractor.base_extractor import Extractor
from databuilder.extractor.dashboard.mode_analytics.mode_dashboard_utils import ModeDashboardUtils
from databuilder.rest_api.mode_analytics.mode_paginated_rest_api_query import ModePaginatedRestApiQuery
from databuilder.rest_api.query_merger import QueryMerger
from databuilder.transformer.base_transformer import ChainedTransformer, Transformer
from databuilder.transformer.dict_to_model import MODEL_CLASS, DictToModel
from databuilder.transformer.template_variable_substitution_transformer import (
    FIELD_NAME as VAR_FIELD_NAME, TEMPLATE, TemplateVariableSubstitutionTransformer,
)
from databuilder.transformer.timestamp_string_to_epoch import FIELD_NAME, TimestampStringToEpoch

LOGGER = logging.getLogger(__name__)

# a list of space tokens that we want to skip indexing
DASHBOARD_GROUP_IDS_TO_SKIP = 'dashboard_group_ids_to_skip'


class ModeDashboardExtractor(Extractor):
    """
    A Extractor that extracts core metadata on Mode dashboard. https://app.mode.com/
    It extracts list of reports that consists of:
        Dashboard group name (Space name)
        Dashboard group id (Space token)
        Dashboard group description (Space description)
        Dashboard name (Report name)
        Dashboard id (Report token)
        Dashboard description (Report description)

    Other information such as report run, owner, chart name, query name is in separate extractor.
    """

    def init(self, conf: ConfigTree) -> None:
        self._conf = conf

        self.dashboard_group_ids_to_skip = self._conf.get_list(DASHBOARD_GROUP_IDS_TO_SKIP, [])

        restapi_query = self._build_restapi_query()
        self._extractor = ModeDashboardUtils.create_mode_rest_api_extractor(restapi_query=restapi_query,
                                                                            conf=self._conf)

        # Payload from RestApiQuery has timestamp which is ISO8601. Here we are using TimestampStringToEpoch to
        # transform into epoch and then using DictToModel to convert Dictionary to Model
        transformers: List[Transformer] = []
        timestamp_str_to_epoch_transformer = TimestampStringToEpoch()
        timestamp_str_to_epoch_transformer.init(
            conf=Scoped.get_scoped_conf(self._conf, timestamp_str_to_epoch_transformer.get_scope()).with_fallback(
                ConfigFactory.from_dict({FIELD_NAME: 'created_timestamp', })))

        transformers.append(timestamp_str_to_epoch_transformer)

        dashboard_group_url_transformer = TemplateVariableSubstitutionTransformer()
        dashboard_group_url_transformer.init(
            conf=Scoped.get_scoped_conf(self._conf, dashboard_group_url_transformer.get_scope()).with_fallback(
                ConfigFactory.from_dict({VAR_FIELD_NAME: 'dashboard_group_url',
                                         TEMPLATE: 'https://app.mode.com/{organization}/spaces/{dashboard_group_id}'})))

        transformers.append(dashboard_group_url_transformer)

        dashboard_url_transformer = TemplateVariableSubstitutionTransformer()
        dashboard_url_transformer.init(
            conf=Scoped.get_scoped_conf(self._conf, dashboard_url_transformer.get_scope()).with_fallback(
                ConfigFactory.from_dict({VAR_FIELD_NAME: 'dashboard_url',
                                         TEMPLATE: 'https://app.mode.com/{organization}/reports/{dashboard_id}'})))
        transformers.append(dashboard_url_transformer)

        dict_to_model_transformer = DictToModel()
        dict_to_model_transformer.init(
            conf=Scoped.get_scoped_conf(self._conf, dict_to_model_transformer.get_scope()).with_fallback(
                ConfigFactory.from_dict(
                    {MODEL_CLASS: 'databuilder.models.dashboard.dashboard_metadata.DashboardMetadata'})))
        transformers.append(dict_to_model_transformer)

        self._transformer = ChainedTransformer(transformers=transformers)

    def extract(self) -> Any:
        record = self._extractor.extract()

        # determine whether we want to skip these records
        while record and record.get('dashboard_group_id') in self.dashboard_group_ids_to_skip:
            record = self._extractor.extract()

        if not record:
            return None

        return self._transformer.transform(record=record)

    def get_scope(self) -> str:
        return 'extractor.mode_dashboard'

    def _build_restapi_query(self) -> ModePaginatedRestApiQuery:
        """
        Build REST API Query to get Mode Dashboard metadata
        :return: A RestApiQuery that provides Mode Dashboard metadata
        """
        seed_query = ModeDashboardUtils.get_seed_query(conf=self._conf)
        params = ModeDashboardUtils.get_auth_params(conf=self._conf, discover_auth=True)

        # Reports
        # https://mode.com/developer/discovery-api/analytics/reports/
        url = 'https://app.mode.com/batch/{organization}/reports'
        json_path = 'reports[*].[token, name, description, created_at, space_token]'
        field_names = ['dashboard_id', 'dashboard_name', 'description', 'created_timestamp', 'dashboard_group_id']
        max_record_size = 1000
        pagination_json_path = 'reports[*]'

        spaces_query = ModeDashboardUtils.get_spaces_query_api(conf=self._conf)
        query_merger = QueryMerger(query_to_merge=spaces_query, merge_key='dashboard_group_id')

        reports_query = ModePaginatedRestApiQuery(query_to_join=seed_query, url=url, params=params,
                                                  json_path=json_path, field_names=field_names,
                                                  skip_no_result=True, max_record_size=max_record_size,
                                                  pagination_json_path=pagination_json_path,
                                                  query_merger=query_merger)

        return reports_query
