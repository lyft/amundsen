# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from typing import (
    Dict, Iterator, Union,
)

import cassandra.metadata
from cassandra.cluster import Cluster
from pyhocon import ConfigFactory, ConfigTree

from databuilder.extractor.base_extractor import Extractor
from databuilder.models.table_metadata import ColumnMetadata, TableMetadata


class CassandraExtractor(Extractor):
    """
    Extracts tables and columns metadata from Apacha Cassandra
    """

    CLUSTER_KEY = 'cluster'
    # Key to define clusters ips, it should be List[str]
    IPS_KEY = 'ips'
    # Key to define extra kwargs to pass on cluster constructor,
    # it should be Dict[Any]
    KWARGS_KEY = 'kwargs'
    # Key to define custom filter function based on keyspace and table
    # since the cluster metadata doesn't support native filters,
    # it should be like def filter(keyspace: str, table: str) -> bool and return False if
    # going to skip that table and True if not
    FILTER_FUNCTION_KEY = 'filter'

    # Default values
    DEFAULT_CONFIG = ConfigFactory.from_dict({
        CLUSTER_KEY: 'gold',
        IPS_KEY: [],
        KWARGS_KEY: {},
        FILTER_FUNCTION_KEY: None
    })

    def init(self, conf: ConfigTree) -> None:
        conf = conf.with_fallback(CassandraExtractor.DEFAULT_CONFIG)
        self._cluster = conf.get_string(CassandraExtractor.CLUSTER_KEY)
        self._filter = conf.get(CassandraExtractor.FILTER_FUNCTION_KEY)
        ips = conf.get_list(CassandraExtractor.IPS_KEY)
        kwargs = conf.get(CassandraExtractor.KWARGS_KEY)
        self._client = Cluster(ips, **kwargs)
        self._client.connect()
        self._extract_iter: Union[None, Iterator] = None

    def extract(self) -> Union[TableMetadata, None]:
        if not self._extract_iter:
            self._extract_iter = self._get_extract_iter()
        try:
            return next(self._extract_iter)
        except StopIteration:
            return None

    def get_scope(self) -> str:
        return 'extractor.cassandra'

    def _get_extract_iter(self) -> Iterator[TableMetadata]:
        """
        It gets all tables and yields TableMetadata
        :return:
        """
        keyspaces = self._get_keyspaces()
        for keyspace in keyspaces:
            # system keyspaces
            if keyspace.startswith('system'):
                continue
            for table in self._get_tables(keyspace):
                if self._filter and not self._filter(keyspace, table):
                    continue

                columns = []

                columns_dict = self._get_columns(keyspace, table)
                for idx, (column_name, column) in enumerate(columns_dict.items()):
                    columns.append(ColumnMetadata(
                        column_name,
                        None,
                        column.cql_type,
                        idx
                    ))

                yield TableMetadata(
                    'cassandra',
                    self._cluster,
                    keyspace,
                    table,
                    None,
                    columns
                )

    def _get_keyspaces(self) -> Dict[str, cassandra.metadata.KeyspaceMetadata]:
        return self._client.metadata.keyspaces

    def _get_tables(self, keyspace: str) -> Dict[str, cassandra.metadata.TableMetadata]:
        return self._client.metadata.keyspaces[keyspace].tables

    def _get_columns(self, keyspace: str, table: str) -> Dict[str, cassandra.metadata.ColumnMetadata]:
        return self._client.metadata.keyspaces[keyspace].tables[table].columns
