# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import abc

from pyhocon import ConfigTree

from databuilder import Scoped


class Task(Scoped):
    """
    A Abstract task that can run an abstract task
    """
    @abc.abstractmethod
    def init(self, conf: ConfigTree) -> None:
        pass

    @abc.abstractmethod
    def run(self) -> None:
        """
        Runs a task
        :return:
        """
        pass

    def get_scope(self) -> str:
        return 'task'
