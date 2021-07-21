# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import logging
from typing import List

from pyhocon import ConfigFactory, ConfigTree
from retrying import retry

from databuilder import Scoped
from databuilder.filesystem.metadata import FileMetadata

LOGGER = logging.getLogger(__name__)
CLIENT_ERRORS = {'ClientError', 'FileNotFoundError', 'ParamValidationError'}


def is_client_side_error(e: Exception) -> bool:
    """
    An method that determines if the error is client side error within FileSystem context
    :param e:
    :return:
    """
    return e.__class__.__name__ in CLIENT_ERRORS


def is_retriable_error(e: Exception) -> bool:
    """
    An method that determines if the error is retriable error within FileSystem context
    :param e:
    :return:
    """

    return not is_client_side_error(e)


class FileSystem(Scoped):
    """
    An high level file system, that utilizes Dask File system.
    http://docs.dask.org/en/latest/remote-data-services.html

    All remote call leverages retry against any failure. https://pypi.org/project/retrying/
    """

    # METADATA KEYS
    LAST_UPDATED = 'last_updated'
    SIZE = 'size'

    # CONFIG KEYS
    DASK_FILE_SYSTEM = 'dask_file_system'

    # File metadata that is provided via info(path) method on Dask file system provides a dictionary. As dictionary
    # does not guarantee same key across different implementation, user can provide key mapping.
    FILE_METADATA_MAPPING_KEY = 'file_metadata_mapping'

    default_metadata_mapping = {LAST_UPDATED: 'LastModified',
                                SIZE: 'Size'}
    DEFAULT_CONFIG = ConfigFactory.from_dict({FILE_METADATA_MAPPING_KEY: default_metadata_mapping})

    def init(self,
             conf: ConfigTree
             ) -> None:
        """
        Initialize Filesystem with DASK file system instance
        Dask file system supports multiple remote storage such as S3, HDFS, Google cloud storage,
        Azure Datalake, etc

        http://docs.dask.org/en/latest/remote-data-services.html
        https://github.com/dask/s3fs
        https://github.com/dask/hdfs3
        ...

        :param conf: hocon config
        :return:
        """
        self._conf = conf.with_fallback(FileSystem.DEFAULT_CONFIG)
        self._dask_fs = self._conf.get(FileSystem.DASK_FILE_SYSTEM)
        self._metadata_key_mapping = self._conf.get(FileSystem.FILE_METADATA_MAPPING_KEY).as_plain_ordered_dict()

    @retry(retry_on_exception=is_retriable_error, stop_max_attempt_number=3, wait_exponential_multiplier=1000,
           wait_exponential_max=5000)
    def ls(self, path: str) -> List[str]:
        """
        A scope for the config. Typesafe config supports nested config.
        Scope, string, is used to basically peel off nested config
        :return:
        """
        return self._dask_fs.ls(path)

    @retry(retry_on_exception=is_retriable_error, stop_max_attempt_number=3, wait_exponential_multiplier=1000,
           wait_exponential_max=5000)
    def is_file(self, path: str) -> bool:
        contents = self._dask_fs.ls(path)
        return len(contents) == 1 and contents[0] == path

    @retry(retry_on_exception=is_retriable_error, stop_max_attempt_number=3, wait_exponential_multiplier=1000,
           wait_exponential_max=5000)
    def info(self, path: str) -> FileMetadata:
        """
        Metadata information about the file. It utilizes _metadata_key_mapping when fetching metadata so that it can
        deal with different keys
        :return:
        """
        metadata_dict = self._dask_fs.info(path)
        fm = FileMetadata(path=path,
                          last_updated=metadata_dict[self._metadata_key_mapping[FileSystem.LAST_UPDATED]],
                          size=metadata_dict[self._metadata_key_mapping[FileSystem.SIZE]])
        return fm

    def get_scope(self) -> str:
        return 'filesystem'
