# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import logging
import unittest
from typing import Any
from unittest.mock import patch

from amundsen_rds.models.table import Table
from pyhocon import ConfigFactory

from databuilder.publisher.mysql_csv_publisher import MySQLCSVPublisher
from databuilder.task import mysql_staleness_removal_task
from databuilder.task.mysql_staleness_removal_task import MySQLStalenessRemovalTask


class TestMySQLStalenessRemovalTask(unittest.TestCase):

    def setUp(self) -> None:
        logging.basicConfig(level=logging.INFO)

    @patch.object(mysql_staleness_removal_task, 'sessionmaker')
    @patch.object(mysql_staleness_removal_task, 'create_engine')
    def test_marker(self, mock_create_engine: Any, mock_session_maker: Any) -> None:
        task = MySQLStalenessRemovalTask()
        job_config = ConfigFactory.from_dict({
            'job.identifier': 'mysql_remove_stale_data_job',
            f'{task.get_scope()}.{MySQLStalenessRemovalTask.CONN_STRING}': 'foobar',
            f'{task.get_scope()}.{MySQLStalenessRemovalTask.STALENESS_MAX_PCT}': 5,
            MySQLCSVPublisher.JOB_PUBLISH_TAG: 'foo'
        })
        task.init(job_config)

        self.assertIsNone(task.ms_to_expire)
        self.assertEqual(task.marker, 'foo')

        task = MySQLStalenessRemovalTask()
        job_config = ConfigFactory.from_dict({
            'job.identifier': 'mysql_remove_stale_data_job',
            f'{task.get_scope()}.{MySQLStalenessRemovalTask.CONN_STRING}': 'foobar',
            f'{task.get_scope()}.{MySQLStalenessRemovalTask.STALENESS_MAX_PCT}': 5,
            f'{task.get_scope()}.{MySQLStalenessRemovalTask.MS_TO_EXPIRE}': 86400000
        })
        task.init(job_config)

        self.assertIsNotNone(task.ms_to_expire)
        self.assertEqual(task.marker, 86400000)

    @patch.object(mysql_staleness_removal_task, 'sessionmaker')
    @patch.object(mysql_staleness_removal_task, 'create_engine')
    def test_config_with_publish_tag_and_ms_to_expire(self, mock_create_engine: Any, mock_session_maker: Any) -> None:
        task = MySQLStalenessRemovalTask()
        job_config = ConfigFactory.from_dict({
            'job.identifier': 'mysql_remove_stale_data_job',
            f'{task.get_scope()}.{MySQLStalenessRemovalTask.CONN_STRING}': 'foobar',
            f'{task.get_scope()}.{MySQLStalenessRemovalTask.STALENESS_MAX_PCT}': 5,
            f'{task.get_scope()}.{MySQLStalenessRemovalTask.MS_TO_EXPIRE}': 86400000,
            MySQLCSVPublisher.JOB_PUBLISH_TAG: 'foo'
        })

        self.assertRaises(Exception, task.init, job_config)

    @patch.object(mysql_staleness_removal_task, 'sessionmaker')
    @patch.object(mysql_staleness_removal_task, 'create_engine')
    def test_ms_to_expire_too_small(self, mock_create_engine: Any, mock_session_maker: Any) -> None:
        task = MySQLStalenessRemovalTask()
        job_config = ConfigFactory.from_dict({
            'job.identifier': 'mysql_remove_stale_data_job',
            f'{task.get_scope()}.{MySQLStalenessRemovalTask.CONN_STRING}': 'foobar',
            f'{task.get_scope()}.{MySQLStalenessRemovalTask.STALENESS_MAX_PCT}': 5,
            f'{task.get_scope()}.{MySQLStalenessRemovalTask.MS_TO_EXPIRE}': 24 * 60 * 60 * 100,
        })

        self.assertRaises(Exception, task.init, job_config)

    @patch.object(mysql_staleness_removal_task, 'sessionmaker')
    @patch.object(mysql_staleness_removal_task, 'create_engine')
    def test_validation_threshold_override(self, mock_create_engine: Any, mock_session_maker: Any) -> None:
        task = MySQLStalenessRemovalTask()
        job_config = ConfigFactory.from_dict({
            'job.identifier': 'mysql_remove_stale_data_job',
            f'{task.get_scope()}.{MySQLStalenessRemovalTask.CONN_STRING}': 'foobar',
            f'{task.get_scope()}.{MySQLStalenessRemovalTask.STALENESS_MAX_PCT}': 5,
            f'{task.get_scope()}.{MySQLStalenessRemovalTask.STALENESS_PCT_MAX_DICT}': {'table_metadata': 30},
            f'{task.get_scope()}.{MySQLStalenessRemovalTask.TARGET_TABLES}': ['table_metadata'],
            MySQLCSVPublisher.JOB_PUBLISH_TAG: 'foo'
        })
        mock_total_records_query = mock_session_maker.return_value.return_value.query.return_value.scalar
        mock_total_records_query.return_value = 10
        mock_stale_records_query = mock_session_maker.return_value.return_value \
            .query.return_value.filter.return_value.scalar
        mock_stale_records_query.return_value = 5

        task.init(job_config)

        self.assertRaises(Exception, task._validate_record_staleness_pct, 'table_metadata', Table, 'rk')

    @patch.object(mysql_staleness_removal_task, 'sessionmaker')
    @patch.object(mysql_staleness_removal_task, 'create_engine')
    def test_dry_run(self, mock_create_engine: Any, mock_session_maker: Any) -> None:
        task = MySQLStalenessRemovalTask()
        job_config = ConfigFactory.from_dict({
            'job.identifier': 'mysql_remove_stale_data_job',
            f'{task.get_scope()}.{MySQLStalenessRemovalTask.CONN_STRING}': 'foobar',
            f'{task.get_scope()}.{MySQLStalenessRemovalTask.STALENESS_MAX_PCT}': 5,
            f'{task.get_scope()}.{MySQLStalenessRemovalTask.TARGET_TABLES}': ['foo'],
            f'{task.get_scope()}.{MySQLStalenessRemovalTask.DRY_RUN}': True,
            MySQLCSVPublisher.JOB_PUBLISH_TAG: 'foo'
        })
        mock_commit = mock_session_maker.return_value.return_value.commit

        task.init(job_config)

        mock_commit.assert_not_called()

    @patch.object(mysql_staleness_removal_task, 'sessionmaker')
    @patch.object(mysql_staleness_removal_task, 'create_engine')
    def test_stale_records_filter_condition(self, mock_create_engine: Any, mock_session_maker: Any) -> None:
        task = MySQLStalenessRemovalTask()
        job_config = ConfigFactory.from_dict({
            'job.identifier': 'mysql_remove_stale_data_job',
            f'{task.get_scope()}.{MySQLStalenessRemovalTask.CONN_STRING}': 'foobar',
            f'{task.get_scope()}.{MySQLStalenessRemovalTask.STALENESS_MAX_PCT}': 5,
            f'{task.get_scope()}.{MySQLStalenessRemovalTask.TARGET_TABLES}': ['table_metadata'],
            MySQLCSVPublisher.JOB_PUBLISH_TAG: 'foo'
        })

        task.init(job_config)
        filter_statement = task._get_stale_records_filter_condition(Table)

        self.assertTrue(str(filter_statement) == 'table_metadata.published_tag != :published_tag_1')

        task = MySQLStalenessRemovalTask()
        job_config = ConfigFactory.from_dict({
            'job.identifier': 'mysql_remove_stale_data_job',
            f'{task.get_scope()}.{MySQLStalenessRemovalTask.CONN_STRING}': 'foobar',
            f'{task.get_scope()}.{MySQLStalenessRemovalTask.STALENESS_MAX_PCT}': 5,
            f'{task.get_scope()}.{MySQLStalenessRemovalTask.TARGET_TABLES}': ['table_metadata'],
            f'{task.get_scope()}.{MySQLStalenessRemovalTask.MS_TO_EXPIRE}': 24 * 60 * 60 * 1000

        })

        task.init(job_config)
        filter_statement = task._get_stale_records_filter_condition(Table)

        self.assertTrue(str(filter_statement) == 'table_metadata.publisher_last_updated_epoch_ms < '
                                                 ':publisher_last_updated_epoch_ms_1')


if __name__ == '__main__':
    unittest.main()
