# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import re
from typing import (
    Any, Iterator, Union,
)

from amundsen_rds.models import RDSModel
from amundsen_rds.models.schema import (
    Schema as RDSSchema, SchemaDescription as RDSSchemaDescription,
    SchemaProgrammaticDescription as RDSSchemaProgrammaticDescription,
)

from databuilder.models.graph_node import GraphNode
from databuilder.models.graph_relationship import GraphRelationship
from databuilder.models.graph_serializable import GraphSerializable
from databuilder.models.schema.schema_constant import (
    SCHEMA_KEY_PATTERN_REGEX, SCHEMA_NAME_ATTR, SCHEMA_NODE_LABEL,
)
from databuilder.models.table_metadata import DescriptionMetadata
from databuilder.models.table_serializable import TableSerializable


class SchemaModel(GraphSerializable, TableSerializable):
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
