# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import attr
from marshmallow3_annotations.ext.attrs import AttrsSchema


@attr.s(auto_attribs=True, kw_only=True)
class Badge:
    badge_name: str = attr.ib()
    category: str = attr.ib()


class BadgeSchema(AttrsSchema):
    class Meta:
        target = Badge
        register_as_scheme = True
