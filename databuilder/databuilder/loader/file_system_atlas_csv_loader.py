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
from databuilder.models.atlas_serializable import AtlasSerializable
from databuilder.serializers import atlas_serializer
from databuilder.utils.closer import Closer

LOGGER = logging.getLogger(__name__)


class FsAtlasCSVLoader(Loader):
    """
    Write entity and relationship CSV file(s) that can be consumed by
    AtlasCsvPublisher.
    It assumes that the record it consumes is instance of AtlasCsvSerializable
    """
    # Config keys
    ENTITY_DIR_PATH = 'entity_dir_path'
    RELATIONSHIP_DIR_PATH = 'relationship_dir_path'
    FORCE_CREATE_DIR = 'force_create_directory'
    SHOULD_DELETE_CREATED_DIR = 'delete_created_directories'

    _DEFAULT_CONFIG = ConfigFactory.from_dict({
        SHOULD_DELETE_CREATED_DIR: True,
        FORCE_CREATE_DIR: False,
    })

    def __init__(self) -> None:
        self._entity_file_mapping: Dict[Any, DictWriter] = {}
        self._relation_file_mapping: Dict[Any, DictWriter] = {}
        self._keys: Dict[FrozenSet[str], int] = {}
        self._closer = Closer()

    def init(self, conf: ConfigTree) -> None:
        """
        Initializing FsAtlasCSVLoader by creating directory for entity files
        and relationship files. Note that the directory defined in
        configuration should not exist.
        :param conf:
        :return:
        """
        conf = conf.with_fallback(FsAtlasCSVLoader._DEFAULT_CONFIG)

        self._entity_dir = conf.get_string(FsAtlasCSVLoader.ENTITY_DIR_PATH)
        self._relation_dir = \
            conf.get_string(FsAtlasCSVLoader.RELATIONSHIP_DIR_PATH)

        self._delete_created_dir = \
            conf.get_bool(FsAtlasCSVLoader.SHOULD_DELETE_CREATED_DIR)
        self._force_create_dir = conf.get_bool(FsAtlasCSVLoader.FORCE_CREATE_DIR)
        self._create_directory(self._entity_dir)
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

    def load(self, csv_serializable: AtlasSerializable) -> None:
        """
        Writes AtlasSerializable into CSV files.
        There are multiple CSV files that this method writes.
        This is because there're not only node and relationship, but also it
        can also have different entities, and relationships.

        Common pattern for both entities and relations:
         1. retrieve csv row (a dict where keys represent a header,
         values represent a row)
         2. using this dict to get a appropriate csv writer and write to it.
         3. repeat 1 and 2

        :param csv_serializable:
        :return:
        """

        entity = csv_serializable.next_atlas_entity()
        while entity:
            entity_dict = atlas_serializer.serialize_entity(entity)
            key = (self._make_key(entity_dict), entity.typeName)
            file_suffix = '{}_{}'.format(*key)
            entity_writer = self._get_writer(
                entity_dict,
                self._entity_file_mapping,
                key,
                self._entity_dir,
                file_suffix,
            )
            entity_writer.writerow(entity_dict)
            entity = csv_serializable.next_atlas_entity()

        relation = csv_serializable.next_atlas_relation()
        while relation:
            relation_dict = atlas_serializer.serialize_relationship(relation)
            keys = (
                self._make_key(relation_dict),
                relation.entityType1,
                relation.entityType2,
            )

            file_suffix = '{}_{}_{}'.format(*keys)
            relation_writer = self._get_writer(
                relation_dict,
                self._relation_file_mapping,
                keys,
                self._relation_dir,
                file_suffix,
            )
            relation_writer.writerow(relation_dict)
            relation = csv_serializable.next_atlas_relation()

    def _get_writer(
        self,
        csv_record_dict: Dict[str, Any],
        file_mapping: Dict[Any, DictWriter],
        key: Any,
        dir_path: str,
        file_suffix: str,
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
        writer = csv.DictWriter(  # type: ignore
            file_out,
            fieldnames=csv_record_dict.keys(),
            quoting=csv.QUOTE_NONNUMERIC,
        )

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
        return "loader.filesystem_csv_atlas"

    def _make_key(self, record_dict: Dict[str, Any]) -> str:
        """ Each unique set of record keys is assigned an increasing numeric key """
        return str(self._keys.setdefault(frozenset(record_dict.keys()), len(self._keys))).rjust(3, '0')
