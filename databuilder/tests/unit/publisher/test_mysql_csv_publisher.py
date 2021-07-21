# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import os
import unittest
from typing import Any
from unittest.mock import MagicMock, patch

from freezegun import freeze_time
from pyhocon import ConfigFactory

from databuilder.publisher import mysql_csv_publisher
from databuilder.publisher.mysql_csv_publisher import MySQLCSVPublisher
from tests.unit.models.test_table_serializable import Base

here = os.path.dirname(__file__)


class TestMySQLPublish(unittest.TestCase):

    def setUp(self) -> None:
        resource_path = os.path.join(here, '../resources/mysql_csv_publisher')
        self.conf = ConfigFactory.from_dict(
            {
                MySQLCSVPublisher.CONN_STRING: 'test_connection',
                MySQLCSVPublisher.RECORD_FILES_DIR: f'{resource_path}/records',
                MySQLCSVPublisher.JOB_PUBLISH_TAG: 'test'
            }
        )

    @freeze_time("2021-01-01 01:01:00")
    @patch.object(mysql_csv_publisher, 'sessionmaker')
    @patch.object(mysql_csv_publisher, 'create_engine')
    def test_publisher_old(self, mock_create_engine: Any, mock_session_maker: Any) -> None:
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        mock_session_factory = MagicMock()
        mock_session_maker.return_value = mock_session_factory

        mock_session = MagicMock()
        mock_session_factory.return_value = mock_session

        mock_merge = MagicMock()
        mock_session.merge = mock_merge

        mock_commit = MagicMock()
        mock_session.commit = mock_commit

        mysql_csv_publisher.Base = Base

        publisher = MySQLCSVPublisher()
        publisher.init(self.conf)
        publisher.publish()

        # 5 records
        self.assertEqual(5, mock_merge.call_count)
        # 3 record files
        self.assertEqual(3, mock_commit.call_count)


if __name__ == '__main__':
    unittest.main()
