# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import abc
import logging
from typing import (
    Any, Dict, Iterable, Iterator,
)

LOGGER = logging.getLogger(__name__)


class BaseRestApiQuery(object, metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def execute(self) -> Iterator[Dict[str, Any]]:
        """
        Provides iterator of the records. It uses iterator so that it can stream the result.
        :return:
        """

        return iter([dict()])


class RestApiQuerySeed(BaseRestApiQuery):
    """
    A seed RestApiQuery.

    RestApiQuery is using decorator pattern where it needs to have a seed to begin with. RestApiQuerySeed is for
    RestApiQuery to start with.

    Example: see ModeDashboardExtractor._build_restapi_query
    """

    def __init__(self,
                 seed_record: Iterable[Dict[str, Any]]
                 ) -> None:
        self._seed_record = seed_record

    def execute(self) -> Iterator[Dict[str, Any]]:
        return iter(self._seed_record)


class EmptyRestApiQuerySeed(RestApiQuerySeed):
    """
    Sometimes there simply isn't a record to seed with.
    """

    def __init__(self) -> None:
        super(EmptyRestApiQuerySeed, self).__init__([{'empty_rest_api_query_seed': 1}])
