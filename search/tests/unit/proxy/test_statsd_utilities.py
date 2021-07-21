# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import unittest

from flask import current_app
from mock import MagicMock, patch
from statsd import StatsClient

from search_service import create_app
from search_service.proxy import statsd_utilities
from search_service.proxy.elasticsearch import ElasticsearchProxy
from search_service.proxy.statsd_utilities import _get_statsd_client


class TestStatsdUtilities(unittest.TestCase):
    def setUp(self) -> None:
        self.app = create_app(config_module_class='search_service.config.LocalConfig')
        self.app_context = self.app.app_context()
        self.app_context.push()

    def test_no_statsd_client(self) -> None:
        with patch.object(StatsClient, '__init__'):
            statsd_client = _get_statsd_client(prefix='foo')
            self.assertIsNone(statsd_client)

    def test_get_statsd_client(self) -> None:
        with patch.object(current_app, 'config') as mock_config, \
                patch.object(StatsClient, '__init__', return_value=None):
            mock_config.return_value.single.return_value = True

            statsd_client1 = _get_statsd_client(prefix='test')
            self.assertIsNotNone(statsd_client1)

    def test_same_statsd_client_for_same_prefix(self) -> None:
        with patch.object(current_app, 'config') as mock_config, \
                patch.object(StatsClient, '__init__', return_value=None) as mock_statsd_init:
            mock_config.return_value.single.return_value = True

            statsd_client1 = _get_statsd_client(prefix='test_same')
            self.assertIsNotNone(statsd_client1)
            statsd_client2 = _get_statsd_client(prefix='test_same')
            self.assertIsNotNone(statsd_client2)
            self.assertEqual(statsd_client1, statsd_client2)

            self.assertEqual(mock_statsd_init.call_count, 1)

    def test_different_statsd_client_for_different_prefix(self) -> None:
        with patch.object(current_app, 'config') as mock_config, \
                patch.object(StatsClient, '__init__', return_value=None) as mock_statsd_init:
            mock_config.return_value.single.return_value = True

            statsd_client1 = _get_statsd_client(prefix='test_diff')
            self.assertIsNotNone(statsd_client1)

            statsd_client2 = _get_statsd_client(prefix='test_diff2')
            self.assertIsNotNone(statsd_client2)

            self.assertNotEqual(statsd_client1, statsd_client2)
            self.assertEqual(mock_statsd_init.call_count, 2)

    @patch('elasticsearch_dsl.Search.execute')
    def test_with_elasticsearch_proxy(self,
                                      mock_search: MagicMock) -> None:

        mock_elasticsearch_client = MagicMock()
        es_proxy = ElasticsearchProxy(client=mock_elasticsearch_client)

        with patch.object(statsd_utilities, '_get_statsd_client') as mock_statsd_client:
            mock_success_incr = MagicMock()
            mock_statsd_client.return_value.incr = mock_success_incr

            es_proxy.fetch_table_search_results(query_term='DOES_NOT_MATTER')

            self.assertEqual(mock_success_incr.call_count, 1)
