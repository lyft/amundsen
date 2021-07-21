# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from typing import Optional, List

from amundsen_common.models.badge import Badge

import attr
from marshmallow3_annotations.ext.attrs import AttrsSchema


@attr.s(auto_attribs=True, kw_only=True)
class LineageItem:
    key: str  # down/upstream table/col/task key
    level: int  # upstream/downstream distance from current resource
    source: str  # database this resource is from
    badges: Optional[List[Badge]] = None
    usage: Optional[int] = None  # statistic to sort lineage items by
    parent: Optional[str] = None  # key of the parent entity, used to create the relationships in graph


class LineageItemSchema(AttrsSchema):
    class Meta:
        target = LineageItem
        register_as_scheme = True


@attr.s(auto_attribs=True, kw_only=True)
class Lineage:
    key: str  # current table/col/task key
    direction: str  # upstream/downstream/both
    depth: int  # how many levels up/down 0 == all
    upstream_entities: List[LineageItem]  # list of upstream entities
    downstream_entities: List[LineageItem]  # list of downstream entities


class LineageSchema(AttrsSchema):
    class Meta:
        target = Lineage
        register_as_scheme = True
