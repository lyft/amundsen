# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import abc
from typing import Union

from amundsen_rds.models import RDSModel


class TableSerializable(object, metaclass=abc.ABCMeta):
    """
    A Serializable abstract class asks subclass to implement next record
    in rds model instance form so that it can be serialized to CSV file.

    Any model class that needs to be pushed to a relational database should inherit this class.
    """

    def __init__(self) -> None:
        pass

    @abc.abstractmethod
    def create_next_record(self) -> Union[RDSModel, None]:
        """
        Creates rds model instance.
        The process that consumes this class takes the output and serializes
        the record to the desired relational database.

        :return: a rds model instance or None if no more records to serialize
        """
        raise NotImplementedError

    def next_record(self) -> Union[RDSModel, None]:
        record = self.create_next_record()
        if not record:
            return None

        return record
