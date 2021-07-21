# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import re
from typing import (
    Any, Iterator, Union,
)

from amundsen_common.utils.atlas import AtlasCommonParams, AtlasTableTypes
from amundsen_rds.models import RDSModel
from amundsen_rds.models.schema import (
    Schema as RDSSchema, SchemaDescription as RDSSchemaDescription,
    SchemaProgrammaticDescription as RDSSchemaProgrammaticDescription,
)

from databuilder.models.atlas_entity import AtlasEntity
from databuilder.models.atlas_relationship import AtlasRelationship
from databuilder.models.atlas_serializable import AtlasSerializable
from databuilder.models.graph_node import GraphNode
from databuilder.models.graph_relationship import GraphRelationship
from databuilder.models.graph_serializable import GraphSerializable
from databuilder.models.schema.schema_constant import (
    SCHEMA_KEY_PATTERN_REGEX, SCHEMA_NAME_ATTR, SCHEMA_NODE_LABEL,
)
from databuilder.models.table_metadata import DescriptionMetadata
from databuilder.models.table_serializable import TableSerializable
from databuilder.serializers.atlas_serializer import get_entity_attrs
from databuilder.utils.atlas import AtlasSerializedEntityOperation


class SchemaModel(GraphSerializable, TableSerializable, AtlasSerializable):
    def __init__(self,
                 schema_key: str,
                 schema: str,
                 description: str = None,
                 description_source: str = None,
                 **kwargs: Any
                 ) -> None:
        self._schema_key = schema_key
        self._schema = schema
        self._cluster_key = self._get_cluster_key(schema_key)
        self._description = DescriptionMetadata.create_description_metadata(text=description,
                                                                            source=description_source) \
            if description else None
        self._node_iterator = self._create_node_iterator()
        self._relation_iterator = self._create_relation_iterator()
        self._record_iterator = self._create_record_iterator()
        self._atlas_entity_iterator = self._create_next_atlas_entity()

    def create_next_node(self) -> Union[GraphNode, None]:
        try:
            return next(self._node_iterator)
        except StopIteration:
            return None

    def _create_node_iterator(self) -> Iterator[GraphNode]:
        node = GraphNode(
            key=self._schema_key,
            label=SCHEMA_NODE_LABEL,
            attributes={
                SCHEMA_NAME_ATTR: self._schema,
            }
        )
        yield node

        if self._description:
            yield self._description.get_node(self._get_description_node_key())

    def create_next_relation(self) -> Union[GraphRelationship, None]:
        try:
            return next(self._relation_iterator)
        except StopIteration:
            return None

    def create_next_record(self) -> Union[RDSModel, None]:
        try:
            return next(self._record_iterator)
        except StopIteration:
            return None

    def _create_record_iterator(self) -> Iterator[RDSModel]:
        schema_record = RDSSchema(
            rk=self._schema_key,
            name=self._schema,
            cluster_rk=self._cluster_key
        )
        yield schema_record

        if self._description:
            if self._description.label == DescriptionMetadata.DESCRIPTION_NODE_LABEL:
                yield RDSSchemaDescription(
                    rk=self._get_description_node_key(),
                    description_source=self._description.source,
                    description=self._description.text,
                    schema_rk=self._schema_key
                )
            else:
                yield RDSSchemaProgrammaticDescription(
                    rk=self._get_description_node_key(),
                    description_source=self._description.source,
                    description=self._description.text,
                    schema_rk=self._schema_key
                )

    def _get_description_node_key(self) -> str:
        desc = self._description.get_description_id() if self._description is not None else ''
        return f'{self._schema_key}/{desc}'

    def _create_relation_iterator(self) -> Iterator[GraphRelationship]:
        if self._description:
            yield self._description.get_relation(start_node=SCHEMA_NODE_LABEL,
                                                 start_key=self._schema_key,
                                                 end_key=self._get_description_node_key())

    def _get_cluster_key(self, schema_key: str) -> str:
        schema_key_pattern = re.compile(SCHEMA_KEY_PATTERN_REGEX)
        schema_key_match = schema_key_pattern.match(schema_key)
        if not schema_key_match:
            raise Exception(f'{schema_key} does not match the schema key pattern')

        cluster_key = schema_key_match.group(1)
        return cluster_key

    def _create_atlas_schema_entity(self) -> AtlasEntity:
        attrs_mapping = [
            (AtlasCommonParams.qualified_name, self._schema_key),
            ('name', self._schema_key),
            ('description', self._description.text if self._description else '')
        ]

        entity_attrs = get_entity_attrs(attrs_mapping)

        # Since Schema cannot exist without Cluster (COMPOSITION relationship type), we assume Schema entity was created
        # by different process and we only update schema description here using UPDATE operation.
        entity = AtlasEntity(
            typeName=AtlasTableTypes.schema,
            operation=AtlasSerializedEntityOperation.UPDATE,
            attributes=entity_attrs,
            relationships=None
        )

        return entity

    def _create_next_atlas_entity(self) -> Iterator[AtlasEntity]:
        yield self._create_atlas_schema_entity()

    def create_next_atlas_entity(self) -> Union[AtlasEntity, None]:
        try:
            return next(self._atlas_entity_iterator)
        except StopIteration:
            return None

    def create_next_atlas_relation(self) -> Union[AtlasRelationship, None]:
        pass
