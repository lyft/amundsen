# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import os

from pyhocon import ConfigTree

from databuilder.loader.base_loader import Loader
from databuilder.models.elasticsearch_document import ElasticsearchDocument


class FSElasticsearchJSONLoader(Loader):
    """
    Loader class to produce Elasticsearch bulk load file to Local FileSystem
    """
    FILE_PATH_CONFIG_KEY = 'file_path'
    FILE_MODE_CONFIG_KEY = 'mode'

    def init(self, conf: ConfigTree) -> None:
        """

        :param conf:
        :return:
        """
        self.conf = conf
        self.file_path = self.conf.get_string(FSElasticsearchJSONLoader.FILE_PATH_CONFIG_KEY)
        self.file_mode = self.conf.get_string(FSElasticsearchJSONLoader.FILE_MODE_CONFIG_KEY, 'w')

        file_dir = self.file_path.rsplit('/', 1)[0]
        self._ensure_directory_exists(file_dir)
        self.file_handler = open(self.file_path, self.file_mode)

    def _ensure_directory_exists(self, path: str) -> None:
        """
        Check to ensure file directory exists; create the directories otherwise
        :param path:
        :return: None
        """
        if os.path.exists(path):
            return  # nothing to do here

        os.makedirs(path)

    def load(self, record: ElasticsearchDocument) -> None:
        """
        Write a record in json format to file
        :param record:
        :return:
        """
        if not record:
            return

        if not isinstance(record, ElasticsearchDocument):
            raise Exception("Record not of type 'ElasticsearchDocument'!")

        self.file_handler.write(record.to_json())
        self.file_handler.flush()

    def close(self) -> None:
        """
        close the file handler
        :return:
        """
        if self.file_handler:
            self.file_handler.close()

    def get_scope(self) -> str:
        return 'loader.filesystem.elasticsearch'
