# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import logging
from typing import Any

from pyhocon import ConfigTree

from databuilder.extractor.base_extractor import Extractor
from databuilder.extractor.dashboard.mode_analytics.mode_dashboard_utils import ModeDashboardUtils
from databuilder.rest_api.mode_analytics.mode_paginated_rest_api_query import ModePaginatedRestApiQuery
from databuilder.rest_api.query_merger import QueryMerger

LOGGER = logging.getLogger(__name__)


class ModeDashboardUsageExtractor(Extractor):
    """
    A Extractor that extracts Mode dashboard's accumulated view count
    """

    def init(self, conf: ConfigTree) -> None:
        self._conf = conf

        restapi_query = self._build_restapi_query()
        self._extractor = ModeDashboardUtils.create_mode_rest_api_extractor(restapi_query=restapi_query,
                                                                            conf=self._conf)

    def extract(self) -> Any:
        return self._extractor.extract()

    def get_scope(self) -> str:
        return 'extractor.mode_dashboard_usage'

    def _build_restapi_query(self) -> ModePaginatedRestApiQuery:
        """
        Build REST API Query. To get Mode Dashboard usage, it needs to call three discovery APIs (
        spaces API, reports API and report stats API).
        :return: A RestApiQuery that provides Mode Dashboard metadata
        """

        seed_query = ModeDashboardUtils.get_seed_query(conf=self._conf)
        params = ModeDashboardUtils.get_auth_params(conf=self._conf, discover_auth=True)

        # Reports
        # https://mode.com/developer/discovery-api/analytics/reports/
        reports_url = 'https://app.mode.com/batch/{organization}/reports'
        reports_json_path = 'reports[*].[token, space_token]'
        reports_field_names = ['dashboard_id', 'dashboard_group_id']
        reports_max_record_size = 1000
        reports_pagination_json_path = 'reports[*]'
        spaces_query = ModeDashboardUtils.get_spaces_query_api(conf=self._conf)
        spaces_query_merger = QueryMerger(query_to_merge=spaces_query, merge_key='dashboard_group_id')
        reports_query = ModePaginatedRestApiQuery(query_to_join=seed_query, url=reports_url, params=params,
                                                  json_path=reports_json_path, field_names=reports_field_names,
                                                  skip_no_result=True, max_record_size=reports_max_record_size,
                                                  pagination_json_path=reports_pagination_json_path,
                                                  query_merger=spaces_query_merger)

        # https://mode.com/developer/discovery-api/analytics/report-stats/
        stats_url = 'https://app.mode.com/batch/{organization}/report_stats'
        stats_json_path = 'report_stats[*].[report_token, view_count]'
        stats_field_names = ['dashboard_id', 'accumulated_view_count']
        stats_max_record_size = 1000
        stats_pagination_json_path = 'report_stats[*]'
        reports_query_merger = QueryMerger(query_to_merge=reports_query, merge_key='dashboard_id')
        report_stats_query = ModePaginatedRestApiQuery(query_to_join=seed_query, url=stats_url, params=params,
                                                       json_path=stats_json_path, field_names=stats_field_names,
                                                       skip_no_result=True, max_record_size=stats_max_record_size,
                                                       pagination_json_path=stats_pagination_json_path,
                                                       query_merger=reports_query_merger)

        return report_stats_query
