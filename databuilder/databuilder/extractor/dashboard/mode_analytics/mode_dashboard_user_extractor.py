# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import logging
from typing import Any, List

from pyhocon import ConfigFactory, ConfigTree
from requests.auth import HTTPBasicAuth

from databuilder import Scoped
from databuilder.extractor.base_extractor import Extractor
from databuilder.extractor.dashboard.mode_analytics.mode_dashboard_constants import (
    MODE_ACCESS_TOKEN, MODE_PASSWORD_TOKEN, ORGANIZATION,
)
from databuilder.extractor.dashboard.mode_analytics.mode_dashboard_utils import ModeDashboardUtils
from databuilder.rest_api.base_rest_api_query import RestApiQuerySeed
from databuilder.rest_api.rest_api_failure_handlers import HttpFailureSkipOnStatus
from databuilder.rest_api.rest_api_query import RestApiQuery
from databuilder.transformer.base_transformer import ChainedTransformer, Transformer
from databuilder.transformer.dict_to_model import MODEL_CLASS, DictToModel
from databuilder.transformer.remove_field_transformer import FIELD_NAMES, RemoveFieldTransformer

LOGGER = logging.getLogger(__name__)


class ModeDashboardUserExtractor(Extractor):
    """
    An Extractor that extracts all Mode Dashboard user and add mode_user_id attribute to User model.
    """

    def init(self, conf: ConfigTree) -> None:
        self._conf = conf

        restapi_query = self._build_restapi_query()
        self._extractor = ModeDashboardUtils.create_mode_rest_api_extractor(
            restapi_query=restapi_query,
            conf=self._conf
        )

        # Remove all unnecessary fields because User model accepts all attributes and push it to Neo4j.
        transformers: List[Transformer] = []

        remove_fields_transformer = RemoveFieldTransformer()
        remove_fields_transformer.init(
            conf=Scoped.get_scoped_conf(self._conf, remove_fields_transformer.get_scope()).with_fallback(
                ConfigFactory.from_dict(
                    {FIELD_NAMES: ['organization', 'mode_user_resource_path', 'product']})))
        transformers.append(remove_fields_transformer)

        dict_to_model_transformer = DictToModel()
        dict_to_model_transformer.init(
            conf=Scoped.get_scoped_conf(self._conf, dict_to_model_transformer.get_scope()).with_fallback(
                ConfigFactory.from_dict(
                    {MODEL_CLASS: 'databuilder.models.user.User'})))
        transformers.append(dict_to_model_transformer)

        self._transformer = ChainedTransformer(transformers=transformers)

    def extract(self) -> Any:
        record = self._extractor.extract()
        if not record:
            return None

        return self._transformer.transform(record=record)

    def get_scope(self) -> str:
        return 'extractor.mode_dashboard_owner'

    def _build_restapi_query(self) -> RestApiQuery:
        """
        Build REST API Query. To get Mode Dashboard owner, it needs to call three APIs (spaces API, reports
        API, and user API) joining together.
        :return: A RestApiQuery that provides Mode Dashboard owner
        """

        # Seed query record for next query api to join with
        seed_record = [{
            'organization': self._conf.get_string(ORGANIZATION),
            'is_active': None,
            'updated_at': None,
            'do_not_update_empty_attribute': True,
        }]
        seed_query = RestApiQuerySeed(seed_record=seed_record)

        # memberships
        # https://mode.com/developer/api-reference/management/organization-memberships/#listMemberships
        memberships_url_template = 'https://app.mode.com/api/{organization}/memberships'
        params = {'auth': HTTPBasicAuth(self._conf.get_string(MODE_ACCESS_TOKEN),
                                        self._conf.get_string(MODE_PASSWORD_TOKEN))}

        json_path = '(_embedded.memberships[*].member_username) | (_embedded.memberships[*]._links.user.href)'
        field_names = ['mode_user_id', 'mode_user_resource_path']
        mode_user_ids_query = RestApiQuery(query_to_join=seed_query, url=memberships_url_template, params=params,
                                           json_path=json_path, field_names=field_names,
                                           skip_no_result=True, json_path_contains_or=True)

        # https://mode.com/developer/api-reference/management/users/
        user_url_template = 'https://app.mode.com{mode_user_resource_path}'

        json_path = 'email'
        field_names = ['email']
        failure_handler = HttpFailureSkipOnStatus(status_codes_to_skip={404})
        mode_user_email_query = RestApiQuery(query_to_join=mode_user_ids_query, url=user_url_template,
                                             params=params, json_path=json_path, field_names=field_names,
                                             skip_no_result=True, can_skip_failure=failure_handler.can_skip_failure)

        return mode_user_email_query
