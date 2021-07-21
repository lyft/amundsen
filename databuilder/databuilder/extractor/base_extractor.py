# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import abc
from typing import Any

from pyhocon import ConfigTree

from databuilder import Scoped


class Extractor(Scoped):
    """
    An extractor extracts record
    """

    @abc.abstractmethod
    def init(self, conf: ConfigTree) -> None:
        pass

    @abc.abstractmethod
    def extract(self) -> Any:
        """
        :return: Provides a record or None if no more to extract
        """
        return None

    def get_scope(self) -> str:
        return 'extractor'
