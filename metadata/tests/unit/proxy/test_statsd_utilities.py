# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import unittest
from unittest.mock import MagicMock, patch

from flask import current_app
from neo4j import GraphDatabase
from statsd import StatsClient

from metadata_service import create_app
from metadata_service.proxy import statsd_utilities
from metadata_service.proxy.neo4j_proxy import Neo4jProxy
from metadata_service.proxy.statsd_utilities import _get_statsd_client


class TestStatsdUtilities(unittest.TestCase):
    def setUp(self) -> None:
        self.app = create_app(config_module_class='metadata_service.config.LocalConfig')
        self.app_context = self.app.app_context()
        self.app_context.push()

    def test_no_statsd_client(self) -> None:
        with patch.object(StatsClient, '__init__'):
            statsd_client = _get_statsd_client(prefix='foo')
            self.assertIsNone(statsd_client)

    def test_get_statsd_client(self) -> None:
        with patch.object(current_app, 'config') as mock_config, \
                patch.object(StatsClient, '__init__', return_value=None) as mock_statsd_init:
            mock_config.return_value.single.return_value = True

            statsd_client1 = _get_statsd_client(prefix='foo')
            self.assertIsNotNone(statsd_client1)
            statsd_client2 = _get_statsd_client(prefix='foo')
            self.assertIsNotNone(statsd_client2)
            self.assertEqual(statsd_client1, statsd_client2)

            self.assertEqual(mock_statsd_init.call_count, 1)

            statsd_client3 = _get_statsd_client(prefix='bar')
            self.assertIsNotNone(statsd_client3)
            statsd_client4 = _get_statsd_client(prefix='bar')
            self.assertIsNotNone(statsd_client4)
            self.assertEqual(statsd_client3, statsd_client4)

            self.assertNotEqual(statsd_client1, statsd_client3)
            self.assertEqual(mock_statsd_init.call_count, 2)

    def test_with_neo4j_proxy(self) -> None:
        with patch.object(GraphDatabase, 'driver'), \
                patch.object(Neo4jProxy, '_execute_cypher_query'), \
                patch.object(statsd_utilities, '_get_statsd_client') as mock_statsd_client:

            mock_success_incr = MagicMock()
            mock_statsd_client.return_value.incr = mock_success_incr

            neo4j_proxy = Neo4jProxy(host='DOES_NOT_MATTER', port=0000)
            neo4j_proxy.add_owner(table_uri='bogus_uri', owner='foo')

            self.assertEqual(mock_success_incr.call_count, 2)


if __name__ == '__main__':
    unittest.main()
