# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import logging
from typing import Any, Optional

from pyhocon import ConfigTree

from databuilder.loader.base_loader import Loader

LOGGER = logging.getLogger(__name__)

CALLBACK_FUNCTION = 'callback_function'


def log_call_back(record: Optional[Any]) -> None:
    """
    A Sample callback function. Implement any function follows this function's signature to fit your needs.
    :param record:
    :return:
    """
    LOGGER.info('record: %s', record)


class GenericLoader(Loader):
    """
    Loader class to call back a function provided by user
    """

    def init(self, conf: ConfigTree) -> None:
        """
        Initialize file handlers from conf
        :param conf:
        """
        self.conf = conf
        self._callback_func = self.conf.get(CALLBACK_FUNCTION, log_call_back)

    def load(self, record: Optional[Any]) -> None:
        """
        Write record to function
        :param record:
        :return:
        """
        if not record:
            return

        self._callback_func(record)

    def close(self) -> None:
        pass

    def get_scope(self) -> str:
        return "loader.generic"
