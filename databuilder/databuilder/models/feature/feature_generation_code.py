# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from typing import (
    Any, Dict, Iterator, Optional, Union,
)

from databuilder.models.feature.feature_metadata import FeatureMetadata
from databuilder.models.graph_node import GraphNode
from databuilder.models.graph_relationship import GraphRelationship
from databuilder.models.graph_serializable import GraphSerializable


# FeatureGenerationCode allows ingesting as text the generation code - whether sql or not -
# which was used to create a feature. Unlike the Query node for Dashboards, it has no inherent
# concept of name, url, id, or hierarchical structure. This allows for maximum flexibility to
# ingest generation code regardless of source.
class FeatureGenerationCode(GraphSerializable):
    NODE_LABEL = 'Feature_Generation_Code'

    TEXT_ATTR = 'text'
    LAST_EXECUTED_TIMESTAMP_ATTR = 'last_executed_timestamp'
    SOURCE_ATTR = 'source'

    FEATURE_GENCODE_RELATION_TYPE = 'GENERATION_CODE'
    GENCODE_FEATURE_RELATION_TYPE = 'GENERATION_CODE_OF'

    def __init__(self,
                 feature_group: str,
                 feature_name: str,
                 feature_version: str,
                 text: str,
                 source: Optional[str] = None,
                 last_executed_timestamp: Optional[int] = None,
                 **kwargs: Any
                 ) -> None:

        self.feature_group = feature_group
        self.feature_name = feature_name
        self.feature_version = feature_version
        self.text = text
        self.source = source
        self.last_executed_timestamp = last_executed_timestamp

        self._node_iterator = self._create_node_iterator()
        self._relation_iterator = self._create_relation_iterator()

    def __repr__(self) -> str:
        return f'Feature_Generation_Code({self.feature_group!r}, {self.feature_name!r}, {self.feature_version!r}, ' \
               f'{self.text!r}, {self.source!r}, {self.last_executed_timestamp!r})'

    def _get_feature_key(self) -> str:
        return FeatureMetadata.KEY_FORMAT.format(feature_group=self.feature_group,
                                                 name=self.feature_name,
                                                 version=self.feature_version)

    def _get_generation_code_key(self) -> str:
        return f'{self._get_feature_key()}/_generation_code'

    def create_next_node(self) -> Union[GraphNode, None]:
        try:
            return next(self._node_iterator)
        except StopIteration:
            return None

    def _create_node_iterator(self) -> Iterator[GraphNode]:
        attrs: Dict[str, Any] = {
            FeatureGenerationCode.TEXT_ATTR: self.text,
        }
        if self.last_executed_timestamp:
            attrs[FeatureGenerationCode.LAST_EXECUTED_TIMESTAMP_ATTR] = self.last_executed_timestamp

        if self.source:
            attrs[FeatureGenerationCode.SOURCE_ATTR] = self.source

        yield GraphNode(
            key=self._get_generation_code_key(),
            label=FeatureGenerationCode.NODE_LABEL,
            attributes=attrs,
        )

    def create_next_relation(self) -> Union[GraphRelationship, None]:
        try:
            return next(self._relation_iterator)
        except StopIteration:
            return None

    def _create_relation_iterator(self) -> Iterator[GraphRelationship]:
        yield GraphRelationship(
            start_label=FeatureMetadata.NODE_LABEL,
            end_label=FeatureGenerationCode.NODE_LABEL,
            start_key=self._get_feature_key(),
            end_key=self._get_generation_code_key(),
            type=FeatureGenerationCode.FEATURE_GENCODE_RELATION_TYPE,
            reverse_type=FeatureGenerationCode.GENCODE_FEATURE_RELATION_TYPE,
            attributes={},
        )
