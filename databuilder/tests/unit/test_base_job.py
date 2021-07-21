# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import json
import logging
import shutil
import tempfile
import unittest
from typing import Any

from mock import patch
from pyhocon import ConfigFactory, ConfigTree

from databuilder.extractor.base_extractor import Extractor
from databuilder.job.job import DefaultJob
from databuilder.loader.base_loader import Loader
from databuilder.task.task import DefaultTask
from databuilder.transformer.base_transformer import Transformer

LOGGER = logging.getLogger(__name__)


class TestJob(unittest.TestCase):

    def setUp(self) -> None:
        self.temp_dir_path = tempfile.mkdtemp()
        self.dest_file_name = f'{self.temp_dir_path}/superhero.json'
        self.conf = ConfigFactory.from_dict({'loader.superhero.dest_file': self.dest_file_name})

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir_path)

    def test_job(self) -> None:
        with patch("databuilder.job.job.StatsClient") as mock_statsd:
            task = DefaultTask(SuperHeroExtractor(),
                               SuperHeroLoader(),
                               transformer=SuperHeroReverseNameTransformer())

            job = DefaultJob(self.conf, task)
            job.launch()

            expected_list = ['{"hero": "Super man", "name": "tneK kralC"}',
                             '{"hero": "Bat man", "name": "enyaW ecurB"}']
            with open(self.dest_file_name, 'r') as file:
                for expected in expected_list:
                    actual = file.readline().rstrip('\n')
                    self.assertEqual(expected, actual)
                self.assertFalse(file.readline())

        self.assertEqual(mock_statsd.call_count, 0)


class TestJobNoTransform(unittest.TestCase):

    def setUp(self) -> None:
        self.temp_dir_path = tempfile.mkdtemp()
        self.dest_file_name = f'{self.temp_dir_path}/superhero.json'
        self.conf = ConfigFactory.from_dict(
            {'loader.superhero.dest_file': self.dest_file_name})

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir_path)

    def test_job(self) -> None:
        task = DefaultTask(SuperHeroExtractor(), SuperHeroLoader())

        job = DefaultJob(self.conf, task)
        job.launch()

        expected_list = ['{"hero": "Super man", "name": "Clark Kent"}',
                         '{"hero": "Bat man", "name": "Bruce Wayne"}']
        with open(self.dest_file_name, 'r') as file:
            for expected in expected_list:
                actual = file.readline().rstrip('\n')
                self.assertEqual(expected, actual)
            self.assertFalse(file.readline())


class TestJobStatsd(unittest.TestCase):

    def setUp(self) -> None:
        self.temp_dir_path = tempfile.mkdtemp()
        self.dest_file_name = f'{self.temp_dir_path}/superhero.json'
        self.conf = ConfigFactory.from_dict(
            {'loader.superhero.dest_file': self.dest_file_name,
             'job.is_statsd_enabled': True,
             'job.identifier': 'foobar'})

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir_path)

    def test_job(self) -> None:
        with patch("databuilder.job.job.StatsClient") as mock_statsd:
            task = DefaultTask(SuperHeroExtractor(), SuperHeroLoader())

            job = DefaultJob(self.conf, task)
            job.launch()

            expected_list = ['{"hero": "Super man", "name": "Clark Kent"}',
                             '{"hero": "Bat man", "name": "Bruce Wayne"}']
            with open(self.dest_file_name, 'r') as file:
                for expected in expected_list:
                    actual = file.readline().rstrip('\n')
                    self.assertEqual(expected, actual)
                self.assertFalse(file.readline())

            self.assertEqual(mock_statsd.return_value.incr.call_count, 1)


class SuperHeroExtractor(Extractor):
    def __init__(self) -> None:
        pass

    def init(self, conf: ConfigTree) -> None:
        self.records = [SuperHero(hero='Super man', name='Clark Kent'),
                        SuperHero(hero='Bat man', name='Bruce Wayne')]
        self.iter = iter(self.records)

    def extract(self) -> Any:
        try:
            return next(self.iter)
        except StopIteration:
            return None

    def get_scope(self) -> str:
        return 'extractor.superhero'


class SuperHero:
    def __init__(self,
                 hero: str,
                 name: str) -> None:
        self.hero = hero
        self.name = name

    def __repr__(self) -> str:
        return f'SuperHero(hero={self.hero}, name={self.name})'


class SuperHeroReverseNameTransformer(Transformer):
    def __init__(self) -> None:
        pass

    def init(self, conf: ConfigTree) -> None:
        pass

    def transform(self, record: Any) -> Any:
        record.name = record.name[::-1]
        return record

    def get_scope(self) -> str:
        return 'transformer.superhero'


class SuperHeroLoader(Loader):
    def init(self, conf: ConfigTree) -> None:
        self.conf = conf
        dest_file_path = self.conf.get_string('dest_file')
        LOGGER.info('Loading to %s', dest_file_path)
        self.dest_file_obj = open(self.conf.get_string('dest_file'), 'w')

    def load(self, record: Any) -> None:
        rec = json.dumps(record.__dict__, sort_keys=True)
        LOGGER.info('Writing record: %s', rec)
        self.dest_file_obj.write(f'{rec}\n')
        self.dest_file_obj.flush()

    def get_scope(self) -> str:
        return 'loader.superhero'


if __name__ == '__main__':
    unittest.main()
