# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from abc import ABCMeta, abstractmethod
from typing import (
    Any, Dict, List, Union,
)

from amundsen_common.models.api.health_check import HealthCheck

from search_service.models.dashboard import SearchDashboardResult
from search_service.models.feature import SearchFeatureResult
from search_service.models.table import SearchTableResult
from search_service.models.user import SearchUserResult


class BaseProxy(metaclass=ABCMeta):
    """
    Base Proxy, which behaves like an interface for all
    the proxy clients available in the amundsen search service
    """

    def health(self) -> HealthCheck:
        """
        Runs one or more series of checks on the service. Can also
        optionally return additional metadata about each check (e.g.
        latency to database, cpu utilization, etc.).
        """
        return HealthCheck(status='ok', checks={f'{type(self).__name__}:connection': {'status': 'not checked'}})

    @abstractmethod
    def fetch_table_search_results(self, *,
                                   query_term: str,
                                   page_index: int = 0,
                                   index: str = '') -> SearchTableResult:
        pass

    @abstractmethod
    def fetch_dashboard_search_results(self, *,
                                       query_term: str,
                                       page_index: int = 0,
                                       index: str = '') -> SearchDashboardResult:
        pass

    @abstractmethod
    def fetch_feature_search_results(self, *,
                                     query_term: str,
                                     page_index: int = 0,
                                     index: str = '') -> SearchFeatureResult:
        pass

    @abstractmethod
    def fetch_user_search_results(self, *,
                                  query_term: str,
                                  page_index: int = 0,
                                  index: str = '') -> SearchUserResult:
        pass

    @abstractmethod
    def fetch_search_results_with_filter(self, *,
                                         query_term: str,
                                         search_request: dict,
                                         page_index: int = 0,
                                         index: str = '') -> Union[SearchTableResult,
                                                                   SearchDashboardResult,
                                                                   SearchFeatureResult]:
        pass

    @abstractmethod
    def update_document(self, *,
                        data: List[Dict[str, Any]],
                        index: str = '') -> str:
        pass

    @abstractmethod
    def create_document(self, *,
                        data: List[Dict[str, Any]],
                        index: str = '') -> str:
        pass

    @abstractmethod
    def delete_document(self, *,
                        data: List[str],
                        index: str = '') -> str:
        pass
