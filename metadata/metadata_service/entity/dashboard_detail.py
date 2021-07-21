# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from typing import List, Optional

import attr
from amundsen_common.models.badge import Badge
from amundsen_common.models.popular_table import PopularTable
from amundsen_common.models.tag import Tag
from amundsen_common.models.user import User
from marshmallow3_annotations.ext.attrs import AttrsSchema

from metadata_service.entity.dashboard_query import DashboardQuery


@attr.s(auto_attribs=True, kw_only=True)
class DashboardDetail:
    uri: str = attr.ib()
    cluster: str = attr.ib()
    group_name: str = attr.ib()
    group_url: str = attr.ib()
    product: str = attr.ib()
    name: str = attr.ib()
    url: str = attr.ib()
    description: Optional[str] = attr.ib()
    created_timestamp: Optional[int] = attr.ib()
    updated_timestamp: Optional[int] = attr.ib()
    last_successful_run_timestamp: Optional[int] = attr.ib()
    last_run_timestamp: Optional[int] = attr.ib()
    last_run_state: Optional[str] = attr.ib()
    owners: List[User] = attr.ib(factory=list)
    frequent_users: List[User] = attr.ib(factory=list)
    chart_names: List[str] = attr.ib(factory=list)
    query_names: List[str] = attr.ib(factory=list)  # DEPRECATED
    queries: List[DashboardQuery] = attr.ib(factory=list)
    tables: List[PopularTable] = attr.ib(factory=list)
    tags: List[Tag] = attr.ib(factory=list)
    badges: List[Badge] = attr.ib(factory=list)
    recent_view_count: Optional[int] = attr.ib(default=0)


class DashboardSchema(AttrsSchema):
    class Meta:
        target = DashboardDetail
        register_as_scheme = True
