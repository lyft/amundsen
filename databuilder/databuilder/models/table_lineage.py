# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from abc import abstractmethod
from typing import (
    Iterator, List, Union,
)

from databuilder.models.graph_node import GraphNode
from databuilder.models.graph_relationship import GraphRelationship
from databuilder.models.graph_serializable import GraphSerializable
from databuilder.models.table_metadata import ColumnMetadata, TableMetadata


class BaseLineage(GraphSerializable):
    """
    Generic Lineage Interface
    """
    LABEL = 'Lineage'
    ORIGIN_DEPENDENCY_RELATION_TYPE = 'HAS_DOWNSTREAM'
    DEPENDENCY_ORIGIN_RELATION_TYPE = 'HAS_UPSTREAM'

    def __init__(self) -> None:
        self._node_iter = self._create_node_iterator()
        self._relation_iter = self._create_rel_iterator()

    def create_next_node(self) -> Union[GraphNode, None]:
        # return the string representation of the data
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
        """
        It won't create any node for this model
        :return:
        """
        return
        yield

    @abstractmethod
    def _create_rel_iterator(self) -> Iterator[GraphRelationship]:
        pass


class TableLineage(BaseLineage):
    """
    Table Lineage Model. It won't create nodes but create upstream/downstream rels.
    """

    def __init__(self,
                 table_key: str,
                 downstream_deps: List = None,  # List of table keys
                 ) -> None:
        self.table_key = table_key
        # a list of downstream dependencies, each of which will follow
        # the same key
        self.downstream_deps = downstream_deps or []
        super().__init__()

    def _create_rel_iterator(self) -> Iterator[GraphRelationship]:
        """
        Create relations between source table and all the downstream tables
        :return:
        """
        for downstream_key in self.downstream_deps:
            relationship = GraphRelationship(
                start_key=self.table_key,
                start_label=TableMetadata.TABLE_NODE_LABEL,
                end_label=TableMetadata.TABLE_NODE_LABEL,
                end_key=downstream_key,
                type=TableLineage.ORIGIN_DEPENDENCY_RELATION_TYPE,
                reverse_type=TableLineage.DEPENDENCY_ORIGIN_RELATION_TYPE,
                attributes={}
            )
            yield relationship

    def __repr__(self) -> str:
        return f'TableLineage({self.table_key!r})'


class ColumnLineage(BaseLineage):
    """
    Column Lineage Model. It won't create nodes but create upstream/downstream rels.
    """
    def __init__(self,
                 column_key: str,
                 downstream_deps: List = None,  # List of column keys
                 ) -> None:
        self.column_key = column_key
        # a list of downstream dependencies, each of which will follow
        # the same key
        self.downstream_deps = downstream_deps or []
        super().__init__()

    def _create_rel_iterator(self) -> Iterator[GraphRelationship]:
        """
        Create relations between source column and all the downstream columns
        :return:
        """
        for downstream_key in self.downstream_deps:
            relationship = GraphRelationship(
                start_key=self.column_key,
                start_label=ColumnMetadata.COLUMN_NODE_LABEL,
                end_label=ColumnMetadata.COLUMN_NODE_LABEL,
                end_key=downstream_key,
                type=ColumnLineage.ORIGIN_DEPENDENCY_RELATION_TYPE,
                reverse_type=ColumnLineage.DEPENDENCY_ORIGIN_RELATION_TYPE,
                attributes={}
            )
            yield relationship

    def __repr__(self) -> str:
        return f'ColumnLineage({self.column_key!r})'
