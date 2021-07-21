# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import logging
from typing import Any, List

from pyhocon import ConfigFactory, ConfigTree

from databuilder import Scoped
from databuilder.extractor.base_extractor import Extractor
from databuilder.extractor.dashboard.mode_analytics.mode_dashboard_utils import ModeDashboardUtils
from databuilder.rest_api.mode_analytics.mode_paginated_rest_api_query import ModePaginatedRestApiQuery
from databuilder.transformer.base_transformer import ChainedTransformer, Transformer
from databuilder.transformer.dict_to_model import MODEL_CLASS, DictToModel
from databuilder.transformer.regex_str_replace_transformer import (
    ATTRIBUTE_NAME, REGEX_REPLACE_TUPLE_LIST, RegexStrReplaceTransformer,
)
from databuilder.transformer.template_variable_substitution_transformer import (
    FIELD_NAME, TEMPLATE, TemplateVariableSubstitutionTransformer,
)

LOGGER = logging.getLogger(__name__)


class ModeDashboardQueriesExtractor(Extractor):
    """
    A Extractor that extracts Query information

    """

    def init(self, conf: ConfigTree) -> None:
        self._conf = conf

        restapi_query = self._build_restapi_query()
        self._extractor = ModeDashboardUtils.create_mode_rest_api_extractor(
            restapi_query=restapi_query,
            conf=self._conf
        )

        # Constructing URL using several ID via TemplateVariableSubstitutionTransformer
        transformers: List[Transformer] = []
        variable_substitution_transformer = TemplateVariableSubstitutionTransformer()
        variable_substitution_transformer.init(
            conf=Scoped.get_scoped_conf(self._conf,
                                        variable_substitution_transformer.get_scope()).with_fallback(
                ConfigFactory.from_dict({FIELD_NAME: 'url',
                                         TEMPLATE: 'https://app.mode.com/{organization}'
                                                   '/reports/{dashboard_id}/queries/{query_id}'})))

        transformers.append(variable_substitution_transformer)

        # Escape backslash as it breaks Cypher statement.
        replace_transformer = RegexStrReplaceTransformer()
        replace_transformer.init(
            conf=Scoped.get_scoped_conf(self._conf, replace_transformer.get_scope()).with_fallback(
                ConfigFactory.from_dict(
                    {REGEX_REPLACE_TUPLE_LIST: [('\\', '\\\\')], ATTRIBUTE_NAME: 'query_text'})))
        transformers.append(replace_transformer)

        dict_to_model_transformer = DictToModel()
        dict_to_model_transformer.init(
            conf=Scoped.get_scoped_conf(self._conf, dict_to_model_transformer.get_scope()).with_fallback(
                ConfigFactory.from_dict(
                    {MODEL_CLASS: 'databuilder.models.dashboard.dashboard_query.DashboardQuery'})))
        transformers.append(dict_to_model_transformer)

        self._transformer = ChainedTransformer(transformers=transformers)

    def extract(self) -> Any:
        record = self._extractor.extract()
        if not record:
            return None

        return self._transformer.transform(record=record)

    def get_scope(self) -> str:
        return 'extractor.mode_dashboard_query'

    def _build_restapi_query(self) -> ModePaginatedRestApiQuery:
        """
        Build REST API Query to get Mode Dashboard queries
        :return: A RestApiQuery that provides Mode Dashboard execution (run)
        """

        seed_query = ModeDashboardUtils.get_seed_query(conf=self._conf)
        params = ModeDashboardUtils.get_auth_params(conf=self._conf, discover_auth=True)

        # Queries
        # https://mode.com/developer/discovery-api/analytics/queries/
        url = 'https://app.mode.com/batch/{organization}/queries'
        json_path = 'queries[*].[report_token, space_token, token, name, raw_query]'
        field_names = ['dashboard_id', 'dashboard_group_id', 'query_id', 'query_name', 'query_text']
        max_record_size = 1000
        pagination_json_path = 'queries[*]'
        query_names_query = ModePaginatedRestApiQuery(query_to_join=seed_query, url=url, params=params,
                                                      json_path=json_path, field_names=field_names,
                                                      skip_no_result=True, max_record_size=max_record_size,
                                                      pagination_json_path=pagination_json_path)

        return query_names_query
