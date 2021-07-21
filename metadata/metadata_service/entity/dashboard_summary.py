# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from typing import List

import attr
from amundsen_common.models.dashboard import DashboardSummary as Summary
from marshmallow3_annotations.ext.attrs import AttrsSchema


@attr.s(auto_attribs=True, kw_only=True)
class DashboardSummary:
    dashboards: List[Summary] = attr.ib(factory=list)


class DashboardSummarySchema(AttrsSchema):
    class Meta:
        target = DashboardSummary
        register_as_scheme = True
