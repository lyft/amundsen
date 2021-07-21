# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import csv
import logging
import os
import shutil
from csv import DictWriter
from typing import (
    Any, Dict, FrozenSet,
)

from pyhocon import ConfigFactory, ConfigTree

from databuilder.job.base_job import Job
from databuilder.loader.base_loader import Loader
from databuilder.models.graph_serializable import GraphSerializable
from databuilder.serializers import neo4_serializer
from databuilder.utils.closer import Closer

LOGGER = logging.getLogger(__name__)


class FsNeo4jCSVLoader(Loader):
    """
    Write node and relationship CSV file(s) that can be consumed by
    Neo4jCsvPublisher.
    It assumes that the record it consumes is instance of Neo4jCsvSerializable
    """
    # Config keys
    NODE_DIR_PATH = 'node_dir_path'
    RELATION_DIR_PATH = 'relationship_dir_path'
    FORCE_CREATE_DIR = 'force_create_directory'
    SHOULD_DELETE_CREATED_DIR = 'delete_created_directories'

    _DEFAULT_CONFIG = ConfigFactory.from_dict({
        SHOULD_DELETE_CREATED_DIR: True,
        FORCE_CREATE_DIR: False
    })

    def __init__(self) -> None:
        self._node_file_mapping: Dict[Any, DictWriter] = {}
        self._relation_file_mapping: Dict[Any, DictWriter] = {}
        self._keys: Dict[FrozenSet[str], int] = {}
        self._closer = Closer()

    def init(self, conf: ConfigTree) -> None:
        """
        Initializing FsNeo4jCsvLoader by creating directory for node files
        and relationship files. Note that the directory defined in
        configuration should not exist.
        :param conf:
        :return:
        """
        conf = conf.with_fallback(FsNeo4jCSVLoader._DEFAULT_CONFIG)

        self._node_dir = conf.get_string(FsNeo4jCSVLoader.NODE_DIR_PATH)
        self._relation_dir = \
            conf.get_string(FsNeo4jCSVLoader.RELATION_DIR_PATH)

        self._delete_created_dir = \
            conf.get_bool(FsNeo4jCSVLoader.SHOULD_DELETE_CREATED_DIR)
        self._force_create_dir = conf.get_bool(FsNeo4jCSVLoader.FORCE_CREATE_DIR)
        self._create_directory(self._node_dir)
        self._create_directory(self._relation_dir)

    def _create_directory(self, path: str) -> None:
        """
        Validate directory does not exist, creates it, register deletion of
        created directory function to Job.closer.
        :param path:
        :return:
        """
        if os.path.exists(path):
            if self._force_create_dir:
                LOGGER.info('Directory exist. Deleting directory %s', path)
                shutil.rmtree(path)
            else:
                raise RuntimeError(f'Directory should not exist: {path}')

        os.makedirs(path)

        def _delete_dir() -> None:
            if not self._delete_created_dir:
                LOGGER.warning('Skip Deleting directory %s', path)
                return

            LOGGER.info('Deleting directory %s', path)
            shutil.rmtree(path)

        # Directory should be deleted after publish is finished
        Job.closer.register(_delete_dir)

    def load(self, csv_serializable: GraphSerializable) -> None:
        """
        Writes Neo4jCsvSerializable into CSV files.
        There are multiple CSV files that this method writes.
        This is because there're not only node and relationship, but also it
        can also have different nodes, and relationships.

        Common pattern for both nodes and relations:
         1. retrieve csv row (a dict where keys represent a header,
         values represent a row)
         2. using this dict to get a appropriate csv writer and write to it.
         3. repeat 1 and 2

        :param csv_serializable:
        :return:
        """

        node = csv_serializable.next_node()
        while node:
            node_dict = neo4_serializer.serialize_node(node)
            key = (node.label, self._make_key(node_dict))
            file_suffix = '{}_{}'.format(*key)
            node_writer = self._get_writer(node_dict,
                                           self._node_file_mapping,
                                           key,
                                           self._node_dir,
                                           file_suffix)
            node_writer.writerow(node_dict)
            node = csv_serializable.next_node()

        relation = csv_serializable.next_relation()
        while relation:
            relation_dict = neo4_serializer.serialize_relationship(relation)
            key2 = (relation.start_label,
                    relation.end_label,
                    relation.type,
                    self._make_key(relation_dict))

            file_suffix = f'{key2[0]}_{key2[1]}_{key2[2]}'
            relation_writer = self._get_writer(relation_dict,
                                               self._relation_file_mapping,
                                               key2,
                                               self._relation_dir,
                                               file_suffix)
            relation_writer.writerow(relation_dict)
            relation = csv_serializable.next_relation()

    def _get_writer(self,
                    csv_record_dict: Dict[str, Any],
                    file_mapping: Dict[Any, DictWriter],
                    key: Any,
                    dir_path: str,
                    file_suffix: str
                    ) -> DictWriter:
        """
        Finds a writer based on csv record, key.
        If writer does not exist, it's creates a csv writer and update the
        mapping.

        :param csv_record_dict:
        :param file_mapping:
        :param key:
        :param file_suffix:
        :return:
        """
        writer = file_mapping.get(key)
        if writer:
            return writer

        LOGGER.info('Creating file for %s', key)

        file_out = open(f'{dir_path}/{file_suffix}.csv', 'w', encoding='utf8')
        writer = csv.DictWriter(file_out, fieldnames=csv_record_dict.keys(),
                                quoting=csv.QUOTE_NONNUMERIC)

        def file_out_close() -> None:
            LOGGER.info('Closing file IO %s', file_out)
            file_out.close()
        self._closer.register(file_out_close)

        writer.writeheader()
        file_mapping[key] = writer

        return writer

    def close(self) -> None:
        """
        Any closeable callable registered in _closer, it will close.
        :return:
        """
        self._closer.close()

    def get_scope(self) -> str:
        return "loader.filesystem_csv_neo4j"

    def _make_key(self, record_dict: Dict[str, Any]) -> int:
        """ Each unique set of record keys is assigned an increasing numeric key """
        return self._keys.setdefault(frozenset(record_dict.keys()), len(self._keys))
