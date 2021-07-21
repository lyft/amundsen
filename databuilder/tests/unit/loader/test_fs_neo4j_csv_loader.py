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
    Any, Callable, Dict, Iterable, Optional, Union,
)

from pyhocon import ConfigFactory, ConfigTree

from databuilder.job.base_job import Job
from databuilder.loader.file_system_neo4j_csv_loader import FsNeo4jCSVLoader
from databuilder.models.graph_serializable import (
    GraphNode, GraphRelationship, GraphSerializable,
)
from tests.unit.models.test_graph_serializable import (
    Actor, City, Movie,
)

here = os.path.dirname(__file__)


class TestFsNeo4jCSVLoader(unittest.TestCase):
    def setUp(self) -> None:
        logging.basicConfig(level=logging.INFO)

    def tearDown(self) -> None:
        Job.closer.close()

    def test_load(self) -> None:
        actors = [Actor('Tom Cruise'), Actor('Meg Ryan')]
        cities = [City('San Diego'), City('Oakland')]
        movie = Movie('Top Gun', actors, cities)

        loader = FsNeo4jCSVLoader()

        folder = 'movies'
        conf = self._make_conf(folder)

        loader.init(conf)
        loader.load(movie)
        loader.close()

        expected_node_path = os.path.join(here, f'../resources/fs_neo4j_csv_loader/{folder}/nodes')
        expected_nodes = self._get_csv_rows(expected_node_path, itemgetter('KEY'))
        actual_nodes = self._get_csv_rows(conf.get_string(FsNeo4jCSVLoader.NODE_DIR_PATH),
                                          itemgetter('KEY'))
        self.assertEqual(expected_nodes, actual_nodes)

        expected_rel_path = os.path.join(here, f'../resources/fs_neo4j_csv_loader/{folder}/relationships')
        expected_relations = self._get_csv_rows(expected_rel_path, itemgetter('START_KEY', 'END_KEY'))
        actual_relations = self._get_csv_rows(conf.get_string(FsNeo4jCSVLoader.RELATION_DIR_PATH),
                                              itemgetter('START_KEY', 'END_KEY'))
        self.assertEqual(expected_relations, actual_relations)

    def test_load_disjoint_properties(self) -> None:
        people = [
            Person("Taylor", job="Engineer"),
            Person("Griffin", pet="Lion"),
        ]

        loader = FsNeo4jCSVLoader()

        folder = 'people'
        conf = self._make_conf(folder)

        loader.init(conf)
        loader.load(people[0])
        loader.load(people[1])
        loader.close()

        expected_node_path = os.path.join(here, f'../resources/fs_neo4j_csv_loader/{folder}/nodes')
        expected_nodes = self._get_csv_rows(expected_node_path, itemgetter('KEY'))
        actual_nodes = self._get_csv_rows(conf.get_string(FsNeo4jCSVLoader.NODE_DIR_PATH),
                                          itemgetter('KEY'))
        self.assertEqual(expected_nodes, actual_nodes)

    def _make_conf(self, test_name: str) -> ConfigTree:
        prefix = '/var/tmp/TestFsNeo4jCSVLoader'

        return ConfigFactory.from_dict({
            FsNeo4jCSVLoader.NODE_DIR_PATH: f'{prefix}/{test_name}/{"nodes"}',
            FsNeo4jCSVLoader.RELATION_DIR_PATH: f'{prefix}/{test_name}/{"relationships"}',
            FsNeo4jCSVLoader.SHOULD_DELETE_CREATED_DIR: True
        })

    def _get_csv_rows(self,
                      path: str,
                      sorting_key_getter: Callable) -> Iterable[Dict[str, Any]]:
        files = [join(path, f) for f in listdir(path) if isfile(join(path, f))]

        result = []
        for f in files:
            with open(f, 'r') as f_input:
                reader = csv.DictReader(f_input)
                for row in reader:
                    result.append(collections.OrderedDict(sorted(row.items())))

        return sorted(result, key=sorting_key_getter)


class Person(GraphSerializable):
    """ A Person has multiple optional attributes. When an attribute is None,
        it is not included in the resulting node.
    """
    LABEL = 'Person'
    KEY_FORMAT = 'person://{}'

    def __init__(self,
                 name: str,
                 *,
                 pet: Optional[str] = None,
                 job: Optional[str] = None,
                 ) -> None:
        self._name = name
        self._pet = pet
        self._job = job
        self._node_iter = iter(self.create_nodes())

    def create_next_node(self) -> Union[GraphNode, None]:
        try:
            return next(self._node_iter)
        except StopIteration:
            return None

    def create_next_relation(self) -> Union[GraphRelationship, None]:
        return None

    def create_nodes(self) -> Iterable[GraphNode]:
        attributes = {"name": self._name}
        if self._pet:
            attributes['pet'] = self._pet
        if self._job:
            attributes['job'] = self._job

        return [GraphNode(
            key=Person.KEY_FORMAT.format(self._name),
            label=Person.LABEL,
            attributes=attributes
        )]


if __name__ == '__main__':
    unittest.main()
