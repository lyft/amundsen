# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

# Validation of Cypher statements causing Flake8 to fail. Disabling it on this file only
# flake8: noqa

import logging
import textwrap
import unittest

from mock import patch
from neo4j import GraphDatabase
from pyhocon import ConfigFactory

from databuilder.publisher import neo4j_csv_publisher
from databuilder.task import neo4j_staleness_removal_task
from databuilder.task.neo4j_staleness_removal_task import Neo4jStalenessRemovalTask


class TestRemoveStaleData(unittest.TestCase):

    def setUp(self) -> None:
        logging.basicConfig(level=logging.INFO)

    def test_validation_failure(self) -> None:

        with patch.object(GraphDatabase, 'driver'):
            task = Neo4jStalenessRemovalTask()
            job_config = ConfigFactory.from_dict({
                f'job.identifier': 'remove_stale_data_job',
                f'{task.get_scope()}.{neo4j_staleness_removal_task.NEO4J_END_POINT_KEY}': 'foobar',
                f'{task.get_scope()}.{neo4j_staleness_removal_task.NEO4J_USER}': 'foo',
                f'{task.get_scope()}.{neo4j_staleness_removal_task.NEO4J_PASSWORD}': 'bar',
                f'{task.get_scope()}.{neo4j_staleness_removal_task.STALENESS_MAX_PCT}': 90,
                neo4j_csv_publisher.JOB_PUBLISH_TAG: 'foo'
            })

            task.init(job_config)
            total_records = [{'type': 'foo', 'count': 100}]
            stale_records = [{'type': 'foo', 'count': 50}]
            targets = {'foo'}
            task._validate_staleness_pct(total_records=total_records, stale_records=stale_records, types=targets)

    def test_validation(self) -> None:

        with patch.object(GraphDatabase, 'driver'):
            task = Neo4jStalenessRemovalTask()
            job_config = ConfigFactory.from_dict({
                f'job.identifier': 'remove_stale_data_job',
                f'{task.get_scope()}.{neo4j_staleness_removal_task.NEO4J_END_POINT_KEY}': 'foobar',
                f'{task.get_scope()}.{neo4j_staleness_removal_task.NEO4J_USER}': 'foo',
                f'{task.get_scope()}.{neo4j_staleness_removal_task.NEO4J_PASSWORD}': 'bar',
                f'{task.get_scope()}.{neo4j_staleness_removal_task.STALENESS_MAX_PCT}': 5,
                neo4j_csv_publisher.JOB_PUBLISH_TAG: 'foo'
            })

            task.init(job_config)
            total_records = [{'type': 'foo', 'count': 100}]
            stale_records = [{'type': 'foo', 'count': 50}]
            targets = {'foo'}
            self.assertRaises(Exception, task._validate_staleness_pct, total_records, stale_records, targets)

    def test_validation_threshold_override(self) -> None:

        with patch.object(GraphDatabase, 'driver'):
            task = Neo4jStalenessRemovalTask()
            job_config = ConfigFactory.from_dict({
                f'job.identifier': 'remove_stale_data_job',
                f'{task.get_scope()}.{neo4j_staleness_removal_task.NEO4J_END_POINT_KEY}': 'foobar',
                f'{task.get_scope()}.{neo4j_staleness_removal_task.NEO4J_USER}': 'foo',
                f'{task.get_scope()}.{neo4j_staleness_removal_task.NEO4J_PASSWORD}': 'bar',
                f'{task.get_scope()}.{neo4j_staleness_removal_task.STALENESS_MAX_PCT}': 5,
                f'{task.get_scope()}.{neo4j_staleness_removal_task.STALENESS_PCT_MAX_DICT}': {'foo': 51},
                neo4j_csv_publisher.JOB_PUBLISH_TAG: 'foo'
            })

            task.init(job_config)
            total_records = [{'type': 'foo', 'count': 100},
                             {'type': 'bar', 'count': 100}]
            stale_records = [{'type': 'foo', 'count': 50},
                             {'type': 'bar', 'count': 3}]
            targets = {'foo', 'bar'}
            task._validate_staleness_pct(total_records=total_records, stale_records=stale_records, types=targets)

    def test_marker(self) -> None:
        with patch.object(GraphDatabase, 'driver'):
            task = Neo4jStalenessRemovalTask()
            job_config = ConfigFactory.from_dict({
                f'job.identifier': 'remove_stale_data_job',
                f'{task.get_scope()}.{neo4j_staleness_removal_task.NEO4J_END_POINT_KEY}': 'foobar',
                f'{task.get_scope()}.{neo4j_staleness_removal_task.NEO4J_USER}': 'foo',
                f'{task.get_scope()}.{neo4j_staleness_removal_task.NEO4J_PASSWORD}': 'bar',
                f'{task.get_scope()}.{neo4j_staleness_removal_task.STALENESS_MAX_PCT}': 5,
                neo4j_csv_publisher.JOB_PUBLISH_TAG: 'foo'
            })

            task.init(job_config)
            self.assertIsNone(task.ms_to_expire)
            self.assertEqual(task.marker, 'foo')

            task = Neo4jStalenessRemovalTask()
            job_config = ConfigFactory.from_dict({
                f'job.identifier': 'remove_stale_data_job',
                f'{task.get_scope()}.{neo4j_staleness_removal_task.NEO4J_END_POINT_KEY}': 'foobar',
                f'{task.get_scope()}.{neo4j_staleness_removal_task.NEO4J_USER}': 'foo',
                f'{task.get_scope()}.{neo4j_staleness_removal_task.NEO4J_PASSWORD}': 'bar',
                f'{task.get_scope()}.{neo4j_staleness_removal_task.STALENESS_MAX_PCT}': 5,
                f'{task.get_scope()}.{neo4j_staleness_removal_task.MS_TO_EXPIRE}': 86400000,
            })

            task.init(job_config)
            self.assertIsNotNone(task.ms_to_expire)
            self.assertEqual(task.marker, 86400000)

    def test_validation_statement_publish_tag(self) -> None:
        with patch.object(GraphDatabase, 'driver'), patch.object(Neo4jStalenessRemovalTask, '_execute_cypher_query') \
                as mock_execute:
            task = Neo4jStalenessRemovalTask()
            job_config = ConfigFactory.from_dict({
                f'job.identifier': 'remove_stale_data_job',
                f'{task.get_scope()}.{neo4j_staleness_removal_task.NEO4J_END_POINT_KEY}': 'foobar',
                f'{task.get_scope()}.{neo4j_staleness_removal_task.NEO4J_USER}': 'foo',
                f'{task.get_scope()}.{neo4j_staleness_removal_task.NEO4J_PASSWORD}': 'bar',
                f'{task.get_scope()}.{neo4j_staleness_removal_task.STALENESS_MAX_PCT}': 5,
                f'{task.get_scope()}.{neo4j_staleness_removal_task.TARGET_NODES}': ['Foo'],
                neo4j_csv_publisher.JOB_PUBLISH_TAG: 'foo',
            })

            task.init(job_config)
            task._validate_node_staleness_pct()

            mock_execute.assert_called()
            mock_execute.assert_any_call(statement=textwrap.dedent("""
            MATCH (n)
            WITH DISTINCT labels(n) as node, count(*) as count
            RETURN head(node) as type, count
            """))

            mock_execute.assert_any_call(param_dict={'marker': u'foo'},
                                         statement=textwrap.dedent("""
            MATCH (n)
            WHERE{}
            n.published_tag <> $marker
            OR NOT EXISTS(n.published_tag)
            WITH DISTINCT labels(n) as node, count(*) as count
            RETURN head(node) as type, count
            """.format(' ')))

            task._validate_relation_staleness_pct()
            mock_execute.assert_any_call(param_dict={'marker': u'foo'},
                                         statement=textwrap.dedent("""
            MATCH ()-[n]-()
            WHERE{}
            n.published_tag <> $marker
            OR NOT EXISTS(n.published_tag)
            RETURN type(n) as type, count(*) as count
            """.format(' ')))

    def test_validation_statement_ms_to_expire(self) -> None:
        with patch.object(GraphDatabase, 'driver'), patch.object(Neo4jStalenessRemovalTask, '_execute_cypher_query') \
                as mock_execute:
            task = Neo4jStalenessRemovalTask()
            job_config = ConfigFactory.from_dict({
                f'job.identifier': 'remove_stale_data_job',
                f'{task.get_scope()}.{neo4j_staleness_removal_task.NEO4J_END_POINT_KEY}': 'foobar',
                f'{task.get_scope()}.{neo4j_staleness_removal_task.NEO4J_USER}': 'foo',
                f'{task.get_scope()}.{neo4j_staleness_removal_task.NEO4J_PASSWORD}': 'bar',
                f'{task.get_scope()}.{neo4j_staleness_removal_task.STALENESS_MAX_PCT}': 5,
                f'{task.get_scope()}.{neo4j_staleness_removal_task.MS_TO_EXPIRE}': 9876543210
            })

            task.init(job_config)
            task._validate_node_staleness_pct()

            mock_execute.assert_called()
            mock_execute.assert_any_call(statement=textwrap.dedent("""
            MATCH (n)
            WITH DISTINCT labels(n) as node, count(*) as count
            RETURN head(node) as type, count
            """))

            mock_execute.assert_any_call(param_dict={'marker': 9876543210},
                                         statement=textwrap.dedent("""
            MATCH (n)
            WHERE{}
            n.publisher_last_updated_epoch_ms < (timestamp() - $marker)
            OR NOT EXISTS(n.publisher_last_updated_epoch_ms)
            WITH DISTINCT labels(n) as node, count(*) as count
            RETURN head(node) as type, count
            """.format(' ')))

            task._validate_relation_staleness_pct()
            mock_execute.assert_any_call(param_dict={'marker': 9876543210},
                                         statement=textwrap.dedent("""
            MATCH ()-[n]-()
            WHERE{}
            n.publisher_last_updated_epoch_ms < (timestamp() - $marker)
            OR NOT EXISTS(n.publisher_last_updated_epoch_ms)
            RETURN type(n) as type, count(*) as count
            """.format(' ')))

    def test_delete_statement_publish_tag(self) -> None:
        with patch.object(GraphDatabase, 'driver'), patch.object(Neo4jStalenessRemovalTask, '_execute_cypher_query') \
                as mock_execute:
            mock_execute.return_value.single.return_value = {'count': 0}
            task = Neo4jStalenessRemovalTask()
            job_config = ConfigFactory.from_dict({
                f'job.identifier': 'remove_stale_data_job',
                f'{task.get_scope()}.{neo4j_staleness_removal_task.NEO4J_END_POINT_KEY}': 'foobar',
                f'{task.get_scope()}.{neo4j_staleness_removal_task.NEO4J_USER}': 'foo',
                f'{task.get_scope()}.{neo4j_staleness_removal_task.NEO4J_PASSWORD}': 'bar',
                f'{task.get_scope()}.{neo4j_staleness_removal_task.STALENESS_MAX_PCT}': 5,
                f'{task.get_scope()}.{neo4j_staleness_removal_task.TARGET_NODES}': ['Foo'],
                f'{task.get_scope()}.{neo4j_staleness_removal_task.TARGET_RELATIONS}': ['BAR'],
                neo4j_csv_publisher.JOB_PUBLISH_TAG: 'foo',
            })

            task.init(job_config)
            task._delete_stale_nodes()
            task._delete_stale_relations()

            mock_execute.assert_any_call(dry_run=False,
                                         param_dict={'marker': u'foo', 'batch_size': 100},
                                         statement=textwrap.dedent("""
            MATCH (n:Foo)
            WHERE{}
            n.published_tag <> $marker
            OR NOT EXISTS(n.published_tag)
            WITH n LIMIT $batch_size
            DETACH DELETE (n)
            RETURN COUNT(*) as count;
            """.format(' ')))

            mock_execute.assert_any_call(dry_run=False,
                                         param_dict={'marker': u'foo', 'batch_size': 100},
                                         statement=textwrap.dedent("""
            MATCH ()-[n:BAR]-()
            WHERE{}
            n.published_tag <> $marker
            OR NOT EXISTS(n.published_tag)
            WITH n LIMIT $batch_size
            DELETE n
            RETURN count(*) as count;
                        """.format(' ')))

    def test_delete_statement_ms_to_expire(self) -> None:
        with patch.object(GraphDatabase, 'driver'), patch.object(Neo4jStalenessRemovalTask, '_execute_cypher_query') \
                as mock_execute:
            mock_execute.return_value.single.return_value = {'count': 0}
            task = Neo4jStalenessRemovalTask()
            job_config = ConfigFactory.from_dict({
                f'job.identifier': 'remove_stale_data_job',
                f'{task.get_scope()}.{neo4j_staleness_removal_task.NEO4J_END_POINT_KEY}': 'foobar',
                f'{task.get_scope()}.{neo4j_staleness_removal_task.NEO4J_USER}': 'foo',
                f'{task.get_scope()}.{neo4j_staleness_removal_task.NEO4J_PASSWORD}': 'bar',
                f'{task.get_scope()}.{neo4j_staleness_removal_task.STALENESS_MAX_PCT}': 5,
                f'{task.get_scope()}.{neo4j_staleness_removal_task.TARGET_NODES}': ['Foo'],
                f'{task.get_scope()}.{neo4j_staleness_removal_task.TARGET_RELATIONS}': ['BAR'],
                f'{task.get_scope()}.{neo4j_staleness_removal_task.MS_TO_EXPIRE}': 9876543210
            })

            task.init(job_config)
            task._delete_stale_nodes()
            task._delete_stale_relations()

            mock_execute.assert_any_call(dry_run=False,
                                         param_dict={'marker': 9876543210, 'batch_size': 100},
                                         statement=textwrap.dedent("""
            MATCH (n:Foo)
            WHERE{}
            n.publisher_last_updated_epoch_ms < (timestamp() - $marker)
            OR NOT EXISTS(n.publisher_last_updated_epoch_ms)
            WITH n LIMIT $batch_size
            DETACH DELETE (n)
            RETURN COUNT(*) as count;
            """.format(' ')))

            mock_execute.assert_any_call(dry_run=False,
                                         param_dict={'marker': 9876543210, 'batch_size': 100},
                                         statement=textwrap.dedent("""
            MATCH ()-[n:BAR]-()
            WHERE{}
            n.publisher_last_updated_epoch_ms < (timestamp() - $marker)
            OR NOT EXISTS(n.publisher_last_updated_epoch_ms)
            WITH n LIMIT $batch_size
            DELETE n
            RETURN count(*) as count;
                        """.format(' ')))

    def test_ms_to_expire_too_small(self) -> None:
        with patch.object(GraphDatabase, 'driver'):
            task = Neo4jStalenessRemovalTask()
            job_config = ConfigFactory.from_dict({
                f'job.identifier': 'remove_stale_data_job',
                f'{task.get_scope()}.{neo4j_staleness_removal_task.NEO4J_END_POINT_KEY}': 'foobar',
                f'{task.get_scope()}.{neo4j_staleness_removal_task.NEO4J_USER}': 'foo',
                f'{task.get_scope()}.{neo4j_staleness_removal_task.NEO4J_PASSWORD}': 'bar',
                f'{task.get_scope()}.{neo4j_staleness_removal_task.STALENESS_MAX_PCT}': 5,
                f'{task.get_scope()}.{neo4j_staleness_removal_task.TARGET_NODES}': ['Foo'],
                f'{task.get_scope()}.{neo4j_staleness_removal_task.TARGET_RELATIONS}': ['BAR'],
                f'{task.get_scope()}.{neo4j_staleness_removal_task.MS_TO_EXPIRE}': 24 * 60 * 60 * 100 - 10
            })

            try:
                task.init(job_config)
                self.assertTrue(False, 'Should have failed with small TTL   ')
            except Exception:
                pass

        with patch.object(GraphDatabase, 'driver'):
            task = Neo4jStalenessRemovalTask()
            job_config = ConfigFactory.from_dict({
                f'job.identifier': 'remove_stale_data_job',
                f'{task.get_scope()}.{neo4j_staleness_removal_task.NEO4J_END_POINT_KEY}': 'foobar',
                f'{task.get_scope()}.{neo4j_staleness_removal_task.NEO4J_USER}': 'foo',
                f'{task.get_scope()}.{neo4j_staleness_removal_task.NEO4J_PASSWORD}': 'bar',
                f'{task.get_scope()}.{neo4j_staleness_removal_task.STALENESS_MAX_PCT}': 5,
                f'{task.get_scope()}.{neo4j_staleness_removal_task.TARGET_NODES}': ['Foo'],
                f'{task.get_scope()}.{neo4j_staleness_removal_task.TARGET_RELATIONS}': ['BAR'],
                f'{task.get_scope()}.{neo4j_staleness_removal_task.MS_TO_EXPIRE}': 24 * 60 * 60 * 1000,
            })
            task.init(job_config)

    def test_delete_dry_run(self) -> None:
        with patch.object(GraphDatabase, 'driver') as mock_driver:
            session_mock = mock_driver.return_value.session

            task = Neo4jStalenessRemovalTask()
            job_config = ConfigFactory.from_dict({
                f'job.identifier': 'remove_stale_data_job',
                f'{task.get_scope()}.{neo4j_staleness_removal_task.NEO4J_END_POINT_KEY}': 'foobar',
                f'{task.get_scope()}.{neo4j_staleness_removal_task.NEO4J_USER}': 'foo',
                f'{task.get_scope()}.{neo4j_staleness_removal_task.NEO4J_PASSWORD}': 'bar',
                f'{task.get_scope()}.{neo4j_staleness_removal_task.STALENESS_MAX_PCT}': 5,
                f'{task.get_scope()}.{neo4j_staleness_removal_task.TARGET_NODES}': ['Foo'],
                f'{task.get_scope()}.{neo4j_staleness_removal_task.TARGET_RELATIONS}': ['BAR'],
                f'{task.get_scope()}.{neo4j_staleness_removal_task.DRY_RUN}': True,
                neo4j_csv_publisher.JOB_PUBLISH_TAG: 'foo',
            })

            task.init(job_config)
            task._delete_stale_nodes()
            task._delete_stale_relations()

            session_mock.assert_not_called()


if __name__ == '__main__':
    unittest.main()
