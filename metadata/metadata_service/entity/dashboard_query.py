# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from typing import Optional

import attr
from marshmallow3_annotations.ext.attrs import AttrsSchema


@attr.s(auto_attribs=True, kw_only=True)
class DashboardQuery:
    name: Optional[str] = attr.ib(default=None)
    url: Optional[str] = attr.ib(default=None)
    query_text: Optional[str] = attr.ib(default=None)


class DashboardQuerySchema(AttrsSchema):
    class Meta:
        target = DashboardQuery
        register_as_scheme = True
