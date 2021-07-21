# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import logging
from typing import (
    Any, Iterator, Optional, Union,
)

from amundsen_rds.models import RDSModel
from amundsen_rds.models.dashboard import DashboardExecution as RDSDashboardExecution

from databuilder.models.dashboard.dashboard_metadata import DashboardMetadata
from databuilder.models.graph_node import GraphNode
from databuilder.models.graph_relationship import GraphRelationship
from databuilder.models.graph_serializable import GraphSerializable
from databuilder.models.table_serializable import TableSerializable

LOGGER = logging.getLogger(__name__)


class DashboardExecution(GraphSerializable, TableSerializable):
    """
    A model that encapsulate Dashboard's execution timestamp in epoch and execution state
    """
    DASHBOARD_EXECUTION_LABEL = 'Execution'
    DASHBOARD_EXECUTION_KEY_FORMAT = '{product}_dashboard://{cluster}.{dashboard_group_id}/' \
                                     '{dashboard_id}/execution/{execution_id}'
    DASHBOARD_EXECUTION_RELATION_TYPE = 'EXECUTED'
    EXECUTION_DASHBOARD_RELATION_TYPE = 'EXECUTION_OF'

    LAST_EXECUTION_ID = '_last_execution'
    LAST_SUCCESSFUL_EXECUTION_ID = '_last_successful_execution'

    def __init__(self,
                 dashboard_group_id: Optional[str],
                 dashboard_id: Optional[str],
                 execution_timestamp: int,
                 execution_state: str,
                 execution_id: str = LAST_EXECUTION_ID,
                 product: Optional[str] = '',
                 cluster: str = 'gold',
                 **kwargs: Any
                 ) -> None:
        self._dashboard_group_id = dashboard_group_id
        self._dashboard_id = dashboard_id
        self._execution_timestamp = execution_timestamp
        self._execution_state = execution_state
        self._execution_id = execution_id
        self._product = product
        self._cluster = cluster
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
            key=self._get_last_execution_node_key(),
            label=DashboardExecution.DASHBOARD_EXECUTION_LABEL,
            attributes={
                'timestamp': self._execution_timestamp,
                'state': self._execution_state
            }
        )
        yield node

    def create_next_relation(self) -> Union[GraphRelationship, None]:
        try:
            return next(self._relation_iterator)
        except StopIteration:
            return None

    def _create_relation_iterator(self) -> Iterator[GraphRelationship]:
        relationship = GraphRelationship(
            start_label=DashboardMetadata.DASHBOARD_NODE_LABEL,
            start_key=DashboardMetadata.DASHBOARD_KEY_FORMAT.format(
                product=self._product,
                cluster=self._cluster,
                dashboard_group=self._dashboard_group_id,
                dashboard_name=self._dashboard_id
            ),
            end_label=DashboardExecution.DASHBOARD_EXECUTION_LABEL,
            end_key=self._get_last_execution_node_key(),
            type=DashboardExecution.DASHBOARD_EXECUTION_RELATION_TYPE,
            reverse_type=DashboardExecution.EXECUTION_DASHBOARD_RELATION_TYPE,
            attributes={}
        )
        yield relationship

    def create_next_record(self) -> Union[RDSModel, None]:
        try:
            return next(self._record_iterator)
        except StopIteration:
            return None

    def _create_record_iterator(self) -> Iterator[RDSModel]:
        yield RDSDashboardExecution(
            rk=self._get_last_execution_node_key(),
            timestamp=self._execution_timestamp,
            state=self._execution_state,
            dashboard_rk=DashboardMetadata.DASHBOARD_KEY_FORMAT.format(
                product=self._product,
                cluster=self._cluster,
                dashboard_group=self._dashboard_group_id,
                dashboard_name=self._dashboard_id
            )
        )

    def _get_last_execution_node_key(self) -> str:
        return DashboardExecution.DASHBOARD_EXECUTION_KEY_FORMAT.format(
            product=self._product,
            cluster=self._cluster,
            dashboard_group_id=self._dashboard_group_id,
            dashboard_id=self._dashboard_id,
            execution_id=self._execution_id
        )

    def __repr__(self) -> str:
        return f'DashboardExecution({self._dashboard_group_id!r}, {self._dashboard_id!r}, ' \
               f'{self._execution_timestamp!r}, {self._execution_state!r}, ' \
               f'{self._execution_id!r}, {self._product!r}, {self._cluster!r})'
