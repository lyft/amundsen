# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from typing import (
    Iterable, Iterator, Optional, Union,
)

from amundsen_rds.models import RDSModel

from databuilder.models.atlas_entity import AtlasEntity
from databuilder.models.atlas_relationship import AtlasRelationship
from databuilder.models.atlas_serializable import AtlasSerializable
from databuilder.models.graph_node import GraphNode
from databuilder.models.graph_relationship import GraphRelationship
from databuilder.models.graph_serializable import GraphSerializable
from databuilder.models.table_metadata import TableMetadata
from databuilder.models.table_serializable import TableSerializable
from databuilder.models.usage.usage import Usage


class ColumnReader(Usage):
    """
    Represent user's read action on a table - and eventually on a column.
    """

    def __init__(self,
                 database: str,
                 cluster: str,
                 schema: str,
                 table: str,
                 column: str,  # not used: per-column usage not yet implemented
                 user_email: str,
                 read_count: int = 1
                 ) -> None:

        Usage.__init__(
            self,
            start_label=TableMetadata.TABLE_NODE_LABEL,
            start_key=TableMetadata.TABLE_KEY_FORMAT.format(
                db=database,
                cluster=cluster,
                schema=schema,
                tbl=table),
            user_email=user_email,
            read_count=read_count,
        )


class TableColumnUsage(GraphSerializable, TableSerializable, AtlasSerializable):
    """
    Represents an iterable of read actions.
    """

    def __init__(self, col_readers: Iterable[ColumnReader]) -> None:
        self.col_readers = col_readers

        self._node_iterator = self._create_node_iterator()
        self._rel_iter = self._create_rel_iterator()
        self._record_iter = self._create_record_iterator()
        self._atlas_entity_iterator = self._create_next_atlas_entity()
        self._atlas_relation_iterator = self._create_atlas_relation_iterator()

    def create_next_node(self) -> Union[GraphNode, None]:
        try:
            return next(self._node_iterator)
        except StopIteration:
            return None

    def _create_node_iterator(self) -> Iterator[GraphNode]:
        for usage in self.col_readers:
            node = usage.create_next_node()
            while node is not None:
                yield node
                node = usage.create_next_node()

    def create_next_relation(self) -> Union[GraphRelationship, None]:
        try:
            return next(self._rel_iter)
        except StopIteration:
            return None

    def _create_rel_iterator(self) -> Iterator[GraphRelationship]:
        for usage in self.col_readers:
            rel = usage.create_next_relation()
            while rel is not None:
                yield rel
                rel = usage.create_next_relation()

    def create_next_record(self) -> Union[RDSModel, None]:
        try:
            return next(self._record_iter)
        except StopIteration:
            return None

    def _create_record_iterator(self) -> Iterator[RDSModel]:
        for usage in self.col_readers:
            record = usage.create_next_record()
            while record is not None:
                yield record
                record = usage.create_next_record()

    def _create_next_atlas_entity(self) -> Iterator[Optional[AtlasEntity]]:
        for usage in self.col_readers:
            yield usage.create_next_atlas_entity()

    def create_next_atlas_entity(self) -> Union[AtlasEntity, None]:
        try:
            return next(self._atlas_entity_iterator)  # type: ignore
        except StopIteration:
            return None

    def create_next_atlas_relation(self) -> Union[AtlasRelationship, None]:
        try:
            return next(self._atlas_relation_iterator)  # type: ignore
        except StopIteration:
            return None

    def _create_atlas_relation_iterator(self) -> Iterator[Optional[AtlasRelationship]]:
        for usage in self.col_readers:
            yield usage.create_next_atlas_relation()

    def __repr__(self) -> str:
        return f'TableColumnUsage(col_readers={self.col_readers!r})'
