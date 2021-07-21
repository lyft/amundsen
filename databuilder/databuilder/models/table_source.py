# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from typing import (
    Iterator, Optional, Union,
)

from amundsen_common.utils.atlas import AtlasCommonParams, AtlasTableTypes
from amundsen_rds.models import RDSModel
from amundsen_rds.models.table import TableSource as RDSTableSource

from databuilder.models.atlas_entity import AtlasEntity
from databuilder.models.atlas_relationship import AtlasRelationship
from databuilder.models.atlas_serializable import AtlasSerializable
from databuilder.models.graph_node import GraphNode
from databuilder.models.graph_relationship import GraphRelationship
from databuilder.models.graph_serializable import GraphSerializable
from databuilder.models.table_metadata import TableMetadata
from databuilder.models.table_serializable import TableSerializable
from databuilder.serializers.atlas_serializer import get_entity_attrs
from databuilder.utils.atlas import AtlasRelationshipTypes, AtlasSerializedEntityOperation


class TableSource(GraphSerializable, TableSerializable, AtlasSerializable):
    """
    Hive table source model.
    """
    LABEL = 'Source'
    KEY_FORMAT = '{db}://{cluster}.{schema}/{tbl}/_source'
    SOURCE_TABLE_RELATION_TYPE = 'SOURCE_OF'
    TABLE_SOURCE_RELATION_TYPE = 'SOURCE'

    def __init__(self,
                 db_name: str,
                 schema: str,
                 table_name: str,
                 cluster: str,
                 source: str,
                 source_type: str = 'github',
                 ) -> None:
        self.db = db_name
        self.schema = schema
        self.table = table_name

        self.cluster = cluster if cluster else 'gold'
        # source is the source file location
        self.source = source
        self.source_type = source_type
        self._node_iter = self._create_node_iterator()
        self._relation_iter = self._create_relation_iterator()
        self._record_iter = self._create_record_iterator()
        self._atlas_entity_iterator = self._create_next_atlas_entity()
        self._atlas_relation_iterator = self._create_atlas_relation_iterator()

    def create_next_node(self) -> Optional[GraphNode]:
        # return the string representation of the data
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

    def get_source_model_key(self) -> str:
        return TableSource.KEY_FORMAT.format(db=self.db,
                                             cluster=self.cluster,
                                             schema=self.schema,
                                             tbl=self.table)

    def get_metadata_model_key(self) -> str:
        return f'{self.db}://{self.cluster}.{self.schema}/{self.table}'

    def _create_node_iterator(self) -> Iterator[GraphNode]:
        """
        Create a table source node
        :return:
        """
        node = GraphNode(
            key=self.get_source_model_key(),
            label=TableSource.LABEL,
            attributes={
                'source': self.source,
                'source_type': self.source_type
            }
        )
        yield node

    def _create_relation_iterator(self) -> Iterator[GraphRelationship]:
        """
        Create relation map between owner record with original hive table
        :return:
        """
        relationship = GraphRelationship(
            start_label=TableSource.LABEL,
            start_key=self.get_source_model_key(),
            end_label=TableMetadata.TABLE_NODE_LABEL,
            end_key=self.get_metadata_model_key(),
            type=TableSource.SOURCE_TABLE_RELATION_TYPE,
            reverse_type=TableSource.TABLE_SOURCE_RELATION_TYPE,
            attributes={}
        )
        yield relationship

    def _create_record_iterator(self) -> Iterator[RDSModel]:
        record = RDSTableSource(
            rk=self.get_source_model_key(),
            source=self.source,
            source_type=self.source_type,
            table_rk=self.get_metadata_model_key()
        )
        yield record

    def _create_atlas_source_entity(self) -> AtlasEntity:
        attrs_mapping = [
            (AtlasCommonParams.qualified_name, self.get_source_model_key()),
            ('name', self.source),
            ('source_type', self.source_type),
            ('displayName', self.source)
        ]

        entity_attrs = get_entity_attrs(attrs_mapping)

        entity = AtlasEntity(
            typeName=AtlasTableTypes.source,
            operation=AtlasSerializedEntityOperation.CREATE,
            attributes=entity_attrs,
            relationships=None
        )

        return entity

    def create_next_atlas_relation(self) -> Union[AtlasRelationship, None]:
        try:
            return next(self._atlas_relation_iterator)
        except StopIteration:
            return None

    def _create_atlas_relation_iterator(self) -> Iterator[AtlasRelationship]:
        relationship = AtlasRelationship(
            relationshipType=AtlasRelationshipTypes.table_source,
            entityType1=AtlasTableTypes.source,
            entityQualifiedName1=self.get_source_model_key(),
            entityType2=AtlasTableTypes.table,
            entityQualifiedName2=self.get_metadata_model_key(),
            attributes={}
        )

        yield relationship

    def _create_next_atlas_entity(self) -> Iterator[AtlasEntity]:
        yield self._create_atlas_source_entity()

    def create_next_atlas_entity(self) -> Union[AtlasEntity, None]:
        try:
            return next(self._atlas_entity_iterator)
        except StopIteration:
            return None

    def __repr__(self) -> str:
        return f'TableSource({self.db!r}, {self.cluster!r}, {self.schema!r}, {self.table!r}, {self.source!r})'
