# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from typing import (
    Iterator, Optional, Union,
)

from databuilder.models.graph_node import GraphNode
from databuilder.models.graph_relationship import GraphRelationship
from databuilder.models.graph_serializable import GraphSerializable
from databuilder.models.query.query import QueryMetadata


class QueryExecutionsMetadata(GraphSerializable):
    """
    The Amundsen Query Executions model represents an aggregation for the number
    of times a query was executed within a given time window.

    Query executions are aggregated to time window to enable easily adding and
    dropping new query execution aggregations without having to maintain
    all instances that a query was executed in the database. Query Executions only
    contain a start time and a window duration, although the window duration is
    only used for informational purposes. Amundsen does not apply validation that
    query executions do not overlap, therefore, it is important that any implementation
    of a query execution is able to deterministically retrieve non-overlapping queries
    between data builder runs.
    """
    NODE_LABEL = 'Execution'
    KEY_FORMAT = '{query_key}-{start_time}'

    # Relation between entity and query
    QUERY_EXECUTION_RELATION_TYPE = 'HAS_EXECUTION'
    INVERSE_QUERY_EXECUTION_RELATION_TYPE = 'EXECUTION_OF'

    # Execution window ENUMs
    EXECUTION_WINDOW_HOURLY = 'hourly'
    EXECUTION_WINDOW_DAILY = 'daily'
    EXECUTION_WINDOW_WEEKLY = 'weekly'

    # Attributes
    START_TIME = 'start_time'
    EXECUTION_COUNT = 'execution_count'
    WINDOW_DURATION = 'window_duration'

    def __init__(self,
                 query_metadata: QueryMetadata,
                 start_time: int,
                 execution_count: int,
                 window_duration: str = EXECUTION_WINDOW_DAILY,     # Purely for descriptive purposes
                 yield_relation_nodes: bool = False
                 ):
        """
        :param query_metadata: The Query metadata object that this execution belongs to
        :param start_time: The time the query execution window started. This should
            consistently be supplied as either seconds or milliseconds since epoch.
        :param execution_count: The count of the number of times this query was executed
            within the window
        :param window_duration: A description of the window duration, e.g. daily, hourly
        :param yield_relation_nodes: A boolean, indicating whether or not the query
            associated to this execution should have it's node created if it does not
            already exist.
        """
        self.query_metadata = query_metadata
        self.start_time = start_time
        self.execution_count = execution_count
        self.window_duration = window_duration
        self.yield_relation_nodes = yield_relation_nodes
        self._node_iter = self._create_next_node()
        self._relation_iter = self._create_relation_iterator()

    def __repr__(self) -> str:
        return (
            f'QueryExecutionsMetadata(Query: {self.query_metadata.get_key_self()}, Start Time: {self.start_time}, '
            f'Window Duration: {self.window_duration}, Count: {self.execution_count})'
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
    def get_key(query_key: str, start_time: Union[str, int]) -> str:
        return QueryExecutionsMetadata.KEY_FORMAT.format(query_key=query_key, start_time=start_time)

    def get_key_self(self) -> str:
        return QueryExecutionsMetadata.get_key(query_key=self.query_metadata.get_key_self(), start_time=self.start_time)

    def get_query_relations(self) -> Iterator[GraphRelationship]:
        yield GraphRelationship(
            start_label=QueryMetadata.NODE_LABEL,
            end_label=self.NODE_LABEL,
            start_key=self.query_metadata.get_key_self(),
            end_key=self.get_key_self(),
            type=self.QUERY_EXECUTION_RELATION_TYPE,
            reverse_type=self.INVERSE_QUERY_EXECUTION_RELATION_TYPE,
            attributes={}
        )

    def _create_next_node(self) -> Iterator[GraphNode]:
        """
        Create query nodes
        :return:
        """
        # TODO: Should query metadata yiled tables as well? Otherwise if a table does not exist
        # before this script is ran then the query relatoinship will not get created.
        # Ideally this relationship wouldn't be "lost" but created once the table is created as well.
        yield GraphNode(
            key=self.get_key_self(),
            label=self.NODE_LABEL,
            attributes={
                self.START_TIME: self.start_time,
                self.EXECUTION_COUNT: self.execution_count,
                self.WINDOW_DURATION: self.window_duration,
            }
        )
        if self.yield_relation_nodes and self.query_metadata:
            for query_item in self.query_metadata._create_next_node():
                yield query_item

    def _create_relation_iterator(self) -> Iterator[GraphRelationship]:
        relations = self.get_query_relations()
        for relation in relations:
            yield relation

        if self.yield_relation_nodes and self.query_metadata:
            for query_rel in self.query_metadata._create_relation_iterator():
                yield query_rel
