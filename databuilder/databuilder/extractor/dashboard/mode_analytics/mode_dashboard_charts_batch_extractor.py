# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import logging
from typing import Any

from pyhocon import ConfigFactory, ConfigTree

from databuilder import Scoped
from databuilder.extractor.base_extractor import Extractor
from databuilder.extractor.dashboard.mode_analytics.mode_dashboard_constants import ORGANIZATION
from databuilder.extractor.dashboard.mode_analytics.mode_dashboard_utils import ModeDashboardUtils
from databuilder.rest_api.base_rest_api_query import RestApiQuerySeed
from databuilder.rest_api.mode_analytics.mode_paginated_rest_api_query import ModePaginatedRestApiQuery
from databuilder.rest_api.rest_api_query import RestApiQuery
from databuilder.transformer.dict_to_model import MODEL_CLASS, DictToModel

LOGGER = logging.getLogger(__name__)


class ModeDashboardChartsBatchExtractor(Extractor):
    """
    Mode dashboard chart extractor leveraging batch / discovery endpoint.
    The detail could be found in https://mode.com/help/articles/discovery-api/#list-charts-for-an-organization
    """
    # config to include the charts from all space
    INCLUDE_ALL_SPACE = 'include_all_space'

    def init(self, conf: ConfigTree) -> None:
        self._conf = conf
        restapi_query = self._build_restapi_query()
        self._extractor = ModeDashboardUtils.create_mode_rest_api_extractor(
            restapi_query=restapi_query,
            conf=self._conf
        )

        dict_to_model_transformer = DictToModel()
        dict_to_model_transformer.init(
            conf=Scoped.get_scoped_conf(self._conf, dict_to_model_transformer.get_scope()).with_fallback(
                ConfigFactory.from_dict(
                    {MODEL_CLASS: 'databuilder.models.dashboard.dashboard_chart.DashboardChart'})))
        self._transformer = dict_to_model_transformer

    def extract(self) -> Any:

        record = self._extractor.extract()
        if not record:
            return None
        return self._transformer.transform(record=record)

    def get_scope(self) -> str:
        return 'extractor.mode_dashboard_chart_batch'

    def _build_restapi_query(self) -> RestApiQuery:
        """
        Build a paginated REST API based on Mode discovery API
        :return:
        """
        params = ModeDashboardUtils.get_auth_params(conf=self._conf, discover_auth=True)

        seed_record = [{
            'organization': self._conf.get_string(ORGANIZATION),
            'is_active': None,
            'updated_at': None,
            'do_not_update_empty_attribute': True,
        }]
        seed_query = RestApiQuerySeed(seed_record=seed_record)

        chart_url_template = 'http://app.mode.com/batch/{organization}/charts'
        if self._conf.get_bool(ModeDashboardChartsBatchExtractor.INCLUDE_ALL_SPACE, default=False):
            chart_url_template += '?include_spaces=all'
        json_path = '(charts[*].[space_token,report_token,query_token,token,chart_title,chart_type])'
        field_names = ['dashboard_group_id',
                       'dashboard_id',
                       'query_id',
                       'chart_id',
                       'chart_name',
                       'chart_type']
        max_record_size = 1000
        chart_batch_query = ModePaginatedRestApiQuery(query_to_join=seed_query,
                                                      url=chart_url_template,
                                                      params=params,
                                                      json_path=json_path,
                                                      pagination_json_path=json_path,
                                                      field_names=field_names,
                                                      skip_no_result=True,
                                                      max_record_size=max_record_size)
        return chart_batch_query
