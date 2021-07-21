# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import logging
from typing import Any, Dict

from pyhocon import ConfigTree

from databuilder.transformer.base_transformer import Transformer

FIELD_NAMES = 'field_names'  # field name to be removed

LOGGER = logging.getLogger(__name__)


class RemoveFieldTransformer(Transformer):
    """
    Remove field in Dict by specifying list of fields (keys).

    """

    def init(self, conf: ConfigTree) -> None:
        self._field_names = conf.get_list(FIELD_NAMES)

    def transform(self, record: Dict[str, Any]) -> Dict[str, Any]:

        for k in self._field_names:
            if k in record:
                del record[k]

        return record

    def get_scope(self) -> str:
        return 'transformer.remove_field'
