# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import logging
from typing import (
    Any, Iterator, Optional, Union,
)

from amundsen_common.utils.atlas import AtlasCommonParams, AtlasDashboardTypes
from amundsen_rds.models import RDSModel
from amundsen_rds.models.dashboard import DashboardTimestamp as RDSDashboardTimestamp

from databuilder.models.atlas_entity import AtlasEntity
from databuilder.models.atlas_relationship import AtlasRelationship
from databuilder.models.atlas_serializable import AtlasSerializable
from databuilder.models.dashboard.dashboard_metadata import DashboardMetadata
from databuilder.models.graph_node import GraphNode
from databuilder.models.graph_relationship import GraphRelationship
from databuilder.models.graph_serializable import GraphSerializable
from databuilder.models.table_serializable import TableSerializable
from databuilder.models.timestamp import timestamp_constants
from databuilder.serializers.atlas_serializer import get_entity_attrs
from databuilder.utils.atlas import AtlasSerializedEntityOperation

LOGGER = logging.getLogger(__name__)


class DashboardLastModifiedTimestamp(GraphSerializable, TableSerializable, AtlasSerializable):
    """
    A model that encapsulate Dashboard's last modified timestamp in epoch
    """

    DASHBOARD_LAST_MODIFIED_KEY_FORMAT = '{product}_dashboard://{cluster}.{dashboard_group_id}/' \
                                         '{dashboard_id}/_last_modified_timestamp'

    def __init__(self,
                 dashboard_group_id: Optional[str],
                 dashboard_id: Optional[str],
                 last_modified_timestamp: int,
                 product: Optional[str] = '',
                 cluster: str = 'gold',
                 **kwargs: Any
                 ) -> None:
        self._dashboard_group_id = dashboard_group_id
        self._dashboard_id = dashboard_id
        self._last_modified_timestamp = last_modified_timestamp
        self._product = product
        self._cluster = cluster
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
        node_attributes = {
            timestamp_constants.TIMESTAMP_PROPERTY: self._last_modified_timestamp,
            timestamp_constants.TIMESTAMP_NAME_PROPERTY: timestamp_constants.TimestampName.last_updated_timestamp.name
        }
        node = GraphNode(
            key=self._get_last_modified_node_key(),
            label=timestamp_constants.NODE_LABEL,
            attributes=node_attributes
        )
        yield node

    def create_next_relation(self) -> Union[GraphRelationship, None]:
        try:
            return next(self._relation_iterator)
        except StopIteration:
            return None

    def _create_relation_iterator(self) -> Iterator[GraphRelationship]:
        relationship = GraphRelationship(
            start_key=DashboardMetadata.DASHBOARD_KEY_FORMAT.format(
                product=self._product,
                cluster=self._cluster,
                dashboard_group=self._dashboard_group_id,
                dashboard_name=self._dashboard_id
            ),
            start_label=DashboardMetadata.DASHBOARD_NODE_LABEL,
            end_key=self._get_last_modified_node_key(),
            end_label=timestamp_constants.NODE_LABEL,
            type=timestamp_constants.LASTUPDATED_RELATION_TYPE,
            reverse_type=timestamp_constants.LASTUPDATED_REVERSE_RELATION_TYPE,
            attributes={}
        )
        yield relationship

    def create_next_atlas_entity(self) -> Union[AtlasEntity, None]:
        try:
            return next(self._atlas_entity_iterator)
        except StopIteration:
            return None

    def _create_next_atlas_entity(self) -> Iterator[AtlasEntity]:

        # last modified
        attrs_mapping = [
            (
                AtlasCommonParams.qualified_name, DashboardMetadata.DASHBOARD_KEY_FORMAT.format(
                    product=self._product,
                    cluster=self._cluster,
                    dashboard_group=self._dashboard_group_id,
                    dashboard_name=self._dashboard_id
                )
            ),
            (AtlasCommonParams.last_modified_timestamp, self._last_modified_timestamp),
        ]

        dashboard_entity_attrs = get_entity_attrs(attrs_mapping)

        last_modified = AtlasEntity(
            typeName=AtlasDashboardTypes.metadata,
            operation=AtlasSerializedEntityOperation.UPDATE,
            relationships=None,
            attributes=dashboard_entity_attrs
        )
        yield last_modified

    def create_next_atlas_relation(self) -> Union[AtlasRelationship, None]:
        return None

    def create_next_record(self) -> Union[RDSModel, None]:
        try:
            return next(self._record_iterator)
        except StopIteration:
            return None

    def _create_record_iterator(self) -> Iterator[RDSModel]:
        yield RDSDashboardTimestamp(
            rk=self._get_last_modified_node_key(),
            timestamp=self._last_modified_timestamp,
            name=timestamp_constants.TimestampName.last_updated_timestamp.name,
            dashboard_rk=DashboardMetadata.DASHBOARD_KEY_FORMAT.format(
                product=self._product,
                cluster=self._cluster,
                dashboard_group=self._dashboard_group_id,
                dashboard_name=self._dashboard_id
            )
        )

    def _get_last_modified_node_key(self) -> str:
        return DashboardLastModifiedTimestamp.DASHBOARD_LAST_MODIFIED_KEY_FORMAT.format(
            product=self._product,
            cluster=self._cluster,
            dashboard_group_id=self._dashboard_group_id,
            dashboard_id=self._dashboard_id,
        )

    def __repr__(self) -> str:
        return f'DashboardLastModifiedTimestamp({self._dashboard_group_id!r}, {self._dashboard_id!r}, ' \
               f'{self._last_modified_timestamp!r}, {self._product!r}, {self._cluster!r})'
