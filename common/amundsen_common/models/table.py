# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from typing import List, Optional

import attr

from amundsen_common.models.user import User
from amundsen_common.models.badge import Badge
from amundsen_common.models.tag import Tag
from marshmallow3_annotations.ext.attrs import AttrsSchema


@attr.s(auto_attribs=True, kw_only=True)
class Reader:
    user: User
    read_count: int


class ReaderSchema(AttrsSchema):
    class Meta:
        target = Reader
        register_as_scheme = True


@attr.s(auto_attribs=True, kw_only=True)
class Watermark:
    watermark_type: Optional[str] = None
    partition_key: Optional[str] = None
    partition_value: Optional[str] = None
    create_time: Optional[str] = None


class WatermarkSchema(AttrsSchema):
    class Meta:
        target = Watermark
        register_as_scheme = True


@attr.s(auto_attribs=True, kw_only=True)
class Stat:
    stat_type: str
    stat_val: Optional[str] = None
    start_epoch: Optional[int] = None
    end_epoch: Optional[int] = None


class StatSchema(AttrsSchema):
    class Meta:
        target = Stat
        register_as_scheme = True


@attr.s(auto_attribs=True, kw_only=True)
class Column:
    name: str
    key: Optional[str] = None
    description: Optional[str] = None
    col_type: str
    sort_order: int
    stats: List[Stat] = []
    badges: Optional[List[Badge]] = []


class ColumnSchema(AttrsSchema):
    class Meta:
        target = Column
        register_as_scheme = True


@attr.s(auto_attribs=True, kw_only=True)
class Application:
    application_url: Optional[str] = None
    description: Optional[str] = None
    id: str
    name: Optional[str] = None
    kind: Optional[str] = None


class ApplicationSchema(AttrsSchema):
    class Meta:
        target = Application
        register_as_scheme = True


@attr.s(auto_attribs=True, kw_only=True)
class Source:
    source_type: str
    source: str


class SourceSchema(AttrsSchema):
    class Meta:
        target = Source
        register_as_scheme = True


@attr.s(auto_attribs=True, kw_only=True)
class ResourceReport:
    name: str
    url: str


class ResourceReportSchema(AttrsSchema):
    class Meta:
        target = ResourceReport
        register_as_scheme = True


# this is a temporary hack to satisfy mypy. Once https://github.com/python/mypy/issues/6136 is resolved, use
# `attr.converters.default_if_none(default=False)`
def default_if_none(arg: Optional[bool]) -> bool:
    return arg or False


@attr.s(auto_attribs=True, kw_only=True)
class ProgrammaticDescription:
    source: str
    text: str


class ProgrammaticDescriptionSchema(AttrsSchema):
    class Meta:
        target = ProgrammaticDescription
        register_as_scheme = True


@attr.s(auto_attribs=True, kw_only=True)
class TableSummary:
    database: str = attr.ib()
    cluster: str = attr.ib()
    schema: str = attr.ib()
    name: str = attr.ib()
    description: Optional[str] = attr.ib(default=None)
    schema_description: Optional[str] = attr.ib(default=None)


class TableSummarySchema(AttrsSchema):
    class Meta:
        target = TableSummary
        register_as_scheme = True


@attr.s(auto_attribs=True, kw_only=True)
class SqlJoin:
    column: str
    joined_on_table: TableSummary
    joined_on_column: str
    join_type: str
    join_sql: str


class SqlJoinSchema(AttrsSchema):
    class Meta:
        target = SqlJoin
        register_as_scheme = True


@attr.s(auto_attribs=True, kw_only=True)
class SqlWhere:
    where_clause: str


class SqlWhereSchema(AttrsSchema):
    class Meta:
        target = SqlWhere
        register_as_scheme = True


@attr.s(auto_attribs=True, kw_only=True)
class Table:
    database: str
    cluster: str
    schema: str
    name: str
    key: Optional[str] = None
    tags: List[Tag] = []
    badges: List[Badge] = []
    table_readers: List[Reader] = []
    description: Optional[str] = None
    columns: List[Column]
    owners: List[User] = []
    watermarks: List[Watermark] = []
    table_writer: Optional[Application] = None
    resource_reports: Optional[List[ResourceReport]] = None
    last_updated_timestamp: Optional[int] = None
    source: Optional[Source] = None
    is_view: Optional[bool] = attr.ib(default=None, converter=default_if_none)
    programmatic_descriptions: List[ProgrammaticDescription] = []
    common_joins: Optional[List[SqlJoin]] = None
    common_filters: Optional[List[SqlWhere]] = None


class TableSchema(AttrsSchema):
    class Meta:
        target = Table
        register_as_scheme = True
