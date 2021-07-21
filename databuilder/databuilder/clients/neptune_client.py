# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from typing import (
    Any, Callable, Dict, List, Optional, Tuple,
)

from amundsen_gremlin.neptune_bulk_loader import api as neptune_bulk_loader_api
from boto3.session import Session
from gremlin_python.process.graph_traversal import (
    GraphTraversal, GraphTraversalSource, __,
)
from gremlin_python.process.traversal import T
from pyhocon import ConfigFactory, ConfigTree

from databuilder import Scoped


class NeptuneSessionClient(Scoped):
    """
        A convenience client for neptune gives functions to perform upserts, deletions and queries with filters.
    """
    # What property is used to local nodes and edges by ids
    NEPTUNE_HOST_NAME = 'neptune_host_name'
    # AWS Region the Neptune cluster is located
    AWS_REGION = 'aws_region'
    AWS_ACCESS_KEY = 'aws_access_key'
    AWS_SECRET_ACCESS_KEY = 'aws_access_secret'
    AWS_SESSION_TOKEN = 'aws_session_token'

    WEBSOCKET_OPTIONS = 'websocket_options'

    DEFAULT_CONFIG = ConfigFactory.from_dict(
        {
            AWS_SESSION_TOKEN: None,
            WEBSOCKET_OPTIONS: {},
        }
    )

    def __init__(self) -> None:
        self._graph = None

    def init(self, conf: ConfigTree) -> None:
        conf = conf.with_fallback(NeptuneSessionClient.DEFAULT_CONFIG)

        boto_session = Session(
            aws_access_key_id=conf.get_string(NeptuneSessionClient.AWS_ACCESS_KEY, default=None),
            aws_secret_access_key=conf.get_string(NeptuneSessionClient.AWS_SECRET_ACCESS_KEY, default=None),
            aws_session_token=conf.get_string(NeptuneSessionClient.AWS_SESSION_TOKEN, default=None),
            region_name=conf.get_string(NeptuneSessionClient.AWS_REGION, default=None)
        )
        self._neptune_host = conf.get_string(NeptuneSessionClient.NEPTUNE_HOST_NAME)
        neptune_uri = "wss://{host}/gremlin".format(
            host=self._neptune_host
        )
        source_factory = neptune_bulk_loader_api.get_neptune_graph_traversal_source_factory(
            neptune_url=neptune_uri,
            session=boto_session
        )
        self._graph = source_factory()

    def get_scope(self) -> str:
        return 'neptune.client'

    def get_graph(self) -> GraphTraversalSource:
        return self._graph

    def upsert_node(self, node_id: str, node_label: str, node_properties: Dict[str, Any]) -> None:
        create_traversal = __.addV(node_label).property(T.id, node_id)
        node_traversal = self.get_graph().V().has(T.id, node_id). \
            fold().coalesce(__.unfold(), create_traversal)

        node_traversal = NeptuneSessionClient.update_entity_properties_on_traversal(node_traversal, node_properties)
        node_traversal.next()

    def upsert_edge(
            self,
            start_node_id: str,
            end_node_id: str,
            edge_id: str,
            edge_label: str,
            edge_properties: Dict[str, Any]
    ) -> None:
        create_traversal = __.V().has(
            T.id, start_node_id
        ).addE(edge_label).to(__.V().has(T.id, end_node_id)).property(T.id, edge_id)
        edge_traversal = self.get_graph().V().has(T.id, start_node_id).outE(edge_label).has(T.id, edge_id). \
            fold(). \
            coalesce(__.unfold(), create_traversal)

        edge_traversal = NeptuneSessionClient.update_entity_properties_on_traversal(edge_traversal, edge_properties)
        edge_traversal.next()

    @staticmethod
    def update_entity_properties_on_traversal(
            graph_traversal: GraphTraversal,
            properties: Dict[str, Any]
    ) -> GraphTraversal:
        for key, value in properties.items():
            key_split = key.split(':')
            key = key_split[0]
            value_type = key_split[1]
            if "Long" in value_type:
                value = int(value)
            graph_traversal = graph_traversal.property(key, value)

        return graph_traversal

    @staticmethod
    def filter_traversal(
            graph_traversal: GraphTraversal,
            filter_properties: List[Tuple[str, Any, Callable]],
    ) -> GraphTraversal:
        for filter_property in filter_properties:
            (filter_property_name, filter_property_value, filter_operator) = filter_property
            graph_traversal = graph_traversal.has(filter_property_name, filter_operator(filter_property_value))
        return graph_traversal

    def delete_edges(
            self,
            filter_properties: List[Tuple[str, Any, Callable]],
            edge_labels: Optional[List[str]]
    ) -> None:
        tx = self.get_graph().E()
        if edge_labels:
            tx = tx.hasLabel(*edge_labels)
        tx = NeptuneSessionClient.filter_traversal(tx, filter_properties)

        tx.drop().iterate()

    def delete_nodes(
            self,
            filter_properties: List[Tuple[str, Any, Callable]],
            node_labels: Optional[List[str]]
    ) -> None:
        tx = self.get_graph().V()
        if node_labels:
            tx = tx.hasLabel(*node_labels)
        tx = NeptuneSessionClient.filter_traversal(tx, filter_properties)

        tx.drop().iterate()
