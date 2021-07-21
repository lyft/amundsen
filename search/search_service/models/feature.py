# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from typing import (
    List, Optional, Set,
)

import attr
from marshmallow3_annotations.ext.attrs import AttrsSchema

from search_service.models.base import Base
from search_service.models.tag import Tag


@attr.s(auto_attribs=True, kw_only=True)
class Feature(Base):
    """
    This represents the part of a feature stored in the search proxy
    """
    id: str
    feature_group: str
    feature_name: str
    version: str
    key: str
    total_usage: int = 0
    status: Optional[str] = None
    entity: Optional[str] = None
    description: Optional[str] = None
    availability: Optional[List[str]] = None
    badges: Optional[List[Tag]] = None
    tags: Optional[List[Tag]] = None
    last_updated_timestamp: Optional[int] = None

    def get_id(self) -> str:
        return self.id

    def get_attrs_dict(self) -> dict:
        attrs_dict = self.__dict__.copy()
        if self.tags is not None:
            attrs_dict['tags'] = [str(tag) for tag in self.tags]
        if self.badges is not None:
            attrs_dict['badges'] = [str(badge) for badge in self.badges]
        if self.availability is not None:
            attrs_dict['availability'] = [str(db) for db in self.availability]
        return attrs_dict

    @classmethod
    def get_attrs(cls) -> Set:
        return {
            'id',
            'feature_group',
            'feature_name',
            'version',
            'key',
            'total_usage',
            'status',
            'entity',
            'description',
            'availability',
            'badges',
            'tags',
            'last_updated_timestamp',
        }

    @staticmethod
    def get_type() -> str:
        return 'feature'


class FeatureSchema(AttrsSchema):
    class Meta:
        target = Feature
        register_as_scheme = True


@attr.s(auto_attribs=True, kw_only=True)
class SearchFeatureResult:
    total_results: int = attr.ib()
    results: List[Feature] = attr.ib(factory=list)


class SearchFeatureResultSchema(AttrsSchema):
    class Meta:
        target = SearchFeatureResult
        register_as_scheme = True
