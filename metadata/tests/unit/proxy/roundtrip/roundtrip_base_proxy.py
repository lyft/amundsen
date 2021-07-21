# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from abc import abstractmethod
from typing import List

from amundsen_common.models.table import (Application, Column,
                                          ProgrammaticDescription, Table)
from amundsen_common.models.user import User

from metadata_service.proxy import BaseProxy


class RoundtripBaseProxy(BaseProxy):
    """
    A base proxy that supports roundtrip tests
    """
    @abstractmethod
    def put_user(self, *, data: User) -> None:
        pass

    @abstractmethod
    def post_users(self, *, data: List[User]) -> None:
        pass

    @abstractmethod
    def put_app(self, *, data: Application) -> None:
        pass

    @abstractmethod
    def post_apps(self, *, data: List[Application]) -> None:
        pass

    @abstractmethod
    def put_table(self, *, table: Table) -> None:
        pass

    @abstractmethod
    def post_tables(self, *, tables: List[Table]) -> None:
        pass

    @abstractmethod
    def put_column(self, *, table_uri: str, column: Column) -> None:
        pass

    @abstractmethod
    def put_programmatic_table_description(self, *, table_uri: str, description: ProgrammaticDescription) -> None:
        pass

    @abstractmethod
    def add_read_count(self, *, table_uri: str, user_id: str, read_count: int) -> None:
        pass
