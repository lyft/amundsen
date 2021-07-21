# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import attr
from marshmallow3_annotations.ext.attrs import AttrsSchema


@attr.s(auto_attribs=True, kw_only=True)
class Description:
    description: str = attr.ib()


class DescriptionSchema(AttrsSchema):
    class Meta:
        target = Description
        register_as_scheme = True
