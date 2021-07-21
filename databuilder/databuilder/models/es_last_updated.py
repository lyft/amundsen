# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from typing import Iterator, Union

from amundsen_rds.models import RDSModel
from amundsen_rds.models.updated_timestamp import UpdatedTimestamp as RDSUpdatedTimestamp

from databuilder.models.graph_node import GraphNode
from databuilder.models.graph_relationship import GraphRelationship
from databuilder.models.graph_serializable import GraphSerializable
from databuilder.models.table_serializable import TableSerializable


class ESLastUpdated(GraphSerializable, TableSerializable):
    """
    Data model to keep track the last updated timestamp for
    datastore and es.
    """

    LABEL = 'Updatedtimestamp'
    KEY = 'amundsen_updated_timestamp'
    LATEST_TIMESTAMP = 'latest_timestamp'

    def __init__(self,
                 timestamp: int,
                 ) -> None:
        """
        :param timestamp: epoch for latest updated timestamp for neo4j an es
        """
        self.timestamp = timestamp
        self._node_iter = self._create_node_iterator()
        self._rel_iter = self._create_relation_iterator()
        self._record_iter = self._create_record_iterator()

    def create_next_node(self) -> Union[GraphNode, None]:
        """
        Will create an orphan node for last updated timestamp.
        """
        try:
            return next(self._node_iter)
        except StopIteration:
            return None

    def _create_node_iterator(self) -> Iterator[GraphNode]:
        """
        Create an es_updated_timestamp node
        """
        node = GraphNode(
            key=ESLastUpdated.KEY,
            label=ESLastUpdated.LABEL,
            attributes={
                ESLastUpdated.LATEST_TIMESTAMP: self.timestamp
            }
        )
        yield node

    def create_next_relation(self) -> Union[GraphRelationship, None]:
        try:
            return next(self._rel_iter)
        except StopIteration:
            return None

    def _create_relation_iterator(self) -> Iterator[GraphRelationship]:
        return
        yield

    def create_next_record(self) -> Union[RDSModel, None]:
        try:
            return next(self._record_iter)
        except StopIteration:
            return None

    def _create_record_iterator(self) -> Iterator[RDSModel]:
        record = RDSUpdatedTimestamp(rk=ESLastUpdated.KEY,
                                     latest_timestamp=self.timestamp)
        yield record
