# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import shutil
import tempfile
import unittest
from typing import List

from pyhocon import ConfigFactory

from databuilder import Scoped
from databuilder.loader.file_system_csv_loader import FileSystemCSVLoader
from tests.unit.extractor.test_sql_alchemy_extractor import TableMetadataResult


class TestFileSystemCSVLoader(unittest.TestCase):

    def setUp(self) -> None:
        self.temp_dir_path = tempfile.mkdtemp()
        self.dest_file_name = f'{self.temp_dir_path}/test_file.csv'
        self.file_mode = 'w'
        config_dict = {'loader.filesystem.csv.file_path': self.dest_file_name,
                       'loader.filesystem.csv.mode': self.file_mode}
        self.conf = ConfigFactory.from_dict(config_dict)

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir_path)

    def _check_results_helper(self, expected: List[str]) -> None:
        """
        Helper function to compare results with expected outcome
        :param expected: expected result
        """
        with open(self.dest_file_name, 'r') as file:
            for e in expected:
                actual = file.readline().rstrip('\r\n')
                self.assertEqual(set(e.split(',')), set(actual.split(',')))
            self.assertFalse(file.readline())

    def test_empty_loading(self) -> None:
        """
        Test loading functionality with no data
        """
        loader = FileSystemCSVLoader()
        loader.init(conf=Scoped.get_scoped_conf(conf=self.conf,
                                                scope=loader.get_scope()))

        loader.load(None)
        loader.close()

        self._check_results_helper(expected=[])

    def test_loading_with_single_object(self) -> None:
        """
        Test Loading functionality with single python object
        """
        loader = FileSystemCSVLoader()
        loader.init(conf=Scoped.get_scoped_conf(conf=self.conf,
                                                scope=loader.get_scope()))

        data = TableMetadataResult(database='test_database',
                                   schema='test_schema',
                                   name='test_table',
                                   description='test_description',
                                   column_name='test_column_name',
                                   column_type='test_column_type',
                                   column_comment='test_column_comment',
                                   owner='test_owner')
        loader.load(data)
        loader.close()

        expected = [
            ','.join(['database', 'schema', 'name', 'description',
                      'column_name', 'column_type', 'column_comment',
                      'owner']),
            ','.join(['test_database', 'test_schema', 'test_table',
                      'test_description', 'test_column_name',
                      'test_column_type', 'test_column_comment',
                      'test_owner'])
        ]

        self._check_results_helper(expected=expected)

    def test_loading_with_list_of_objects(self) -> None:
        """
        Test Loading functionality with list of objects.
        Check to ensure all objects are added to file
        """
        loader = FileSystemCSVLoader()
        loader.init(conf=Scoped.get_scoped_conf(conf=self.conf,
                                                scope=loader.get_scope()))

        data = [TableMetadataResult(database='test_database',
                                    schema='test_schema',
                                    name='test_table',
                                    description='test_description',
                                    column_name='test_column_name',
                                    column_type='test_column_type',
                                    column_comment='test_column_comment',
                                    owner='test_owner')] * 5

        for d in data:
            loader.load(d)
        loader.close()

        expected = [
            ','.join(['database', 'schema', 'name', 'description',
                      'column_name', 'column_type', 'column_comment',
                      'owner'])
        ]
        expected = expected + [
            ','.join(['test_database', 'test_schema', 'test_table',
                      'test_description', 'test_column_name',
                      'test_column_type', 'test_column_comment', 'test_owner']
                     )
        ] * 5

        self._check_results_helper(expected=expected)
