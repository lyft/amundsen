# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import abc
from typing import Any

from pyhocon import ConfigTree

from databuilder import Scoped


class Loader(Scoped):
    """
    A loader loads to the destination or to the staging area
    """
    @abc.abstractmethod
    def init(self, conf: ConfigTree) -> None:
        pass

    @abc.abstractmethod
    def load(self, record: Any) -> None:
        pass

    def get_scope(self) -> str:
        return 'loader'
