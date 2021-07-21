# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from typing import List, Optional, Dict, Any

import attr

from amundsen_common.models.user import User
from amundsen_common.models.badge import Badge
from amundsen_common.models.tag import Tag
from amundsen_common.models.table import ProgrammaticDescription
from marshmallow3_annotations.ext.attrs import AttrsSchema


@attr.s(auto_attribs=True, kw_only=True)
class ColumnItem:
    column_name: str
    column_type: str


class ColumnItemSchema(AttrsSchema):
    class Meta:
        target = ColumnItem
        register_as_scheme = True


@attr.s(auto_attribs=True, kw_only=True)
class DataSample:
    # Modeled after preview data model in FE
    columns: List[ColumnItem]
    data: List[Dict[str, Any]]
    error_text: str


class DataSampleSchema(AttrsSchema):
    class Meta:
        target = DataSample
        register_as_scheme = True


@attr.s(auto_attribs=True, kw_only=True)
class FeatureWatermark:
    key: Optional[str]
    watermark_type: Optional[str]
    time: str


class FeatureWatermarkSchema(AttrsSchema):
    class Meta:
        target = FeatureWatermark
        register_as_scheme = True


@attr.s(auto_attribs=True, kw_only=True)
class Feature:
    key: Optional[str] = attr.ib(default=None)
    name: str
    version: str  # ex: "1.2.0"
    status: Optional[str]
    feature_group: str
    entity: Optional[str]
    data_type: Optional[str]
    availability: List[str]
    description: Optional[str] = attr.ib(default=None)
    owners: List[User]
    badges: List[Badge]
    tags: List[Tag]
    programmatic_descriptions: List[ProgrammaticDescription]
    watermarks: List[FeatureWatermark]
    last_updated_timestamp: Optional[int]
    created_timestamp: Optional[int]


class FeatureSchema(AttrsSchema):
    class Meta:
        target = Feature
        register_as_scheme = True


@attr.s(auto_attribs=True, kw_only=True)
class FeatureSummary:
    key: str  # ex: test_feature_group_name/test_feature_name/1.2.0
    name: str
    version: str
    availability: List[str]
    entity: List[str]
    description: Optional[str] = attr.ib(default=None)
    badges: List[Badge]
    last_updated_timestamp: Optional[int]


class FeatureSummarySchema(AttrsSchema):
    class Meta:
        target = FeatureSummary
        register_as_scheme = True
