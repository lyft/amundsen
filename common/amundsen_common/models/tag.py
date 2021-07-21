import attr

from marshmallow3_annotations.ext.attrs import AttrsSchema


@attr.s(auto_attribs=True, kw_only=True)
class Tag:
    tag_type: str
    tag_name: str


class TagSchema(AttrsSchema):
    class Meta:
        target = Tag
        register_as_scheme = True
