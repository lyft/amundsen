# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0import json


import logging
from typing import List

from amundsen_common.models.table import Application, Table
from amundsen_common.models.user import User
from amundsen_gremlin.neptune_bulk_loader.gremlin_model_converter import \
    GetGraph
from overrides import overrides

from metadata_service.proxy.neptune_proxy import NeptuneGremlinProxy

from .roundtrip_gremlin_proxy import RoundtripGremlinProxy

LOGGER = logging.getLogger(__name__)


class RoundtripNeptuneGremlinProxy(NeptuneGremlinProxy, RoundtripGremlinProxy):
    @overrides
    def post_users(self, *, data: List[User]) -> None:
        entities = GetGraph.user_entities(user_data=data, g=self.neptune_graph_traversal_source_factory())
        self.neptune_bulk_loader_api.bulk_load_entities(entities=entities)

    @overrides
    def put_user(self, *, data: User) -> None:
        self.post_users(data=[data])

    @overrides
    def put_app(self, *, data: Application) -> None:
        self.post_apps(data=[data])

    @overrides
    def post_apps(self, *, data: List[Application]) -> None:
        entities = GetGraph.app_entities(app_data=data, g=self.neptune_graph_traversal_source_factory())
        self.neptune_bulk_loader_api.bulk_load_entities(entities=entities)

    @overrides
    def put_table(self, *, table: Table) -> None:
        self.post_tables(tables=[table])

    @overrides
    def post_tables(self, *, tables: List[Table]) -> None:
        entities = GetGraph.table_entities(table_data=tables, g=self.neptune_graph_traversal_source_factory())
        self.neptune_bulk_loader_api.bulk_load_entities(entities=entities)
