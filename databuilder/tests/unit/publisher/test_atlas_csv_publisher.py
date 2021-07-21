# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0
import logging
import os
import unittest
from unittest.mock import MagicMock

from pyhocon import ConfigFactory

from databuilder import Scoped
from databuilder.publisher.atlas_csv_publisher import AtlasCSVPublisher


class TestAtlasCsvPublisher(unittest.TestCase):

    def setUp(self) -> None:
        logging.basicConfig(level=logging.INFO)
        self._resource_path = os.path.join(os.path.dirname(__file__), '../resources/atlas_csv_publisher')
        self.mock_atlas_client = MagicMock()

        config_dict = {
            'publisher.atlas_csv_publisher.entity_files_directory': f'{self._resource_path}/entities',
            'publisher.atlas_csv_publisher.relationship_files_directory': f'{self._resource_path}/relationships',
            'publisher.atlas_csv_publisher.batch_size': 1,
            'publisher.atlas_csv_publisher.atlas_client': self.mock_atlas_client,
        }

        self._conf = ConfigFactory.from_dict(config_dict)

    def test_publisher(self) -> None:
        publisher = AtlasCSVPublisher()
        publisher.init(
            conf=Scoped.get_scoped_conf(
                conf=self._conf,
                scope=publisher.get_scope(),
            ),
        )
        publisher.publish()

        # 4 entities to create
        self.assertEqual(self.mock_atlas_client.entity.create_entities.call_count, 4)

        # 1 entity to update
        self.assertEqual(self.mock_atlas_client.entity.update_entity.call_count, 1)

        # 2 relationships to create
        self.assertEqual(self.mock_atlas_client.relationship.create_relationship.call_count, 2)
