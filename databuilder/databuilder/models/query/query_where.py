# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import hashlib
from typing import (
    Iterator, List, Optional,
)

from databuilder.models.graph_node import GraphNode
from databuilder.models.graph_relationship import GraphRelationship
from databuilder.models.query.base import QueryBase
from databuilder.models.query.query import QueryMetadata
from databuilder.models.table_metadata import ColumnMetadata, TableMetadata


class QueryWhereMetadata(QueryBase):
    """
    A Where clause used on a query.
    """
    NODE_LABEL = 'Where'
    KEY_FORMAT = '{table_hash}-{where_hash}'

    # Relation between table and query
    COLUMN_WHERE_RELATION_TYPE = 'USES_WHERE_CLAUSE'
    INVERSE_COLUMN_WHERE_RELATION_TYPE = 'WHERE_CLAUSE_USED_ON'

    QUERY_WHERE_RELATION_TYPE = 'HAS_WHERE_CLAUSE'
    INVERSE_QUERY_WHERE_RELATION_TYPE = 'WHERE_CLAUSE_OF'

    # Node attributes
    WHERE_CLAUSE = 'where_clause'
    LEFT_ARG = 'left_arg'
    RIGHT_ARG = 'right_arg'
    OPERATOR = 'operator'
    ALIAS_MAPPING = 'alias_mapping'

    def __init__(self,
                 tables: List[TableMetadata],
                 where_clause: str,
                 left_arg: Optional[str],
                 right_arg: Optional[str],
                 operator: Optional[str],
                 query_metadata: Optional[QueryMetadata] = None,
                 yield_relation_nodes: bool = False):
        """
        :param tables: List of table meteadata objects corresponding to tables in this where clause
        :param where_clause: a sting representation of the SQL where clause
        :param left_arg: An optional string representing the left side of the where cause, e.g.
            in the clause (where x < 3), this would be "x"
        :param operator: An optional string representing the operator in the where cause, e.g.
            in the clause (where x < 3), this would be "<"
        :param right_arg: An optional string representing the right side of the where cause, e.g.
            in the clause (where x < 3), this would be "3"
        :param query_metadata: The Query metadata object that this where clause belongs to, this
            is optional to allow creating static QueryWhereMetadata objects to show on tables
            without the complexity of creating QueryMetadata
        :param yield_relation_nodes: A boolean, indicating whether or not the query metadata
            and tables associated to this Where should have nodes created if they does not
            already exist.
        """
        self.tables = tables
        self.query_metadata = query_metadata
        self.where_clause = where_clause
        self.left_arg = left_arg
        self.right_arg = right_arg
        self.operator = operator
        self.yield_relation_nodes = yield_relation_nodes
        self._table_hash = self._get_table_hash(self.tables)
        self._where_hash = self._get_where_hash(self.where_clause)
        self._node_iter = self._create_next_node()
        self._relation_iter = self._create_relation_iterator()

    def __repr__(self) -> str:
        tbl_str = self.tables[0]._get_table_key()
        if len(self.tables) > 1:
            tbl_str += f' + {len(self.tables) - 1} other tables'
        return f'QueryWhereMetadata(Table: {tbl_str}, {self.where_clause[:25]})'

    def _get_table_hash(self, tables: List[TableMetadata]) -> str:
        """
        Generates a unique hash for a set of tables that are associated to a where clause. Since
        we do not want multiple instances of this where clause represented in the database we may
        need to link mulitple tables to this where clause. We do this by creating a single, unique
        key across multiple tables by concatenating all of the table keys together and creating a
        hash (to shorten the value).
        """
        tbl_keys = ''.join(list(sorted([t._get_table_key() for t in tables])))
        return hashlib.md5(tbl_keys.encode('utf-8')).hexdigest()

    def _get_where_hash(self, where_clause: str) -> str:
        """
        Generates a unique hash for a where clause.
        """
        sql_no_fmt = self._normalize(where_clause)
        return hashlib.md5(sql_no_fmt.encode('utf-8')).hexdigest()

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
    def get_key(table_hash: str, where_hash: str) -> str:
        return QueryWhereMetadata.KEY_FORMAT.format(table_hash=table_hash, where_hash=where_hash)

    def get_key_self(self) -> str:
        return QueryWhereMetadata.get_key(table_hash=self._table_hash, where_hash=self._where_hash)

    def get_query_relations(self) -> Iterator[GraphRelationship]:
        for table in self.tables:
            for col in table.columns:
                yield GraphRelationship(
                    start_label=ColumnMetadata.COLUMN_NODE_LABEL,
                    end_label=self.NODE_LABEL,
                    start_key=table._get_col_key(col),
                    end_key=self.get_key_self(),
                    type=self.COLUMN_WHERE_RELATION_TYPE,
                    reverse_type=self.INVERSE_COLUMN_WHERE_RELATION_TYPE,
                    attributes={}
                )

        # Optional Query to Where Clause
        if self.query_metadata:
            yield GraphRelationship(
                start_label=QueryMetadata.NODE_LABEL,
                end_label=self.NODE_LABEL,
                start_key=self.query_metadata.get_key_self(),
                end_key=self.get_key_self(),
                type=self.QUERY_WHERE_RELATION_TYPE,
                reverse_type=self.INVERSE_QUERY_WHERE_RELATION_TYPE,
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
                self.WHERE_CLAUSE: self.where_clause,
                self.LEFT_ARG: self.left_arg,
                self.RIGHT_ARG: self.right_arg,
                self.OPERATOR: self.operator
            }
        )
        if self.yield_relation_nodes:
            for table in self.tables:
                for tbl_item in table._create_next_node():
                    yield tbl_item
            if self.query_metadata:
                for query_item in self.query_metadata._create_next_node():
                    yield query_item

    def _create_relation_iterator(self) -> Iterator[GraphRelationship]:
        relations = self.get_query_relations()
        for relation in relations:
            yield relation

        if self.yield_relation_nodes:
            for table in self.tables:
                for tbl_rel in table._create_next_relation():
                    yield tbl_rel
            if self.query_metadata:
                for query_rel in self.query_metadata._create_relation_iterator():
                    yield query_rel
