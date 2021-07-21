# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from abc import ABCMeta, abstractmethod


class BaseCallerRetriever(metaclass=ABCMeta):

    @abstractmethod
    def get_caller(self) -> str:
        pass
