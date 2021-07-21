# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from typing import Iterator, Union

from databuilder.models.feature.feature_metadata import FeatureMetadata
from databuilder.models.graph_node import GraphNode
from databuilder.models.graph_relationship import GraphRelationship
from databuilder.models.graph_serializable import GraphSerializable
from databuilder.models.timestamp.timestamp_constants import TIMESTAMP_PROPERTY


# Unlike Watermark, which concerns itself with table implementation specifics (like partition),
# Feature_Watermark is more general and does not care how the feature is stored.
class FeatureWatermark(GraphSerializable):
    """
    Represents the high and low timestamp of data in a Feature.
    """
    NODE_LABEL = 'Feature_Watermark'

    TYPE_ATTR = 'watermark_type'

    WATERMARK_FEATURE_RELATION = 'BELONG_TO_FEATURE'
    FEATURE_WATERMARK_RELATION = 'WATERMARK'

    def __init__(self,
                 feature_group: str,
                 feature_name: str,
                 feature_version: str,
                 timestamp: int,
                 wm_type: str = 'high_watermark',
                 ) -> None:
        self.feature_group = feature_group
        self.feature_name = feature_name
        self.feature_version = feature_version
        self.timestamp = timestamp
        self.wm_type = wm_type

        self._node_iter = self._create_node_iterator()
        self._relation_iter = self._create_relation_iterator()

    def __repr__(self) -> str:
        return f'Feature_Watermark({self.wm_type!r}, {self.timestamp!r}, {self.feature_group!r}, ' \
               f'{self.feature_name!r}, {self.feature_version!r})'

    def _get_feature_key(self) -> str:
        return FeatureMetadata.KEY_FORMAT.format(feature_group=self.feature_group,
                                                 name=self.feature_name,
                                                 version=self.feature_version)

    def _get_watermark_key(self) -> str:
        return f'{self._get_feature_key()}/{self.wm_type}'

    def create_next_node(self) -> Union[GraphNode, None]:
        try:
            return next(self._node_iter)
        except StopIteration:
            return None

    def create_next_relation(self) -> Union[GraphRelationship, None]:
        try:
            return next(self._relation_iter)
        except StopIteration:
            return None

    def _create_node_iterator(self) -> Iterator[GraphNode]:
        yield GraphNode(
            key=self._get_watermark_key(),
            label=FeatureWatermark.NODE_LABEL,
            attributes={
                TIMESTAMP_PROPERTY: self.timestamp,
                FeatureWatermark.TYPE_ATTR: self.wm_type,
            }
        )

    def _create_relation_iterator(self) -> Iterator[GraphRelationship]:
        yield GraphRelationship(
            start_key=self._get_feature_key(),
            start_label=FeatureMetadata.NODE_LABEL,
            end_key=self._get_watermark_key(),
            end_label=FeatureWatermark.NODE_LABEL,
            type=FeatureWatermark.FEATURE_WATERMARK_RELATION,
            reverse_type=FeatureWatermark.WATERMARK_FEATURE_RELATION,
            attributes={}
        )
