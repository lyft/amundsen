# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import importlib
import logging
from typing import Any, Dict

from pyhocon import ConfigTree

from databuilder.transformer.base_transformer import Transformer

MODEL_CLASS = 'model_class'

LOGGER = logging.getLogger(__name__)


class DictToModel(Transformer):
    """
    Transforms dictionary into model
    """

    def init(self, conf: ConfigTree) -> None:
        model_class = conf.get_string(MODEL_CLASS)
        module_name, class_name = model_class.rsplit(".", 1)
        mod = importlib.import_module(module_name)
        self._model_class = getattr(mod, class_name)

    def transform(self, record: Dict[str, Any]) -> Dict[str, Any]:
        return self._model_class(**record)

    def get_scope(self) -> str:
        return 'transformer.dict_to_model'
