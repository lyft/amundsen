# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import string
from typing import Any, List, Optional

from amundsen_common.models.table import (Application, Column,
                                          ProgrammaticDescription, Stat, Table,
                                          Tag)
from amundsen_common.models.user import User


class Fixtures:
    """
    These fixtures are useful for creating test objects. For an example usage, check out tests/tests/test_fixtures.py
    """
    counter = 1000

    @staticmethod
    def next_int() -> int:
        i = Fixtures.counter
        Fixtures.counter += 1
        return i

    @staticmethod
    def next_string(*, prefix: str = '', length: int = 10) -> str:
        astr: str = prefix + \
            ''.join(Fixtures.next_item(items=list(string.ascii_lowercase)) for _ in range(length)) + \
            ('%06d' % Fixtures.next_int())
        return astr

    @staticmethod
    def next_range() -> range:
        return range(0, Fixtures.next_int() % 5)

    @staticmethod
    def next_item(*, items: List[Any]) -> Any:
        return items[Fixtures.next_int() % len(items)]

    @staticmethod
    def next_database() -> str:
        return Fixtures.next_item(items=list(["database1", "database2"]))

    @staticmethod
    def next_application(*, application_id: Optional[str] = None) -> Application:
        if not application_id:
            application_id = Fixtures.next_string(prefix='ap', length=8)
        application = Application(application_url=f'https://{application_id}.example.com',
                                  description=f'{application_id} description',
                                  name=application_id.capitalize(),
                                  id=application_id)
        return application

    @staticmethod
    def next_tag(*, tag_name: Optional[str] = None) -> Tag:
        if not tag_name:
            tag_name = Fixtures.next_string(prefix='ta', length=8)
        return Tag(tag_name=tag_name, tag_type='default')

    @staticmethod
    def next_tags() -> List[Tag]:
        return sorted([Fixtures.next_tag() for _ in Fixtures.next_range()])

    @staticmethod
    def next_description_source() -> str:
        return Fixtures.next_string(prefix='de', length=8)

    @staticmethod
    def next_description(*, text: Optional[str] = None, source: Optional[str] = None) -> ProgrammaticDescription:
        if not text:
            text = Fixtures.next_string(length=20)
        if not source:
            source = Fixtures.next_description_source()
        return ProgrammaticDescription(text=text, source=source)

    @staticmethod
    def next_col_type() -> str:
        return Fixtures.next_item(items=['varchar', 'int', 'blob', 'timestamp', 'datetime'])

    @staticmethod
    def next_column(*,
                    table_key: str,
                    sort_order: int,
                    name: Optional[str] = None) -> Column:
        if not name:
            name = Fixtures.next_string(prefix='co', length=8)

        return Column(name=name,
                      description=f'{name} description',
                      col_type=Fixtures.next_col_type(),
                      key=f'{table_key}/{name}',
                      sort_order=sort_order,
                      stats=[Stat(stat_type='num_rows',
                                  stat_val=f'{Fixtures.next_int() * 100}',
                                  start_epoch=None,
                                  end_epoch=None)])

    @staticmethod
    def next_columns(*,
                     table_key: str,
                     randomize_pii: bool = False,
                     randomize_data_subject: bool = False) -> List[Column]:
        return [Fixtures.next_column(table_key=table_key,
                                     sort_order=i
                                     ) for i in Fixtures.next_range()]

    @staticmethod
    def next_descriptions() -> List[ProgrammaticDescription]:
        return sorted([Fixtures.next_description() for _ in Fixtures.next_range()])

    @staticmethod
    def next_table(table: Optional[str] = None,
                   cluster: Optional[str] = None,
                   schema: Optional[str] = None,
                   database: Optional[str] = None,
                   tags: Optional[List[Tag]] = None,
                   application: Optional[Application] = None) -> Table:
        """
        Returns a table for testing in the test_database
        """
        if not database:
            database = Fixtures.next_database()

        if not table:
            table = Fixtures.next_string(prefix='tb', length=8)

        if not cluster:
            cluster = Fixtures.next_string(prefix='cl', length=8)

        if not schema:
            schema = Fixtures.next_string(prefix='sc', length=8)

        if not tags:
            tags = Fixtures.next_tags()

        table_key: str = f'{database}://{cluster}.{schema}/{table}'
        # TODO: add owners, watermarks, last_udpated_timestamp, source
        return Table(database=database,
                     cluster=cluster,
                     schema=schema,
                     name=table,
                     key=table_key,
                     tags=tags,
                     table_writer=application,
                     table_readers=[],
                     description=f'{table} description',
                     programmatic_descriptions=Fixtures.next_descriptions(),
                     columns=Fixtures.next_columns(table_key=table_key),
                     is_view=False
                     )

    @staticmethod
    def next_user(*, user_id: Optional[str] = None, is_active: bool = True) -> User:
        last_name = ''.join(Fixtures.next_item(items=list(string.ascii_lowercase)) for _ in range(6)).capitalize()
        first_name = Fixtures.next_item(items=['alice', 'bob', 'carol', 'dan']).capitalize()
        if not user_id:
            user_id = Fixtures.next_string(prefix='us', length=8)
        return User(user_id=user_id,
                    email=f'{user_id}@example.com',
                    is_active=is_active,
                    first_name=first_name,
                    last_name=last_name,
                    full_name=f'{first_name} {last_name}')


def next_application(**kwargs: Any) -> Application:
    return Fixtures.next_application(**kwargs)


def next_int() -> int:
    return Fixtures.next_int()


def next_string(**kwargs: Any) -> str:
    return Fixtures.next_string(**kwargs)


def next_range() -> range:
    return Fixtures.next_range()


def next_item(**kwargs: Any) -> Any:
    return Fixtures.next_item(**kwargs)


def next_database() -> str:
    return Fixtures.next_database()


def next_tag(**kwargs: Any) -> Tag:
    return Fixtures.next_tag(**kwargs)


def next_tags() -> List[Tag]:
    return Fixtures.next_tags()


def next_description_source() -> str:
    return Fixtures.next_description_source()


def next_description(**kwargs: Any) -> ProgrammaticDescription:
    return Fixtures.next_description(**kwargs)


def next_col_type() -> str:
    return Fixtures.next_col_type()


def next_column(**kwargs: Any) -> Column:
    return Fixtures.next_column(**kwargs)


def next_columns(**kwargs: Any) -> List[Column]:
    return Fixtures.next_columns(**kwargs)


def next_descriptions() -> List[ProgrammaticDescription]:
    return Fixtures.next_descriptions()


def next_table(**kwargs: Any) -> Table:
    return Fixtures.next_table(**kwargs)


def next_user(**kwargs: Any) -> User:
    return Fixtures.next_user(**kwargs)
