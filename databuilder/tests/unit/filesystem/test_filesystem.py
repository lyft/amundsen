# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import unittest
from datetime import datetime

from mock import MagicMock
from pyhocon import ConfigFactory
from pytz import UTC

from databuilder.filesystem.filesystem import FileSystem
from databuilder.filesystem.metadata import FileMetadata


class TestFileSystem(unittest.TestCase):

    def test_is_file(self) -> None:
        dask_fs = MagicMock()
        dask_fs.ls = MagicMock(return_value=['/foo/bar'])

        fs = FileSystem()
        conf = ConfigFactory.from_dict({FileSystem.DASK_FILE_SYSTEM: dask_fs})
        fs.init(conf=conf)

        self.assertTrue(fs.is_file('/foo/bar'))

        dask_fs.ls = MagicMock(return_value=['bar', 'baz'])

        fs = FileSystem()
        conf = ConfigFactory.from_dict({FileSystem.DASK_FILE_SYSTEM: dask_fs})
        fs.init(conf=conf)

        self.assertFalse(fs.is_file('foo'))

    def test_info(self) -> None:
        dask_fs = MagicMock()
        dask_fs.info = MagicMock(return_value={'LastModified': datetime(2018, 8, 14, 4, 12, 3, tzinfo=UTC),
                                               'Size': 15093})
        fs = FileSystem()
        conf = ConfigFactory.from_dict({FileSystem.DASK_FILE_SYSTEM: dask_fs})
        fs.init(conf=conf)
        metadata = fs.info('/foo/bar')

        expected = FileMetadata(path='/foo/bar', last_updated=datetime(2018, 8, 14, 4, 12, 3, tzinfo=UTC), size=15093)

        self.assertEqual(metadata.__repr__(), expected.__repr__())


if __name__ == '__main__':
    unittest.main()
