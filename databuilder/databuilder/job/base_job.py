# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import abc

from pyhocon import ConfigTree

from databuilder import Scoped
from databuilder.utils.closer import Closer


class Job(Scoped):
    closer = Closer()

    """
    A Databuilder job that represents single work unit.
    """
    @abc.abstractmethod
    def init(self, conf: ConfigTree) -> None:
        pass

    @abc.abstractmethod
    def launch(self) -> None:
        """
        Launch a job
        :return: None
        """
        pass

    def get_scope(self) -> str:
        return 'job'
