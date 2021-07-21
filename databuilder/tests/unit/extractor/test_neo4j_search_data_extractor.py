# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import unittest
from typing import Any

from mock import patch
from pyhocon import ConfigFactory

from databuilder import Scoped
from databuilder.extractor.neo4j_extractor import Neo4jExtractor
from databuilder.extractor.neo4j_search_data_extractor import Neo4jSearchDataExtractor
from databuilder.publisher.neo4j_csv_publisher import JOB_PUBLISH_TAG


class TestNeo4jExtractor(unittest.TestCase):

    def test_adding_filter(self: Any) -> None:
        extractor = Neo4jSearchDataExtractor()
        actual = extractor._add_publish_tag_filter('foo', 'MATCH (table:Table) {publish_tag_filter} RETURN table')

        self.assertEqual(actual, """MATCH (table:Table) WHERE table.published_tag = 'foo' RETURN table""")

    def test_not_adding_filter(self: Any) -> None:
        extractor = Neo4jSearchDataExtractor()
        actual = extractor._add_publish_tag_filter('', 'MATCH (table:Table) {publish_tag_filter} RETURN table')

        self.assertEqual(actual, """MATCH (table:Table)  RETURN table""")

    def test_default_search_query(self: Any) -> None:
        with patch.object(Neo4jExtractor, '_get_driver'):
            extractor = Neo4jSearchDataExtractor()
            conf = ConfigFactory.from_dict({
                f'extractor.search_data.extractor.neo4j.{Neo4jExtractor.GRAPH_URL_CONFIG_KEY}': 'test-endpoint',
                f'extractor.search_data.extractor.neo4j.{Neo4jExtractor.NEO4J_AUTH_USER}': 'test-user',
                f'extractor.search_data.extractor.neo4j.{Neo4jExtractor.NEO4J_AUTH_PW}': 'test-passwd',
                f'extractor.search_data.{Neo4jSearchDataExtractor.ENTITY_TYPE}': 'dashboard',
            })
            extractor.init(Scoped.get_scoped_conf(conf=conf,
                                                  scope=extractor.get_scope()))
            self.assertEqual(extractor.cypher_query, Neo4jSearchDataExtractor
                             .DEFAULT_NEO4J_DASHBOARD_CYPHER_QUERY.format(publish_tag_filter=''))

    def test_default_search_query_with_tag(self: Any) -> None:
        with patch.object(Neo4jExtractor, '_get_driver'):
            extractor = Neo4jSearchDataExtractor()
            conf = ConfigFactory.from_dict({
                f'extractor.search_data.extractor.neo4j.{Neo4jExtractor.GRAPH_URL_CONFIG_KEY}': 'test-endpoint',
                f'extractor.search_data.extractor.neo4j.{Neo4jExtractor.NEO4J_AUTH_USER}': 'test-user',
                f'extractor.search_data.extractor.neo4j.{Neo4jExtractor.NEO4J_AUTH_PW}': 'test-passwd',
                f'extractor.search_data.{Neo4jSearchDataExtractor.ENTITY_TYPE}': 'dashboard',
                f'extractor.search_data.{JOB_PUBLISH_TAG}': 'test-date',
            })
            extractor.init(Scoped.get_scoped_conf(conf=conf,
                                                  scope=extractor.get_scope()))

            self.assertEqual(extractor.cypher_query,
                             Neo4jSearchDataExtractor.DEFAULT_NEO4J_DASHBOARD_CYPHER_QUERY.format
                             (publish_tag_filter="""WHERE dashboard.published_tag = 'test-date'"""))


if __name__ == '__main__':
    unittest.main()
