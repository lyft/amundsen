# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import logging
from typing import Any, Dict

from pyhocon import ConfigTree

from databuilder.transformer.base_transformer import Transformer

CALLBACK_FUNCTION = 'callback_function'
FIELD_NAME = 'field_name'

LOGGER = logging.getLogger(__name__)


class GenericTransformer(Transformer):
    """
    A generic transformer that accepts a callback function that transforms the record on specified field.
    """

    def init(self, conf: ConfigTree) -> None:
        self._callback_function = conf.get(CALLBACK_FUNCTION)
        self._field_name = conf.get_string(FIELD_NAME)

    def transform(self, record: Dict[str, Any]) -> Dict[str, Any]:

        for k, v in record.items():
            if k == self._field_name:
                new_val = self._callback_function(v)
                record[k] = new_val
        return record

    def get_scope(self) -> str:
        return 'transformer.generic'
