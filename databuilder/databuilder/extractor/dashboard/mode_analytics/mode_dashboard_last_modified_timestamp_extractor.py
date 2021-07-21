# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import logging

from pyhocon import ConfigFactory, ConfigTree

from databuilder.extractor.dashboard.mode_analytics.mode_dashboard_executions_extractor import (
    ModeDashboardExecutionsExtractor,
)
from databuilder.extractor.dashboard.mode_analytics.mode_dashboard_utils import ModeDashboardUtils
from databuilder.extractor.restapi.rest_api_extractor import STATIC_RECORD_DICT
from databuilder.rest_api.mode_analytics.mode_paginated_rest_api_query import ModePaginatedRestApiQuery
from databuilder.transformer.dict_to_model import MODEL_CLASS, DictToModel
from databuilder.transformer.timestamp_string_to_epoch import FIELD_NAME, TimestampStringToEpoch

LOGGER = logging.getLogger(__name__)


class ModeDashboardLastModifiedTimestampExtractor(ModeDashboardExecutionsExtractor):
    """
    A Extractor that extracts Mode dashboard's last modified timestamp.

    """

    def __init__(self) -> None:
        super(ModeDashboardLastModifiedTimestampExtractor, self).__init__()

    def init(self, conf: ConfigTree) -> None:
        conf = conf.with_fallback(
            ConfigFactory.from_dict({
                STATIC_RECORD_DICT: {'product': 'mode'},
                f'{DictToModel().get_scope()}.{MODEL_CLASS}':
                    'databuilder.models.dashboard.dashboard_last_modified.DashboardLastModifiedTimestamp',
                f'{TimestampStringToEpoch().get_scope()}.{FIELD_NAME}':
                    'last_modified_timestamp'
            })
        )
        super(ModeDashboardLastModifiedTimestampExtractor, self).init(conf)

    def get_scope(self) -> str:
        return 'extractor.mode_dashboard_last_modified_timestamp_execution'

    def _build_restapi_query(self) -> ModePaginatedRestApiQuery:
        """
        Build REST API Query to get Mode Dashboard last modified timestamp
        :return: A RestApiQuery that provides Mode Dashboard last successful execution (run)
        """

        seed_query = ModeDashboardUtils.get_seed_query(conf=self._conf)
        params = ModeDashboardUtils.get_auth_params(conf=self._conf, discover_auth=True)

        # Reports
        # https://mode.com/developer/discovery-api/analytics/reports/
        url = 'https://app.mode.com/batch/{organization}/reports'
        json_path = 'reports[*].[token, space_token, edited_at]'
        field_names = ['dashboard_id', 'dashboard_group_id', 'last_modified_timestamp']
        max_record_size = 1000
        pagination_json_path = 'reports[*]'
        last_modified_query = ModePaginatedRestApiQuery(query_to_join=seed_query, url=url, params=params,
                                                        json_path=json_path, field_names=field_names,
                                                        skip_no_result=True, max_record_size=max_record_size,
                                                        pagination_json_path=pagination_json_path)

        return last_modified_query
