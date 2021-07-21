# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import logging
import os
import unittest
import uuid

from mock import MagicMock, patch
from neo4j import GraphDatabase
from pyhocon import ConfigFactory

from databuilder.publisher import neo4j_csv_publisher
from databuilder.publisher.neo4j_csv_publisher import Neo4jCsvPublisher

here = os.path.dirname(__file__)


class TestPublish(unittest.TestCase):

    def setUp(self) -> None:
        logging.basicConfig(level=logging.INFO)
        self._resource_path = os.path.join(here, '../resources/csv_publisher')

    def test_publisher(self) -> None:
        with patch.object(GraphDatabase, 'driver') as mock_driver:
            mock_session = MagicMock()
            mock_driver.return_value.session.return_value = mock_session

            mock_transaction = MagicMock()
            mock_session.begin_transaction.return_value = mock_transaction

            mock_run = MagicMock()
            mock_transaction.run = mock_run
            mock_commit = MagicMock()
            mock_transaction.commit = mock_commit

            publisher = Neo4jCsvPublisher()

            conf = ConfigFactory.from_dict(
                {neo4j_csv_publisher.NEO4J_END_POINT_KEY: 'dummy://999.999.999.999:7687/',
                 neo4j_csv_publisher.NODE_FILES_DIR: f'{self._resource_path}/nodes',
                 neo4j_csv_publisher.RELATION_FILES_DIR: f'{self._resource_path}/relations',
                 neo4j_csv_publisher.NEO4J_USER: 'neo4j_user',
                 neo4j_csv_publisher.NEO4J_PASSWORD: 'neo4j_password',
                 neo4j_csv_publisher.JOB_PUBLISH_TAG: str(uuid.uuid4())}
            )
            publisher.init(conf)
            publisher.publish()

            self.assertEqual(mock_run.call_count, 6)

            # 2 node files, 1 relation file
            self.assertEqual(mock_commit.call_count, 1)

    def test_preprocessor(self) -> None:
        with patch.object(GraphDatabase, 'driver') as mock_driver:
            mock_session = MagicMock()
            mock_driver.return_value.session.return_value = mock_session

            mock_transaction = MagicMock()
            mock_session.begin_transaction.return_value = mock_transaction

            mock_run = MagicMock()
            mock_transaction.run = mock_run
            mock_commit = MagicMock()
            mock_transaction.commit = mock_commit

            mock_preprocessor = MagicMock()
            mock_preprocessor.is_perform_preprocess.return_value = MagicMock(return_value=True)
            mock_preprocessor.preprocess_cypher.return_value = ('MATCH (f:Foo) RETURN f', {})

            publisher = Neo4jCsvPublisher()

            conf = ConfigFactory.from_dict(
                {neo4j_csv_publisher.NEO4J_END_POINT_KEY: 'dummy://999.999.999.999:7687/',
                 neo4j_csv_publisher.NODE_FILES_DIR: f'{self._resource_path}/nodes',
                 neo4j_csv_publisher.RELATION_FILES_DIR: f'{self._resource_path}/relations',
                 neo4j_csv_publisher.RELATION_PREPROCESSOR: mock_preprocessor,
                 neo4j_csv_publisher.NEO4J_USER: 'neo4j_user',
                 neo4j_csv_publisher.NEO4J_PASSWORD: 'neo4j_password',
                 neo4j_csv_publisher.JOB_PUBLISH_TAG: str(uuid.uuid4())}
            )
            publisher.init(conf)
            publisher.publish()

            self.assertEqual(mock_run.call_count, 8)

            # 2 node files, 1 relation file
            self.assertEqual(mock_commit.call_count, 1)


if __name__ == '__main__':
    unittest.main()
