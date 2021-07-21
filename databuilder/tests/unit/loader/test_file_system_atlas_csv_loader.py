# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0
import collections
import csv
import logging
import os
import unittest
from operator import itemgetter
from os import listdir
from os.path import isfile, join
from typing import (
    Any, Callable, Dict, Iterable,
)

from pyhocon import ConfigFactory, ConfigTree

from databuilder.job.base_job import Job
from databuilder.loader.file_system_atlas_csv_loader import FsAtlasCSVLoader
from tests.unit.models.test_atlas_serializable import (
    Actor, City, Movie,
)

here = os.path.dirname(__file__)


class TestFileSystemAtlasCSVLoader(unittest.TestCase):
    def setUp(self) -> None:
        logging.basicConfig(level=logging.INFO)

    def _make_conf(self, test_name: str) -> ConfigTree:
        prefix = '/var/tmp/TestFileSystemAtlasCSVLoader'

        return ConfigFactory.from_dict({
            FsAtlasCSVLoader.ENTITY_DIR_PATH: f'{prefix}/{test_name}/{"entities"}',
            FsAtlasCSVLoader.RELATIONSHIP_DIR_PATH: f'{prefix}/{test_name}/{"relationships"}',
            FsAtlasCSVLoader.SHOULD_DELETE_CREATED_DIR: True,
        })

    def tearDown(self) -> None:
        Job.closer.close()

    def test_load(self) -> None:
        actors = [Actor('Tom Cruise'), Actor('Meg Ryan')]
        cities = [City('San Diego'), City('Oakland')]
        movie = Movie('Top Gun', actors, cities)

        loader = FsAtlasCSVLoader()

        folder = 'movies'
        conf = self._make_conf(folder)

        loader.init(conf)
        loader.load(movie)
        loader.close()

        expected_entity_path = os.path.join(here, f'../resources/fs_atlas_csv_loader/{folder}/entities')
        expected_entities = self._get_csv_rows(expected_entity_path, itemgetter('qualifiedName'))
        actual_entities = self._get_csv_rows(
            conf.get_string(FsAtlasCSVLoader.ENTITY_DIR_PATH),
            itemgetter('qualifiedName'),
        )
        self.assertEqual(expected_entities, actual_entities)

        expected_rel_path = os.path.join(here, f'../resources/fs_atlas_csv_loader/{folder}/relationships')
        expected_relations = self._get_csv_rows(
            expected_rel_path, itemgetter(
                'entityQualifiedName1', 'entityQualifiedName2',
            ),
        )
        actual_relations = self._get_csv_rows(
            conf.get_string(FsAtlasCSVLoader.RELATIONSHIP_DIR_PATH),
            itemgetter('entityQualifiedName1', 'entityQualifiedName2'),
        )
        self.assertEqual(expected_relations, actual_relations)

    def _get_csv_rows(
        self,
        path: str,
        sorting_key_getter: Callable,
    ) -> Iterable[Dict[str, Any]]:
        files = [join(path, f) for f in listdir(path) if isfile(join(path, f))]

        result = []
        for f in files:
            with open(f) as f_input:
                reader = csv.DictReader(f_input)
                for row in reader:
                    result.append(collections.OrderedDict(sorted(row.items())))
        print(result)
        return sorted(result, key=sorting_key_getter)


if __name__ == '__main__':
    unittest.main()
