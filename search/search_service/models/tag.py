# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import attr
from marshmallow3_annotations.ext.attrs import AttrsSchema


@attr.s(auto_attribs=True, kw_only=True)
class Tag:
    tag_name: str

    def __init__(self, tag_name: str):
        self.tag_name = tag_name

    def __str__(self) -> str:
        return self.tag_name


class TagSchema(AttrsSchema):
    class Meta:
        target = Tag
        register_as_scheme = True
