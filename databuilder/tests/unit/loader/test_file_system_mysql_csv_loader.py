# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import os
import unittest
from collections import OrderedDict
from csv import DictReader
from os import listdir
from os.path import (
    basename, isfile, join, splitext,
)
from typing import Any, Dict

from pyhocon import ConfigFactory

from databuilder.job.base_job import Job
from databuilder.loader.file_system_mysql_csv_loader import FSMySQLCSVLoader
from tests.unit.models.test_table_serializable import Actor, Movie


class TestFileSystemMySQLCSVLoader(unittest.TestCase):
    def setUp(self) -> None:
        directory = '/var/tmp/TestFileSystemMySQLCSVLoader'
        self._conf = ConfigFactory.from_dict(
            {
                FSMySQLCSVLoader.RECORD_DIR_PATH: '{}/{}'.format(directory, 'records'),
                FSMySQLCSVLoader.SHOULD_DELETE_CREATED_DIR: True,
                FSMySQLCSVLoader.FORCE_CREATE_DIR: True,
            }
        )

    def tearDown(self) -> None:
        Job.closer.close()

    def test_load(self) -> None:
        actors = [Actor('Tom Cruise'), Actor('Meg Ryan')]
        movie = Movie('Top Gun', actors)

        loader = FSMySQLCSVLoader()
        loader.init(self._conf)
        loader.load(movie)

        loader.close()

        expected_record_path = '{}/../resources/fs_mysql_csv_loader/records'.format(
            os.path.join(os.path.dirname(__file__))
        )
        expected_records = self._get_csv_rows(expected_record_path)
        actual_records = self._get_csv_rows(self._conf.get_string(FSMySQLCSVLoader.RECORD_DIR_PATH))

        self.maxDiff = None
        self.assertDictEqual(expected_records, actual_records)

    def _get_csv_rows(self, path: str) -> Dict[str, Any]:
        files = [join(path, f) for f in listdir(path) if isfile(join(path, f))]

        result: Dict[str, Any] = {}
        for f in files:
            filename = splitext(basename(f))[0]
            result[filename] = []
            with open(f, 'r') as f_input:
                reader = DictReader(f_input)
                for row in reader:
                    result[filename].append(OrderedDict(sorted(row.items())))

        return result


if __name__ == '__main__':
    unittest.main()
