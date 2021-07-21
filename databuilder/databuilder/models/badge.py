# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from typing import (
    Iterator, List, Optional, Union,
)

from amundsen_common.utils.atlas import AtlasCommonParams, AtlasCommonTypes
from amundsen_rds.models import RDSModel
from amundsen_rds.models.badge import Badge as RDSBadge

from databuilder.models.atlas_entity import AtlasEntity
from databuilder.models.atlas_relationship import AtlasRelationship
from databuilder.models.atlas_serializable import AtlasSerializable
from databuilder.models.graph_node import GraphNode
from databuilder.models.graph_relationship import GraphRelationship
from databuilder.models.graph_serializable import GraphSerializable
from databuilder.models.table_serializable import TableSerializable
from databuilder.serializers.atlas_serializer import get_entity_attrs
from databuilder.utils.atlas import AtlasRelationshipTypes, AtlasSerializedEntityOperation


class Badge:
    def __init__(self, name: str, category: str):
        # Amundsen UI always formats badge display with first letter capitalized while other letters are lowercase.
        # Clicking table badges in UI always results in searching lower cases badges
        # https://github.com/amundsen-io/amundsen/blob/6ec9b398634264e52089bb9e1b7d76a6fb6a35a4/frontend/amundsen_application/static/js/components/BadgeList/index.tsx#L56
        # If badges stored in neo4j are not lowercase, they won't be searchable in UI.
        self.name = name.lower()
        self.category = category.lower()

    def __repr__(self) -> str:
        return f'Badge({self.name!r}, {self.category!r})'

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Badge):
            return NotImplemented
        return self.name == other.name and self.category == other.category


class BadgeMetadata(GraphSerializable, TableSerializable, AtlasSerializable):
    """
    Badge model.
    """
    BADGE_NODE_LABEL = 'Badge'
    BADGE_KEY_FORMAT = '{badge}'
    BADGE_CATEGORY = 'category'

    # Relation between entity and badge
    BADGE_RELATION_TYPE = 'HAS_BADGE'
    INVERSE_BADGE_RELATION_TYPE = 'BADGE_FOR'

    LABELS_PERMITTED_TO_HAVE_BADGE = ['Table', 'Dashboard', 'Column', 'Feature']

    def __init__(self,
                 start_label: str,
                 start_key: str,
                 badges: List[Badge],
                 ):
        if start_label not in BadgeMetadata.LABELS_PERMITTED_TO_HAVE_BADGE:
            raise Exception(f'badges for {start_label} are not supported')
        self.start_label = start_label
        self.start_key = start_key
        self.badges = badges

        self._node_iter = self._create_node_iterator()
        self._relation_iter = self._create_relation_iterator()
        self._record_iter = self._create_record_iterator()
        self._atlas_entity_iterator = self._create_next_atlas_entity()
        self._atlas_relation_iterator = self._create_atlas_relation_iterator()

    def __repr__(self) -> str:
        return f'BadgeMetadata({self.start_label!r}, {self.start_key!r}, {self.badges!r})'

    def create_next_node(self) -> Optional[GraphNode]:
        try:
            return next(self._node_iter)
        except StopIteration:
            return None

    def create_next_relation(self) -> Optional[GraphRelationship]:
        try:
            return next(self._relation_iter)
        except StopIteration:
            return None

    def create_next_record(self) -> Union[RDSModel, None]:
        try:
            return next(self._record_iter)
        except StopIteration:
            return None

    @staticmethod
    def get_badge_key(name: str) -> str:
        if not name:
            return ''
        return BadgeMetadata.BADGE_KEY_FORMAT.format(badge=name)

    def get_badge_nodes(self) -> List[GraphNode]:
        nodes = []
        for badge in self.badges:
            if badge:
                node = GraphNode(
                    key=self.get_badge_key(badge.name),
                    label=self.BADGE_NODE_LABEL,
                    attributes={
                        self.BADGE_CATEGORY: badge.category
                    }
                )
                nodes.append(node)
        return nodes

    def get_badge_relations(self) -> List[GraphRelationship]:
        relations = []
        for badge in self.badges:
            relation = GraphRelationship(
                start_label=self.start_label,
                end_label=self.BADGE_NODE_LABEL,
                start_key=self.start_key,
                end_key=self.get_badge_key(badge.name),
                type=self.BADGE_RELATION_TYPE,
                reverse_type=self.INVERSE_BADGE_RELATION_TYPE,
                attributes={}
            )
            relations.append(relation)
        return relations

    def get_badge_records(self) -> List[RDSModel]:
        records = []
        for badge in self.badges:
            if badge:
                record = RDSBadge(
                    rk=self.get_badge_key(badge.name),
                    category=badge.category
                )
                records.append(record)

        return records

    def _create_node_iterator(self) -> Iterator[GraphNode]:
        """
        Create badge nodes
        :return:
        """
        nodes = self.get_badge_nodes()
        for node in nodes:
            yield node

    def _create_relation_iterator(self) -> Iterator[GraphRelationship]:
        relations = self.get_badge_relations()
        for relation in relations:
            yield relation

    def _create_record_iterator(self) -> Iterator[RDSModel]:
        records = self.get_badge_records()
        for record in records:
            yield record

    def _create_atlas_classification_entity(self, badge: Badge) -> AtlasEntity:
        attrs_mapping = [
            (AtlasCommonParams.qualified_name, badge.name),
            ('category', badge.category),
            ('name', badge.name)
        ]

        entity_attrs = get_entity_attrs(attrs_mapping)

        entity = AtlasEntity(
            typeName=AtlasCommonTypes.badge,
            operation=AtlasSerializedEntityOperation.CREATE,
            attributes=entity_attrs,
            relationships=None
        )

        return entity

    def _create_atlas_classification_relation(self, badge: Badge) -> AtlasRelationship:
        table_relationship = AtlasRelationship(
            relationshipType=AtlasRelationshipTypes.badge,
            entityType1=AtlasCommonTypes.data_set,
            entityQualifiedName1=self.start_key,
            entityType2=AtlasRelationshipTypes.badge,
            entityQualifiedName2=badge.name,
            attributes={}
        )

        return table_relationship

    def _create_atlas_relation_iterator(self) -> Iterator[AtlasRelationship]:
        for badge in self.badges:
            yield self._create_atlas_classification_relation(badge)

    def create_next_atlas_relation(self) -> Union[AtlasRelationship, None]:
        try:
            return next(self._atlas_relation_iterator)
        except StopIteration:
            return None

    def _create_next_atlas_entity(self) -> Iterator[AtlasEntity]:
        for badge in self.badges:
            yield self._create_atlas_classification_entity(badge)

    def create_next_atlas_entity(self) -> Union[AtlasEntity, None]:
        try:
            return next(self._atlas_entity_iterator)
        except StopIteration:
            return None
