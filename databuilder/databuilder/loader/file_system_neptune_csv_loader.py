# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import csv
import logging
import os
import shutil
from csv import DictWriter
from typing import Any, Dict

from pyhocon import ConfigFactory, ConfigTree

from databuilder.job.base_job import Job
from databuilder.loader.base_loader import Loader
from databuilder.models.graph_serializable import GraphSerializable
from databuilder.serializers import neptune_serializer
from databuilder.utils.closer import Closer

LOGGER = logging.getLogger(__name__)

PUBLISHED_TAG_PROPERTY_NAME = 'published_tag'


class FSNeptuneCSVLoader(Loader):
    """
    Write node and relationship CSV file(s) that can be consumed by
    NeptuneCsvPublisher.
    It assumes that the record it consumes is instance of GraphSerializable
    """
    # Config keys
    NODE_DIR_PATH = 'node_dir_path'
    RELATION_DIR_PATH = 'relationship_dir_path'
    FORCE_CREATE_DIR = 'force_create_directory'
    SHOULD_DELETE_CREATED_DIR = 'delete_created_directories'
    JOB_PUBLISHER_TAG = 'job_publisher_tag'

    _DEFAULT_CONFIG = ConfigFactory.from_dict({
        SHOULD_DELETE_CREATED_DIR: True,
        FORCE_CREATE_DIR: False
    })

    def __init__(self) -> None:
        self._node_file_mapping: Dict[Any, DictWriter] = {}
        self._relation_file_mapping: Dict[Any, DictWriter] = {}
        self._closer = Closer()

    def init(self, conf: ConfigTree) -> None:
        """
        Initializing FSNeptuneCSVLoader by creating directory for node files
        and relationship files. Note that the directory defined in
        configuration should not exist.
        """
        conf = conf.with_fallback(FSNeptuneCSVLoader._DEFAULT_CONFIG)

        self._node_dir = conf.get_string(FSNeptuneCSVLoader.NODE_DIR_PATH)
        self._relation_dir = conf.get_string(FSNeptuneCSVLoader.RELATION_DIR_PATH)

        self._delete_created_dir = conf.get_bool(FSNeptuneCSVLoader.SHOULD_DELETE_CREATED_DIR)
        self._force_create_dir = conf.get_bool(FSNeptuneCSVLoader.FORCE_CREATE_DIR)
        self._create_directory(self._node_dir)
        self._create_directory(self._relation_dir)
        self.job_publisher_tag = conf.get_string(FSNeptuneCSVLoader.JOB_PUBLISHER_TAG)

    def _create_directory(self, path: str) -> None:
        """
        Validate directory does not exist, creates it, register deletion of
        created directory function to Job.closer.
        """
        if os.path.exists(path):
            if self._force_create_dir:
                LOGGER.info('Directory exist. Deleting directory {}'.format(path))
                shutil.rmtree(path)
            else:
                raise RuntimeError('Directory should not exist: {}'.format(path))

        os.makedirs(path)

        def _delete_dir() -> None:
            if not self._delete_created_dir:
                LOGGER.warn('Skip Deleting directory {}'.format(path))
                return

            LOGGER.info('Deleting directory {}'.format(path))
            shutil.rmtree(path)

        # Directory should be deleted after publish is finished
        Job.closer.register(_delete_dir)

    def load(self, csv_serializable: GraphSerializable) -> None:
        """
        Writes GraphSerializable into CSV files.
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

            node.attributes[PUBLISHED_TAG_PROPERTY_NAME] = self.job_publisher_tag
            node_dict = neptune_serializer.convert_node(node)
            if node_dict:
                key = (node.label, len(node_dict))
                file_suffix = '{}_{}'.format(*key)
                node_writer = self._get_writer(
                    node_dict,
                    self._node_file_mapping,
                    key,
                    self._node_dir,
                    file_suffix
                )
                node_writer.writerow(node_dict)
            node = csv_serializable.next_node()

        relation = csv_serializable.next_relation()
        while relation:
            relation.attributes[PUBLISHED_TAG_PROPERTY_NAME] = self.job_publisher_tag
            relation_dicts = neptune_serializer.convert_relationship(relation)
            if relation_dicts:
                key2 = (relation.start_label,
                        relation.end_label,
                        relation.type,
                        len(relation_dicts[0]))

                file_suffix = '{}_{}_{}'.format(key2[0], key2[1], key2[2])
                relation_writer = self._get_writer(relation_dicts[0],
                                                   self._relation_file_mapping,
                                                   key2,
                                                   self._relation_dir,
                                                   file_suffix)
                relation_writer.writerows(relation_dicts)
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
        """
        writer = file_mapping.get(key)
        if writer:
            return writer

        LOGGER.info('Creating file for {}'.format(key))

        file_out = open('{}/{}.csv'.format(dir_path, file_suffix), 'w', encoding='utf8')
        writer = csv.DictWriter(file_out, fieldnames=csv_record_dict.keys(), quoting=csv.QUOTE_NONNUMERIC)

        def file_out_close() -> None:
            LOGGER.info('Closing file IO {}'.format(file_out))
            file_out.close()
        self._closer.register(file_out_close)

        writer.writeheader()
        file_mapping[key] = writer

        return writer

    def close(self) -> None:
        """
        Any closeable callable registered in _closer, it will close.
        """
        self._closer.close()

    def get_scope(self) -> str:
        return "loader.neptune_filesystem_csv"
