# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import importlib
import time
from typing import Any

from pyhocon import ConfigTree

from databuilder.extractor.generic_extractor import GenericExtractor


class EsLastUpdatedExtractor(GenericExtractor):
    """
    Extractor to extract last updated timestamp for Datastore and Es
    """

    def init(self, conf: ConfigTree) -> None:
        """
        Receives a list of dictionaries which is used for extraction
        :param conf:
        :return:
        """
        self.conf = conf

        model_class = conf.get('model_class', None)
        if model_class:
            module_name, class_name = model_class.rsplit(".", 1)
            mod = importlib.import_module(module_name)
            self.model_class = getattr(mod, class_name)
            last_updated_timestamp = int(time.time())
            result = {'timestamp': last_updated_timestamp}
            results = [self.model_class(**result)]
            self._iter = iter(results)
        else:
            raise RuntimeError('model class needs to be provided!')

    def extract(self) -> Any:
        """
        Fetch one sql result row, convert to {model_class} if specified before
        returning.
        :return:
        """
        try:
            result = next(self._iter)
            return result
        except StopIteration:
            return None

    def get_scope(self) -> str:
        return 'extractor.es_last_updated'
