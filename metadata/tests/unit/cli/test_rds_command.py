# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import unittest
from typing import Any
from unittest.mock import MagicMock, patch

from metadata_service import create_app
from metadata_service.cli import rds_command


class TestRDSCommand(unittest.TestCase):

    def setUp(self) -> None:
        config_module_class = 'metadata_service.config.MySQLConfig'
        self.app = create_app(config_module_class=config_module_class)
        self.app_context = self.app.app_context()
        self.app_context.push()

    @patch.object(rds_command, 'RDSClient')
    def test_cli_init_db(self, mock_rds_client: Any) -> None:
        runner = self.app.test_cli_runner()

        mock_client = MagicMock()
        mock_rds_client.return_value = mock_client

        mock_init_db = MagicMock()
        mock_client.init_db = mock_init_db

        runner.invoke(rds_command.init_db)
        mock_init_db.assert_called_once()

    @patch.object(rds_command, 'RDSClient')
    def test_cli_reset_db(self, mock_rds_client: Any) -> None:
        runner = self.app.test_cli_runner()

        mock_client = MagicMock()
        mock_rds_client.return_value = mock_client

        mock_reset_db = MagicMock()
        mock_client.reset_db = mock_reset_db

        runner.invoke(rds_command.reset_db, ['--yes'])
        mock_reset_db.assert_called_once()


if __name__ == '__main__':
    unittest.main()
