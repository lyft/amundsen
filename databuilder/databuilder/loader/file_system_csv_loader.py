# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import csv
import logging
from typing import Any

from pyhocon import ConfigTree

from databuilder.loader.base_loader import Loader

LOGGER = logging.getLogger(__name__)


class FileSystemCSVLoader(Loader):
    """
    Loader class to write csv files to Local FileSystem
    """

    def init(self, conf: ConfigTree) -> None:
        """
        Initialize file handlers from conf
        :param conf:
        """
        self.conf = conf
        self.file_path = self.conf.get_string('file_path')
        self.file_mode = self.conf.get_string('mode', 'w')

        self.file_handler = open(self.file_path, self.file_mode)

    def load(self, record: Any) -> None:
        """
        Write record object as csv to file
        :param record:
        :return:
        """
        if not record:
            return

        if not hasattr(self, 'writer'):
            self.writer = csv.DictWriter(self.file_handler,
                                         fieldnames=vars(record).keys())
            self.writer.writeheader()

        self.writer.writerow(vars(record))
        self.file_handler.flush()

    def close(self) -> None:
        """
        Close file handlers
        :return:
        """
        try:
            if self.file_handler:
                self.file_handler.close()
        except Exception as e:
            LOGGER.warning("Failed trying to close a file handler! %s", e)

    def get_scope(self) -> str:
        return "loader.filesystem.csv"
