# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from abc import ABCMeta, abstractmethod
from typing import Set


class Base(metaclass=ABCMeta):
    """
    A base class for ES model
    """

    @abstractmethod
    def get_id(cls) -> str:
        # return a document id in ES
        pass

    @abstractmethod
    def get_attrs(cls) -> Set:
        # return a set of attributes for the class
        pass

    @staticmethod
    @abstractmethod
    def get_type() -> str:
        # return a type string for the class
        pass
