# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import logging
from typing import Any

from pyhocon import ConfigTree

from databuilder.transformer.base_transformer import Transformer

LOGGER = logging.getLogger(__name__)


# Config keys
REGEX_REPLACE_TUPLE_LIST = 'regex_replace_tuple_list'
ATTRIBUTE_NAME = 'attribute_name'


class RegexStrReplaceTransformer(Transformer):
    """
    Generic string replacement transformer using REGEX.
    User can pass list of tuples where tuple contains regex and replacement pair.

    Any non-string values will be ignored.
    """

    def init(self, conf: ConfigTree) -> None:
        self._regex_replace_tuples = conf.get_list(REGEX_REPLACE_TUPLE_LIST)
        self._attribute_name = conf.get_string(ATTRIBUTE_NAME)

    def transform(self, record: Any) -> Any:

        if isinstance(record, dict):
            val = record.get(self._attribute_name)
        else:
            val = getattr(record, self._attribute_name)

        if val is None or not isinstance(val, str):
            return record

        for regex_replace_tuple in self._regex_replace_tuples:
            val = val.replace(regex_replace_tuple[0], regex_replace_tuple[1])

        if isinstance(record, dict):
            record[self._attribute_name] = val
        else:
            setattr(record, self._attribute_name, val)

        return record

    def get_scope(self) -> str:
        return 'transformer.regex_str_replace'
