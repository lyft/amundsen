from typing import Optional

import attr

from marshmallow3_annotations.ext.attrs import AttrsSchema


@attr.s(auto_attribs=True, kw_only=True)
class GenerationCode:
    key: Optional[str]
    text: str
    source: Optional[str]


class GenerationCodeSchema(AttrsSchema):
    class Meta:
        target = GenerationCode
        register_as_scheme = True
