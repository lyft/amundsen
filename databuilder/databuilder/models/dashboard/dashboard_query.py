# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import logging
from typing import (
    Any, Iterator, Optional, Union,
)

from amundsen_common.utils.atlas import AtlasCommonParams, AtlasDashboardTypes
from amundsen_rds.models import RDSModel
from amundsen_rds.models.dashboard import DashboardQuery as RDSDashboardQuery

from databuilder.models.atlas_entity import AtlasEntity
from databuilder.models.atlas_relationship import AtlasRelationship
from databuilder.models.atlas_serializable import AtlasSerializable
from databuilder.models.dashboard.dashboard_metadata import DashboardMetadata
from databuilder.models.graph_node import GraphNode
from databuilder.models.graph_relationship import GraphRelationship
from databuilder.models.graph_serializable import GraphSerializable
from databuilder.models.table_serializable import TableSerializable
from databuilder.serializers.atlas_serializer import (
    add_entity_relationship, get_entity_attrs, get_entity_relationships,
)
from databuilder.utils.atlas import AtlasSerializedEntityOperation

LOGGER = logging.getLogger(__name__)


class DashboardQuery(GraphSerializable, TableSerializable, AtlasSerializable):
    """
    A model that encapsulate Dashboard's query name
    """
    DASHBOARD_QUERY_LABEL = 'Query'
    DASHBOARD_QUERY_KEY_FORMAT = '{product}_dashboard://{cluster}.{dashboard_group_id}/' \
                                 '{dashboard_id}/query/{query_id}'
    DASHBOARD_QUERY_RELATION_TYPE = 'HAS_QUERY'
    QUERY_DASHBOARD_RELATION_TYPE = 'QUERY_OF'

    def __init__(self,
                 dashboard_group_id: Optional[str],
                 dashboard_id: Optional[str],
                 query_name: str,
                 query_id: Optional[str] = None,
                 url: Optional[str] = '',
                 query_text: Optional[str] = None,
                 product: Optional[str] = '',
                 cluster: str = 'gold',
                 **kwargs: Any
                 ) -> None:
        self._dashboard_group_id = dashboard_group_id
        self._dashboard_id = dashboard_id
        self._query_name = query_name
        self._query_id = query_id if query_id else query_name
        self._url = url
        self._query_text = query_text
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
            'id': self._query_id,
            'name': self._query_name,
        }

        if self._url:
            node_attributes['url'] = self._url

        if self._query_text:
            node_attributes['query_text'] = self._query_text

        node = GraphNode(
            key=self._get_query_node_key(),
            label=DashboardQuery.DASHBOARD_QUERY_LABEL,
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
            start_label=DashboardMetadata.DASHBOARD_NODE_LABEL,
            end_label=DashboardQuery.DASHBOARD_QUERY_LABEL,
            start_key=DashboardMetadata.DASHBOARD_KEY_FORMAT.format(
                product=self._product,
                cluster=self._cluster,
                dashboard_group=self._dashboard_group_id,
                dashboard_name=self._dashboard_id
            ),
            end_key=self._get_query_node_key(),
            type=DashboardQuery.DASHBOARD_QUERY_RELATION_TYPE,
            reverse_type=DashboardQuery.QUERY_DASHBOARD_RELATION_TYPE,
            attributes={}
        )
        yield relationship

    def create_next_record(self) -> Union[RDSModel, None]:
        try:
            return next(self._record_iterator)
        except StopIteration:
            return None

    def _create_record_iterator(self) -> Iterator[RDSModel]:
        record = RDSDashboardQuery(
            rk=self._get_query_node_key(),
            id=self._query_id,
            name=self._query_name,
            dashboard_rk=DashboardMetadata.DASHBOARD_KEY_FORMAT.format(
                product=self._product,
                cluster=self._cluster,
                dashboard_group=self._dashboard_group_id,
                dashboard_name=self._dashboard_id
            )
        )
        if self._url:
            record.url = self._url
        if self._query_text:
            record.query_text = self._query_text

        yield record

    def _get_query_node_key(self) -> str:
        return DashboardQuery.DASHBOARD_QUERY_KEY_FORMAT.format(
            product=self._product,
            cluster=self._cluster,
            dashboard_group_id=self._dashboard_group_id,
            dashboard_id=self._dashboard_id,
            query_id=self._query_id
        )

    def create_next_atlas_entity(self) -> Union[AtlasEntity, None]:
        try:
            return next(self._atlas_entity_iterator)
        except StopIteration:
            return None

    def create_next_atlas_relation(self) -> Union[AtlasRelationship, None]:
        return None

    def _create_next_atlas_entity(self) -> Iterator[AtlasEntity]:
        # Query
        attrs_mapping = [
            (AtlasCommonParams.qualified_name, self._get_query_node_key()),
            ('name', self._query_name),
            ('id', self._query_id),
            ('url', self._url),
            ('queryText', self._query_text)
        ]

        query_entity_attrs = get_entity_attrs(attrs_mapping)

        relationship_list = []  # type: ignore

        add_entity_relationship(
            relationship_list,
            'dashboard',
            AtlasDashboardTypes.metadata,
            DashboardMetadata.DASHBOARD_KEY_FORMAT.format(
                product=self._product,
                cluster=self._cluster,
                dashboard_group=self._dashboard_group_id,
                dashboard_name=self._dashboard_id
            )
        )

        query_entity = AtlasEntity(
            typeName=AtlasDashboardTypes.query,
            operation=AtlasSerializedEntityOperation.CREATE,
            attributes=query_entity_attrs,
            relationships=get_entity_relationships(relationship_list)
        )
        yield query_entity

    def __repr__(self) -> str:
        return f'DashboardQuery({self._dashboard_group_id!r}, {self._dashboard_id!r}, {self._query_name!r}, ' \
               f'{self._query_id!r}, {self._url!r}, {self._query_text!r}, {self._product!r}, {self._cluster!r})'
