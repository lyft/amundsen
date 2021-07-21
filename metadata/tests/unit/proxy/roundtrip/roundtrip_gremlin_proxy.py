# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import logging
from datetime import datetime
from typing import Any, List

from amundsen_common.models.table import (Application, Column,
                                          ProgrammaticDescription, Table)
from amundsen_common.models.user import User
from amundsen_gremlin.gremlin_model import EdgeTypes, VertexTypes
from amundsen_gremlin.gremlin_shared import (make_cluster_uri, make_column_uri,
                                             make_database_uri,
                                             make_description_uri,
                                             make_schema_uri, make_table_uri)
from gremlin_python.process.traversal import Direction
from overrides import overrides

from metadata_service.proxy.gremlin_proxy import (_V, AMUNDSEN_TIMESTAMP_KEY,
                                                  ExecuteQuery, FromResultSet,
                                                  GenericGremlinProxy,
                                                  _expire_other_links, _link,
                                                  _properties_except,
                                                  _properties_of, _upsert,
                                                  timestamp)
from metadata_service.proxy.statsd_utilities import timer_with_counter

from .roundtrip_base_proxy import RoundtripBaseProxy

LOGGER = logging.getLogger(__name__)


class RoundtripGremlinProxy(GenericGremlinProxy, RoundtripBaseProxy):
    @timer_with_counter
    @overrides
    def put_user(self, *, data: User) -> None:
        with self.query_executor() as executor:
            return self._put_user(data=data, executor=executor)

    def _put_user(self, *, data: User, executor: ExecuteQuery) -> None:
        if data.user_id is None:
            raise NotImplementedError(f'Must pass some user_id to derive vertex key')
        _upsert(executor=executor, g=self.g, label=VertexTypes.User, key=data.user_id,
                key_property_name=self.key_property_name, **_properties_except(data))

    @timer_with_counter
    @overrides
    def post_users(self, *, data: List[User]) -> None:
        with self.query_executor() as executor:
            for each in data:
                self._put_user(data=each, executor=executor)

    @timer_with_counter
    @overrides
    def put_app(self, *, data: Application) -> None:
        with self.query_executor() as executor:
            return self._put_app(data=data, executor=executor)

    def _put_app(self, *, data: Application, executor: ExecuteQuery) -> None:
        _upsert(executor=executor, g=self.g, label=VertexTypes.Application, key=data.id,
                key_property_name=self.key_property_name, **_properties_except(data))

    @timer_with_counter
    @overrides
    def post_apps(self, *, data: List[Application]) -> None:
        with self.query_executor() as executor:
            for each in data:
                self._put_app(data=each, executor=executor)

    def _put_database(self, *, database: str, executor: ExecuteQuery) -> None:
        database_uri = make_database_uri(database_name=database)
        _upsert(executor=executor, g=self.g, label=VertexTypes.Database, key=database_uri,
                key_property_name=self.key_property_name, name=database)

    def _put_cluster(self, *, database_uri: str, cluster: str, executor: ExecuteQuery) -> None:
        cluster_uri: str = make_cluster_uri(database_uri=database_uri, cluster_name=cluster)
        node_id: Any = _upsert(executor=executor, g=self.g, label=VertexTypes.Cluster, key=cluster_uri,
                               key_property_name=self.key_property_name, name=cluster)

        _link(executor=executor, g=self.g, edge_label=EdgeTypes.Cluster, key_property_name=self.key_property_name,
              vertex1_label=VertexTypes.Database, vertex1_key=database_uri, vertex2_id=node_id)

    def _put_schema(self, *, cluster_uri: str, schema: str, executor: ExecuteQuery) -> None:
        schema_uri: str = make_schema_uri(cluster_uri=cluster_uri, schema_name=schema)

        node_id: Any = _upsert(executor=executor, g=self.g, label=VertexTypes.Schema, key=schema_uri,
                               key_property_name=self.key_property_name, name=schema)

        _link(executor=executor, g=self.g, edge_label=EdgeTypes.Schema, key_property_name=self.key_property_name,
              vertex1_label=VertexTypes.Cluster, vertex1_key=cluster_uri, vertex2_id=node_id)

    @timer_with_counter
    @overrides
    def put_table(self, *, table: Table) -> None:
        with self.query_executor() as executor:
            return self._put_table(table=table, executor=executor)

    def _put_table(self, *, table: Table, executor: ExecuteQuery) -> None:
        # note: I hate this API where we pass a name, get back nothing and then recapitulate the key logic.  -
        self._put_database(database=table.database, executor=executor)
        database_uri: str = make_database_uri(database_name=table.database)

        self._put_cluster(cluster=table.cluster, database_uri=database_uri, executor=executor)
        cluster_uri: str = make_cluster_uri(database_uri=database_uri, cluster_name=table.cluster)

        self._put_schema(schema=table.schema, cluster_uri=cluster_uri, executor=executor)
        schema_uri: str = make_schema_uri(cluster_uri=cluster_uri, schema_name=table.schema)

        table_uri: str = make_table_uri(schema_uri=schema_uri, table_name=table.name)
        table_vertex_id: Any = _upsert(executor=executor, g=self.g, label=VertexTypes.Table, key=table_uri,
                                       key_property_name=self.key_property_name, is_view=table.is_view, name=table.name)

        _link(executor=executor, g=self.g, edge_label=EdgeTypes.Table, key_property_name=self.key_property_name,
              vertex1_label=VertexTypes.Schema, vertex1_key=schema_uri, vertex2_id=table_vertex_id)

        if table.table_writer:
            self._put_app_table_relation(executor=executor, app_key=table.table_writer.id, table_uri=table_uri)

        # Attach table description
        if table.description is not None:
            self._put_table_description(executor=executor, table_uri=table_uri, description=table.description)

        for description in table.programmatic_descriptions:
            self._put_programmatic_table_description(executor=executor, table_uri=table_uri, description=description)

        # create tags
        for tag in table.tags:
            self._add_tag(executor=executor, id=table_uri, tag=tag.tag_name)

        self._put_updated_timestamp(executor=executor)

        # create columns
        for column in table.columns:
            self._put_column(executor=executor, table_uri=table_uri, column=column)

    def _put_app_table_relation(self, *, app_key: str, table_uri: str, executor: ExecuteQuery) -> None:
        # try the usual app, but also fallback to a non-standard name (prefixed by app_)
        for key in (app_key, f'app-{app_key}'):
            count = executor(query=_V(g=self.g, label=VertexTypes.Application, key=key).count(),
                             get=FromResultSet.getOnly)
            if count > 0:
                _link(executor=executor, g=self.g, edge_label=EdgeTypes.Generates,
                      key_property_name=self.key_property_name,
                      vertex1_label=VertexTypes.Application, vertex1_key=key,
                      vertex2_label=VertexTypes.Table, vertex2_key=table_uri)

                _expire_other_links(executor=executor, g=self.g, edge_label=EdgeTypes.Generates,
                                    key_property_name=self.key_property_name,
                                    vertex1_label=VertexTypes.Table, vertex1_key=table_uri,
                                    vertex2_label=VertexTypes.Application, vertex2_key=key,
                                    edge_direction=Direction.IN)
                return

        # if app isn't found, the owner may be a user
        if self._get_user(executor=executor, id=app_key):
            LOGGER.debug(f'{app_key} is not a real app but it was marked as owner: {table_uri}')
            self._add_owner(executor=executor, table_uri=table_uri, owner=app_key)
            return

        LOGGER.debug(f'{app_key} is not a real app nor an owner: {table_uri}')

    def _put_updated_timestamp(self, executor: ExecuteQuery) -> datetime:
        t = timestamp()
        _upsert(executor=executor, g=self.g, label=VertexTypes.Updatedtimestamp,
                key=AMUNDSEN_TIMESTAMP_KEY, key_property_name=self.key_property_name, latest_timestamp=t)
        return t

    @timer_with_counter
    @overrides
    def post_tables(self, *, tables: List[Table]) -> None:
        """
        Update table with user-supplied data.

        Add indexes for all node types
        :param table: new table to be added
        """
        with self.query_executor() as executor:
            for each in tables:
                self._put_table(table=each, executor=executor)

    @timer_with_counter
    @overrides
    def put_column(self, *, table_uri: str, column: Column) -> None:
        """
        Update column with user-supplied data
        :param table_uri: Table uri (key in Neo4j)
        :param column: new column to be added
        """
        with self.query_executor() as executor:
            return self._put_column(table_uri=table_uri, column=column, executor=executor)

    def _put_column(self, *, table_uri: str, column: Column, executor: ExecuteQuery) -> None:
        # TODO: could do these async
        column_uri: str = make_column_uri(table_uri=table_uri, column_name=column.name)

        vertex_id: Any = _upsert(executor=executor, g=self.g, label=VertexTypes.Column, key=column_uri,
                                 key_property_name=self.key_property_name,
                                 **_properties_of(column, 'name', 'col_type', 'sort_order'))

        _link(
            executor=executor, g=self.g, edge_label=EdgeTypes.Column, key_property_name=self.key_property_name,
            vertex1_label=VertexTypes.Table, vertex1_key=table_uri, vertex2_id=vertex_id)

        # Add the description if present
        if column.description is not None:
            self._put_column_description(
                executor=executor, table_uri=table_uri, column_name=column.name, description=column.description)

        # stats are handled elsewhere but it would be weird to get
        # them here
        if column.stats:
            raise RuntimeError(f'stats, data_subject_type, data_storage_security are handled elsewhere!')

    @timer_with_counter
    @overrides
    def put_programmatic_table_description(self, *, table_uri: str, description: ProgrammaticDescription) -> None:
        """
        Update table description with one from user
        :param table_uri: Table uri (key in Neo4j)
        :param Description: description object with source and string description
        """
        with self.query_executor() as executor:
            return self._put_programmatic_table_description(
                table_uri=table_uri, description=description, executor=executor)

    def _put_programmatic_table_description(self, *, table_uri: str, description: ProgrammaticDescription,
                                            executor: ExecuteQuery) -> None:
        g = _V(g=self.g, label=VertexTypes.Table, key=table_uri).id()
        table_vertex_id = executor(query=g, get=FromResultSet.getOptional)
        if not table_vertex_id:
            # if the table doesn't exist, don't try to import a description
            return None

        desc_key = make_description_uri(subject_uri=table_uri, source=description.source)
        vertex_id: Any = _upsert(executor=executor, g=self.g, label=VertexTypes.Description, key=desc_key,
                                 key_property_name=self.key_property_name, description=description.text,
                                 source=description.source)

        _link(executor=executor, g=self.g, edge_label=EdgeTypes.Description, key_property_name=self.key_property_name,
              vertex1_id=table_vertex_id, vertex2_id=vertex_id)

    @timer_with_counter
    @overrides
    def add_read_count(self, *, table_uri: str, user_id: str, read_count: int) -> None:
        # TODO: use READ_BY instead of READ edges
        with self.query_executor() as executor:
            _link(executor=executor, g=self.g, edge_label=EdgeTypes.Read, key_property_name=self.key_property_name,
                  vertex1_label=VertexTypes.User, vertex1_key=user_id,
                  vertex2_label=VertexTypes.Table, vertex2_key=table_uri,
                  read_count=read_count)
