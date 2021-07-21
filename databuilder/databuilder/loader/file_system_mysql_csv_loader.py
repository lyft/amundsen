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
from databuilder.models.table_serializable import TableSerializable
from databuilder.serializers import mysql_serializer
from databuilder.utils.closer import Closer

LOGGER = logging.getLogger(__name__)


class FSMySQLCSVLoader(Loader):
    """
    Write table record CSV file(s) that can be consumed by MySQLCsvPublisher.
    It assumes that the record it consumes is instance of TableSerializable.
    """
    # Config keys
    RECORD_DIR_PATH = 'record_dir_path'
    FORCE_CREATE_DIR = 'force_create_directory'
    SHOULD_DELETE_CREATED_DIR = 'delete_created_directories'

    _DEFAULT_CONFIG = ConfigFactory.from_dict({
        SHOULD_DELETE_CREATED_DIR: True,
        FORCE_CREATE_DIR: False
    })

    def __init__(self) -> None:
        self._record_file_mapping: Dict[Any, DictWriter] = {}
        self._keys: Dict[FrozenSet[str], int] = {}
        self._closer = Closer()

    def init(self, conf: ConfigTree) -> None:
        """
        Initializing FsMySQLCSVLoader by creating directory for record files.
        Note that the directory defined in configuration should not exist.
        :param conf:
        :return:
        """
        conf = conf.with_fallback(FSMySQLCSVLoader._DEFAULT_CONFIG)

        self._record_dir = conf.get_string(FSMySQLCSVLoader.RECORD_DIR_PATH)
        self._delete_created_dir = conf.get_bool(FSMySQLCSVLoader.SHOULD_DELETE_CREATED_DIR)
        self._force_create_dir = conf.get_bool(FSMySQLCSVLoader.FORCE_CREATE_DIR)
        self._create_directory(self._record_dir)

    def _create_directory(self, path: str) -> None:
        """
        Validate directory does not exist, creates it, register deletion of
        created directory function to Job.closer.
        :param path:
        :return:
        """
        if os.path.exists(path):
            if self._force_create_dir:
                LOGGER.info(f'Directory exist. Deleting directory {path}')
                shutil.rmtree(path)
            else:
                raise RuntimeError(f'Directory should not exist: {path}')

        os.makedirs(path)

        def _delete_dir() -> None:
            if not self._delete_created_dir:
                LOGGER.warning(f'Skip Deleting directory {path}')
                return

            LOGGER.info(f'Deleting directory {path}')
            shutil.rmtree(path)

        # Directory should be deleted after publish is finished
        Job.closer.register(_delete_dir)

    def load(self, csv_serializable: TableSerializable) -> None:
        """
        Writes TableSerializable records into CSV files.
        There are multiple CSV files meaning different tables that this method writes.

        Common pattern for table records:
         1. retrieve csv row (a dict where keys represent a header,
         values represent a row)
         2. using this dict to get a appropriate csv writer and write to it.
         3. repeat 1 and 2

        :param csv_serializable:
        :return:
        """
        record = csv_serializable.next_record()
        while record:
            record_dict = mysql_serializer.serialize_record(record)
            table_name = record.__tablename__
            key = (table_name, self._make_key(record_dict))
            file_suffix = '{}_{}'.format(*key)
            record_writer = self._get_writer(record_dict,
                                             self._record_file_mapping,
                                             key,
                                             self._record_dir,
                                             file_suffix)
            record_writer.writerow(record_dict)
            record = csv_serializable.next_record()

    def _get_writer(self,
                    csv_record_dict: Dict[str, Any],
                    file_mapping: Dict[Any, DictWriter],
                    key: Any,
                    dir_path: str,
                    file_suffix: str
                    ) -> DictWriter:
        """
        Finds a writer based on csv record, key.
        If writer does not exist, it's creates a csv writer and update the mapping.

        :param csv_record_dict:
        :param file_mapping:
        :param key:
        :param dir_path:
        :param file_suffix:
        :return:
        """
        writer = file_mapping.get(key)
        if writer:
            return writer

        LOGGER.info(f'Creating file for {key}')

        file_out = open(f'{dir_path}/{file_suffix}.csv', 'w', encoding='utf8')
        writer = csv.DictWriter(file_out, fieldnames=csv_record_dict.keys(),
                                quoting=csv.QUOTE_NONNUMERIC)

        def file_out_close() -> None:
            LOGGER.info(f'Closing file IO {file_out}')
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
        return "loader.mysql_filesystem_csv"

    def _make_key(self, record_dict: Dict[str, Any]) -> int:
        """ Each unique set of record keys is assigned an increasing numeric key """
        return self._keys.setdefault(frozenset(record_dict.keys()), len(self._keys))
