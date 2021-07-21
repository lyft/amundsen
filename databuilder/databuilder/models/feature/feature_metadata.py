# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from typing import (
    Any, Dict, Iterator, List, Optional, Set,
)

from databuilder.models.graph_node import GraphNode
from databuilder.models.graph_relationship import GraphRelationship
from databuilder.models.graph_serializable import GraphSerializable
from databuilder.models.table_metadata import (
    DescriptionMetadata, TableMetadata, TagMetadata, _format_as_list,
)


class FeatureMetadata(GraphSerializable):
    """
    Base feature metadata.

    It implements GraphSerializable (TODO: implement TableSerializable)
    so that it can be serialized to produce Feature, Feature_Group, Tag,
    Database, Description and relations between those.
    """

    NODE_LABEL = 'Feature'
    KEY_FORMAT = '{feature_group}/{name}/{version}'

    NAME_ATTR = 'name'
    VERSION_ATTR = 'version'
    STATUS_ATTR = 'status'
    ENTITY_ATTR = 'entity'
    DATA_TYPE_ATTR = 'data_type'
    CREATED_TIMESTAMP_ATTR = 'created_timestamp'
    LAST_UPDATED_TIMESTAMP_ATTR = 'last_updated_timestamp'

    GROUP_NODE_LABEL = 'Feature_Group'
    GROUP_KEY_FORMAT = '{feature_group}'
    GROUP_FEATURE_RELATION_TYPE = 'GROUPS'
    FEATURE_GROUP_RELATION_TYPE = 'GROUPED_BY'

    FEATURE_DATABASE_RELATION_TYPE = 'FEATURE_AVAILABLE_IN'
    DATABASE_FEATURE_RELATION_TYPE = 'AVAILABLE_FEATURE'

    processed_feature_group_keys: Set[str] = set()
    processed_database_keys: Set[str] = set()

    def __init__(self,
                 feature_group: str,
                 name: str,
                 version: str,
                 status: Optional[str] = None,
                 entity: Optional[str] = None,
                 data_type: Optional[str] = None,
                 availability: List[str] = None,  # list of databases
                 description: Optional[str] = None,
                 tags: List[str] = None,
                 created_timestamp: Optional[int] = None,
                 last_updated_timestamp: Optional[int] = None,
                 **kwargs: Any
                 ) -> None:

        self.feature_group = feature_group
        self.name = name
        self.version = version
        self.status = status
        # what business entity the feature is about, e.g. 'Buyer', 'Ride', 'Listing', etc.
        self.entity = entity
        self.data_type = data_type
        self.availability = _format_as_list(availability)
        self.description = DescriptionMetadata.create_description_metadata(text=description)
        self.tags = _format_as_list(tags)
        self.created_timestamp = created_timestamp
        self.last_updated_timestamp = last_updated_timestamp

        self._node_iterator = self._create_next_node()
        self._relation_iterator = self._create_next_relation()

    def __repr__(self) -> str:
        return f'FeatureMetadata(' \
               f'{self.feature_group!r}, {self.name!r}, {self.version!r}, {self.status!r}, ' \
               f'{self.entity!r}, {self.data_type!r}, {self.availability!r}, {self.description!r}, ' \
               f'{self.tags!r}, {self.created_timestamp!r}, {self.last_updated_timestamp!r})'

    def _get_feature_key(self) -> str:
        return FeatureMetadata.KEY_FORMAT.format(feature_group=self.feature_group,
                                                 name=self.name,
                                                 version=self.version)

    def _get_feature_group_key(self) -> str:
        return FeatureMetadata.GROUP_KEY_FORMAT.format(feature_group=self.feature_group)

    def create_next_node(self) -> Optional[GraphNode]:
        try:
            return next(self._node_iterator)
        except StopIteration:
            return None

    def _get_feature_node_attributes(self) -> Dict[str, Any]:
        feature_node_attrs: Dict[str, Any] = {
            FeatureMetadata.NAME_ATTR: self.name,
        }
        if self.version:
            feature_node_attrs[FeatureMetadata.VERSION_ATTR] = self.version

        if self.status:
            feature_node_attrs[FeatureMetadata.STATUS_ATTR] = self.status

        if self.entity:
            feature_node_attrs[FeatureMetadata.ENTITY_ATTR] = self.entity

        if self.data_type:
            feature_node_attrs[FeatureMetadata.DATA_TYPE_ATTR] = self.data_type

        if self.created_timestamp:
            feature_node_attrs[FeatureMetadata.CREATED_TIMESTAMP_ATTR] = self.created_timestamp

        if self.last_updated_timestamp:
            feature_node_attrs[FeatureMetadata.LAST_UPDATED_TIMESTAMP_ATTR] = self.last_updated_timestamp

        return feature_node_attrs

    def _create_next_node(self) -> Iterator[GraphNode]:
        yield GraphNode(
            key=self._get_feature_key(),
            label=FeatureMetadata.NODE_LABEL,
            attributes=self._get_feature_node_attributes()
        )

        if self.feature_group:
            fg = GraphNode(
                key=self._get_feature_group_key(),
                label=FeatureMetadata.GROUP_NODE_LABEL,
                attributes={FeatureMetadata.NAME_ATTR: self.feature_group},
            )
            if fg.key not in FeatureMetadata.processed_feature_group_keys:
                FeatureMetadata.processed_feature_group_keys.add(fg.key)
                yield fg

        if self.description:
            yield self.description.get_node(
                node_key=self.description.get_description_default_key(  # type: ignore
                    start_key=self._get_feature_key()),
            )

        for database in self.availability:
            db = GraphNode(
                key=TableMetadata.DATABASE_KEY_FORMAT.format(db=database),
                label=TableMetadata.DATABASE_NODE_LABEL,
                attributes={
                    FeatureMetadata.NAME_ATTR: database
                }
            )
            if db.key not in FeatureMetadata.processed_database_keys:
                FeatureMetadata.processed_database_keys.add(db.key)
                yield db

        for tag_value in self.tags:
            yield TagMetadata(name=tag_value).get_node()

    def create_next_relation(self) -> Optional[GraphRelationship]:
        try:
            return next(self._relation_iterator)
        except StopIteration:
            return None

    def _create_next_relation(self) -> Iterator[GraphRelationship]:
        # Feature <> Feature group
        if self.feature_group:
            yield GraphRelationship(
                start_label=FeatureMetadata.NODE_LABEL,
                end_label=FeatureMetadata.GROUP_NODE_LABEL,
                start_key=self._get_feature_key(),
                end_key=self._get_feature_group_key(),
                type=FeatureMetadata.FEATURE_GROUP_RELATION_TYPE,
                reverse_type=FeatureMetadata.GROUP_FEATURE_RELATION_TYPE,
                attributes={}
            )

        # Feature <> Description
        if self.description:
            yield GraphRelationship(
                start_label=FeatureMetadata.NODE_LABEL,
                end_label=DescriptionMetadata.DESCRIPTION_NODE_LABEL,
                start_key=self._get_feature_key(),
                end_key=self.description.get_description_default_key(start_key=self._get_feature_key()),
                type=DescriptionMetadata.DESCRIPTION_RELATION_TYPE,
                reverse_type=DescriptionMetadata.INVERSE_DESCRIPTION_RELATION_TYPE,
                attributes={}
            )

        # Feature <> Database
        for database in self.availability:
            yield GraphRelationship(
                start_label=FeatureMetadata.NODE_LABEL,
                end_label=TableMetadata.DATABASE_NODE_LABEL,
                start_key=self._get_feature_key(),
                end_key=TableMetadata.DATABASE_KEY_FORMAT.format(db=database),
                type=FeatureMetadata.FEATURE_DATABASE_RELATION_TYPE,
                reverse_type=FeatureMetadata.DATABASE_FEATURE_RELATION_TYPE,
                attributes={}
            )

        # Feature <> Tag
        for tag in self.tags:
            yield GraphRelationship(
                start_label=FeatureMetadata.NODE_LABEL,
                end_label=TagMetadata.TAG_NODE_LABEL,
                start_key=self._get_feature_key(),
                end_key=TagMetadata.get_tag_key(tag),
                type=TagMetadata.ENTITY_TAG_RELATION_TYPE,
                reverse_type=TagMetadata.TAG_ENTITY_RELATION_TYPE,
                attributes={}
            )
