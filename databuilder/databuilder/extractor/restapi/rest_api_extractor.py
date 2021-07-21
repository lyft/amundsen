# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import importlib
import logging
from typing import (
    Any, Dict, Iterator, Optional,
)

from pyhocon import ConfigTree

from databuilder.extractor.base_extractor import Extractor
from databuilder.rest_api.base_rest_api_query import BaseRestApiQuery

REST_API_QUERY = 'restapi_query'
MODEL_CLASS = 'model_class'

# Static record that will be added into extracted record
# For example, DashboardMetadata requires product name (static name) of Dashboard and REST api does not provide
#  it. and you can add {'product': 'mode'} so that it will be included in the record.
STATIC_RECORD_DICT = 'static_record_dict'

LOGGER = logging.getLogger(__name__)


class RestAPIExtractor(Extractor):
    """
    An Extractor that calls one or more REST API to extract the data.
    This extractor almost entirely depends on RestApiQuery.
    """

    def init(self, conf: ConfigTree) -> None:

        self._restapi_query: BaseRestApiQuery = conf.get(REST_API_QUERY)
        self._iterator: Optional[Iterator[Dict[str, Any]]] = None
        self._static_dict = conf.get(STATIC_RECORD_DICT, dict())
        LOGGER.info('static record: %s', self._static_dict)

        model_class = conf.get(MODEL_CLASS, None)
        if model_class:
            module_name, class_name = model_class.rsplit(".", 1)
            mod = importlib.import_module(module_name)
            self.model_class = getattr(mod, class_name)

    def extract(self) -> Any:
        """
        Fetch one result row from RestApiQuery, convert to {model_class} if specified before
        returning.
        :return:
        """

        if not self._iterator:
            self._iterator = self._restapi_query.execute()

        try:
            record = next(self._iterator)
        except StopIteration:
            return None

        if self._static_dict:
            record.update(self._static_dict)

        if hasattr(self, 'model_class'):
            return self.model_class(**record)

        return record

    def get_scope(self) -> str:

        return 'extractor.restapi'
