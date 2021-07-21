# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import attr
from marshmallow3_annotations.ext.attrs import AttrsSchema


@attr.s(auto_attribs=True, kw_only=True)
class TagDetail:
    tag_name: str = attr.ib()
    tag_count: int = attr.ib()


class TagDetailSchema(AttrsSchema):
    class Meta:
        target = TagDetail
        register_as_scheme = True
