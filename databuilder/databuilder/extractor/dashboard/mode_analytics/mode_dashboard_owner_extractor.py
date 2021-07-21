# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import logging
from typing import Any

from pyhocon import ConfigFactory, ConfigTree

from databuilder.extractor.base_extractor import Extractor
from databuilder.extractor.dashboard.mode_analytics.mode_dashboard_utils import ModeDashboardUtils
from databuilder.extractor.restapi.rest_api_extractor import MODEL_CLASS
from databuilder.rest_api.mode_analytics.mode_paginated_rest_api_query import ModePaginatedRestApiQuery

LOGGER = logging.getLogger(__name__)


class ModeDashboardOwnerExtractor(Extractor):
    """
    An Extractor that extracts Dashboard owner.

    """

    def init(self, conf: ConfigTree) -> None:
        self._conf = conf

        restapi_query = self._build_restapi_query()
        self._extractor = ModeDashboardUtils.create_mode_rest_api_extractor(
            restapi_query=restapi_query,
            conf=self._conf.with_fallback(
                ConfigFactory.from_dict(
                    {MODEL_CLASS: 'databuilder.models.dashboard.dashboard_owner.DashboardOwner', }
                )
            )
        )

    def extract(self) -> Any:
        return self._extractor.extract()

    def get_scope(self) -> str:
        return 'extractor.mode_dashboard_owner'

    def _build_restapi_query(self) -> ModePaginatedRestApiQuery:
        """
        Build REST API Query to get Mode Dashboard owner
        :return: A RestApiQuery that provides Mode Dashboard owner
        """

        seed_query = ModeDashboardUtils.get_seed_query(conf=self._conf)
        params = ModeDashboardUtils.get_auth_params(conf=self._conf, discover_auth=True)

        # Reports
        # https://mode.com/developer/discovery-api/analytics/reports/
        url = 'https://app.mode.com/batch/{organization}/reports'
        json_path = 'reports[*].[token, space_token, creator_email]'
        field_names = ['dashboard_id', 'dashboard_group_id', 'email']
        max_record_size = 1000
        pagination_json_path = 'reports[*]'
        creator_query = ModePaginatedRestApiQuery(query_to_join=seed_query, url=url, params=params,
                                                  json_path=json_path, field_names=field_names,
                                                  skip_no_result=True, max_record_size=max_record_size,
                                                  pagination_json_path=pagination_json_path)

        return creator_query
