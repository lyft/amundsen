# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from typing import Iterator, Optional

from databuilder.models.graph_node import GraphNode
from databuilder.models.graph_relationship import GraphRelationship
from databuilder.models.graph_serializable import GraphSerializable
from databuilder.models.query.query import QueryMetadata
from databuilder.models.table_metadata import ColumnMetadata, TableMetadata


class QueryJoinMetadata(GraphSerializable):
    """
    A Join clause used between two tables within a query
    """
    NODE_LABEL = 'Join'
    KEY_FORMAT = '{join_type}-{left_column_key}-{operator}-{right_column_key}'

    # Relation between entity and query
    COLUMN_JOIN_RELATION_TYPE = 'COLUMN_JOINS_WITH'
    INVERSE_COLUMN_JOIN_RELATION_TYPE = 'JOIN_OF_COLUMN'

    QUERY_JOIN_RELATION_TYPE = 'QUERY_JOINS_WITH'
    INVERSE_QUERY_JOIN_RELATION_TYPE = 'JOIN_OF_QUERY'

    # Node attributes
    JOIN_TYPE = 'join_type'
    JOIN_OPERATOR = 'operator'
    JOIN_SQL = 'join_sql'
    LEFT_TABLE_KEY = 'left_table_key'
    LEFT_DATABASE = 'left_database'
    LEFT_CLUSTER = 'left_cluster'
    LEFT_SCHEMA = 'left_schema'
    LEFT_TABLE = 'left_table'
    RIGHT_TABLE_KEY = 'right_table_key'
    RIGHT_DATABASE = 'right_database'
    RIGHT_CLUSTER = 'right_cluster'
    RIGHT_SCHEMA = 'right_schema'
    RIGHT_TABLE = 'right_table'

    def __init__(self,
                 left_table: TableMetadata,
                 right_table: TableMetadata,
                 left_column: ColumnMetadata,
                 right_column: ColumnMetadata,
                 join_type: str,
                 join_operator: str,
                 join_sql: str,
                 query_metadata: Optional[QueryMetadata] = None,
                 yield_relation_nodes: bool = False):
        """
        :param left_table: The table joined on the left side of the join clause
        :param right_table: The table joined on the right side of the join clause
        :param left_column: The column from the left table used in the join
        :param right_column: The column from the right table used in the join
        :param join_type: A free form string representing the type of join, examples
            include: inner join, right join, full join, etc.
        :param join_operator: The operator used in the join, examples include: =, >, etc.
        :param query_metadata: The Query metadata object that this where clause belongs to, this
            is optional to allow creating static QueryJoinMetadata objects to show on tables
            without the complexity of creating QueryMetadata
        :param yield_relation_nodes: A boolean, indicating whether or not the query metadata
            and tables associated to this Join should have nodes created if they does not
            already exist.
        """
        # For inner joins we don't want to duplicate joins if the other table
        # comes first in the join clause since it produces the same effect.
        # This ONLY applies to inner join and you may need to massage your data
        # for join_type to have the proper value
        swap_left_right = False
        if join_operator == '=' and join_type == 'inner join':
            tables_sorted = sorted([left_table._get_table_key(), right_table._get_table_key()])
            if tables_sorted[0] == right_table:
                swap_left_right = True

        self.left_table = right_table if swap_left_right else left_table
        self.right_table = left_table if swap_left_right else right_table
        self.left_column = right_column if swap_left_right else left_column
        self.right_column = left_column if swap_left_right else right_column

        self.join_type = join_type
        self.join_operator = join_operator
        self.join_sql = join_sql
        self.query_metadata = query_metadata
        self.yield_relation_nodes = yield_relation_nodes
        self._node_iter = self._create_next_node()
        self._relation_iter = self._create_relation_iterator()

    def __repr__(self) -> str:
        return (
            f'QueryJoinMetadata(Left Table: {self.left_table._get_table_key()}, '
            f'Right Table: {self.left_table._get_table_key()})'
        )

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

    @staticmethod
    def get_key(left_column_key: str, right_column_key: str, join_type: str, operator: str) -> str:
        join_no_space = join_type.replace(' ', '-')
        return QueryJoinMetadata.KEY_FORMAT.format(left_column_key=left_column_key,
                                                   right_column_key=right_column_key,
                                                   join_type=join_no_space,
                                                   operator=operator)

    def get_key_self(self) -> str:
        return QueryJoinMetadata.get_key(left_column_key=self.left_table._get_col_key(col=self.left_column),
                                         right_column_key=self.right_table._get_col_key(col=self.right_column),
                                         join_type=self.join_type,
                                         operator=self.join_operator)

    def get_query_relations(self) -> Iterator[GraphRelationship]:

        # Left Column
        yield GraphRelationship(
            start_label=ColumnMetadata.COLUMN_NODE_LABEL,
            end_label=self.NODE_LABEL,
            start_key=self.left_table._get_col_key(col=self.left_column),
            end_key=self.get_key_self(),
            type=self.COLUMN_JOIN_RELATION_TYPE,
            reverse_type=self.INVERSE_COLUMN_JOIN_RELATION_TYPE,
            attributes={}
        )

        # Right Column
        yield GraphRelationship(
            start_label=ColumnMetadata.COLUMN_NODE_LABEL,
            end_label=self.NODE_LABEL,
            start_key=self.right_table._get_col_key(col=self.right_column),
            end_key=self.get_key_self(),
            type=self.COLUMN_JOIN_RELATION_TYPE,
            reverse_type=self.INVERSE_COLUMN_JOIN_RELATION_TYPE,
            attributes={}
        )

        if self.query_metadata:
            yield GraphRelationship(
                start_label=QueryMetadata.NODE_LABEL,
                end_label=self.NODE_LABEL,
                start_key=self.query_metadata.get_key_self(),
                end_key=self.get_key_self(),
                type=self.QUERY_JOIN_RELATION_TYPE,
                reverse_type=self.INVERSE_QUERY_JOIN_RELATION_TYPE,
                attributes={}
            )

    def _create_next_node(self) -> Iterator[GraphNode]:
        """
        Create query nodes
        :return:
        """
        yield GraphNode(
            key=self.get_key_self(),
            label=self.NODE_LABEL,
            attributes={
                self.JOIN_TYPE: self.join_type,
                self.JOIN_OPERATOR: self.join_operator,
                self.JOIN_SQL: self.join_sql,
                self.LEFT_TABLE_KEY: self.left_table._get_table_key(),
                self.LEFT_DATABASE: self.left_table.database,
                self.LEFT_CLUSTER: self.left_table.cluster,
                self.LEFT_SCHEMA: self.left_table.schema,
                self.LEFT_TABLE: self.left_table.name,
                self.RIGHT_TABLE_KEY: self.right_table._get_table_key(),
                self.RIGHT_DATABASE: self.right_table.database,
                self.RIGHT_CLUSTER: self.right_table.cluster,
                self.RIGHT_SCHEMA: self.right_table.schema,
                self.RIGHT_TABLE: self.right_table.name
            }
        )

        if self.yield_relation_nodes:
            for l_tbl_item in self.left_table._create_next_node():
                yield l_tbl_item
            for r_tbl_item in self.right_table._create_next_node():
                yield r_tbl_item
            if self.query_metadata:
                for query_item in self.query_metadata._create_next_node():
                    yield query_item

    def _create_relation_iterator(self) -> Iterator[GraphRelationship]:
        relations = self.get_query_relations()
        for relation in relations:
            yield relation

        if self.yield_relation_nodes:
            for l_tbl_rel in self.left_table._create_next_relation():
                yield l_tbl_rel
            for r_tbl_rel in self.right_table._create_next_relation():
                yield r_tbl_rel
            if self.query_metadata:
                for query_rel in self.query_metadata._create_relation_iterator():
                    yield query_rel
