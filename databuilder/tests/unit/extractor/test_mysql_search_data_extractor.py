# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import unittest
from typing import Any
from unittest.mock import MagicMock, patch

from amundsen_rds.models.badge import Badge
from amundsen_rds.models.cluster import Cluster
from amundsen_rds.models.column import ColumnDescription, TableColumn
from amundsen_rds.models.dashboard import (
    Dashboard, DashboardChart, DashboardCluster, DashboardDescription, DashboardExecution, DashboardGroup,
    DashboardGroupDescription, DashboardQuery, DashboardUsage,
)
from amundsen_rds.models.database import Database
from amundsen_rds.models.schema import Schema, SchemaDescription
from amundsen_rds.models.table import (
    Table, TableDescription, TableProgrammaticDescription, TableTimestamp, TableUsage,
)
from amundsen_rds.models.tag import Tag
from amundsen_rds.models.user import User
from pyhocon import ConfigFactory

from databuilder import Scoped
from databuilder.extractor import mysql_search_data_extractor
from databuilder.extractor.mysql_search_data_extractor import MySQLSearchDataExtractor
from databuilder.models.dashboard_elasticsearch_document import DashboardESDocument
from databuilder.models.table_elasticsearch_document import TableESDocument
from databuilder.models.user_elasticsearch_document import UserESDocument


class MyTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.maxDiff = None

    @patch.object(mysql_search_data_extractor, '_table_search_query')
    @patch.object(mysql_search_data_extractor, 'sessionmaker')
    @patch.object(mysql_search_data_extractor, 'create_engine')
    def test_table_search(self,
                          mock_create_engine: Any,
                          mock_session_maker: Any,
                          mock_table_search_query: Any) -> None:
        database = Database(rk='test_database_key', name='test_database')
        cluster = Cluster(rk='test_cluster_key', name='test_cluster')
        cluster.database = database

        schema = Schema(rk='test_schema_key', name='test_schema')
        schema.description = SchemaDescription(rk='test_schema_description_key', description='test_schema_description')
        schema.cluster = cluster

        table = Table(rk='test_table_key', name='test_table')
        table.schema = schema

        table.description = TableDescription(rk='test_table_description_key', description='test_table_description')
        table.programmatic_descriptions = [TableProgrammaticDescription(rk='test_table_prog_description_key',
                                                                        description='test_table_prog_description')]

        table.timestamp = TableTimestamp(rk='test_table_timestamp_key', last_updated_timestamp=123456789)

        column1 = TableColumn(rk='test_col1_key', name='test_col1')
        column2 = TableColumn(rk='test_col2_key', name='test_col2')
        column3 = TableColumn(rk='test_col3_key', name='test_col3')
        column1.description = ColumnDescription(rk='test_col1_description_key',
                                                description='test_col1_description')
        column2.description = ColumnDescription(rk='test_col2_description_key',
                                                description='test_col2_description')
        table.columns = [column1, column2, column3]

        usage1 = TableUsage(user_rk='test_user1_key', table_rk='test_table_key', read_count=5)
        usage2 = TableUsage(user_rk='test_user2_key', table_rk='test_table_key', read_count=10)
        table.usage = [usage1, usage2]

        tags = [Tag(rk='test_tag', tag_type='default')]
        table.tags = tags

        badges = [Badge(rk='test_badge')]
        table.badges = badges

        tables = [table]

        expected_dict = dict(database='test_database',
                             cluster='test_cluster',
                             schema='test_schema',
                             name='test_table',
                             display_name='test_schema.test_table',
                             key='test_table_key',
                             description='test_table_description',
                             last_updated_timestamp=123456789,
                             column_names=['test_col1', 'test_col2', 'test_col3'],
                             column_descriptions=['test_col1_description', 'test_col2_description', ''],
                             total_usage=15,
                             unique_usage=2,
                             tags=['test_tag'],
                             badges=['test_badge'],
                             schema_description='test_schema_description',
                             programmatic_descriptions=['test_table_prog_description'])

        config_dict = {
            f'extractor.mysql_search_data.{MySQLSearchDataExtractor.CONN_STRING}': 'test_conn_string',
            f'extractor.mysql_search_data.{MySQLSearchDataExtractor.ENTITY_TYPE}': 'table',
            f'extractor.mysql_search_data.{MySQLSearchDataExtractor.JOB_PUBLISH_TAG}': 'test_tag',
            f'extractor.mysql_search_data.{MySQLSearchDataExtractor.MODEL_CLASS}':
                'databuilder.models.table_elasticsearch_document.TableESDocument'
        }
        self.conf = ConfigFactory.from_dict(config_dict)

        extractor = MySQLSearchDataExtractor()
        extractor.init(Scoped.get_scoped_conf(conf=self.conf,
                                              scope=extractor.get_scope()))

        mock_table_search_query.side_effect = [tables, None]

        actual_obj = extractor.extract()

        self.assertIsInstance(actual_obj, TableESDocument)
        self.assertDictEqual(vars(actual_obj), expected_dict)

    @patch.object(mysql_search_data_extractor, '_user_search_query')
    @patch.object(mysql_search_data_extractor, 'sessionmaker')
    @patch.object(mysql_search_data_extractor, 'create_engine')
    def test_user_search(self,
                         mock_create_engine: Any,
                         mock_session_maker: Any,
                         mock_user_search_query: Any) -> None:
        user = User(rk='test_user_key',
                    email='test_user@email.com',
                    first_name='test_first_name',
                    last_name='test_last_name',
                    full_name='test_full_name',
                    github_username='test_github_username',
                    team_name='test_team_name',
                    employee_type='test_employee_type',
                    slack_id='test_slack_id',
                    role_name='test_role_name',
                    is_active=True)
        manager = User(rk='test_manager_key', email='test_manager@email.com')
        user.manager = manager

        expected_dict = dict(email='test_user@email.com',
                             first_name='test_first_name',
                             last_name='test_last_name',
                             full_name='test_full_name',
                             github_username='test_github_username',
                             team_name='test_team_name',
                             employee_type='test_employee_type',
                             manager_email='test_manager@email.com',
                             slack_id='test_slack_id',
                             role_name='test_role_name',
                             is_active=True,
                             total_read=30,
                             total_own=2,
                             total_follow=2)

        config_dict = {
            f'extractor.mysql_search_data.{MySQLSearchDataExtractor.CONN_STRING}': 'test_conn_string',
            f'extractor.mysql_search_data.{MySQLSearchDataExtractor.ENTITY_TYPE}': 'user',
            f'extractor.mysql_search_data.{MySQLSearchDataExtractor.JOB_PUBLISH_TAG}': 'test_tag',
            f'extractor.mysql_search_data.{MySQLSearchDataExtractor.MODEL_CLASS}':
                'databuilder.models.user_elasticsearch_document.UserESDocument'
        }
        self.conf = ConfigFactory.from_dict(config_dict)

        extractor = MySQLSearchDataExtractor()
        extractor.init(Scoped.get_scoped_conf(conf=self.conf,
                                              scope=extractor.get_scope()))

        query_results = [MagicMock(User=user,
                                   table_read_count=10,
                                   dashboard_read_count=20,
                                   table_own_count=1,
                                   dashboard_own_count=1,
                                   table_follow_count=1,
                                   dashboard_follow_count=1)]
        mock_user_search_query.side_effect = [query_results, None]

        actual_obj = extractor.extract()

        self.assertIsInstance(actual_obj, UserESDocument)
        self.assertDictEqual(vars(actual_obj), expected_dict)

    @patch.object(mysql_search_data_extractor, '_dashboard_search_query')
    @patch.object(mysql_search_data_extractor, 'sessionmaker')
    @patch.object(mysql_search_data_extractor, 'create_engine')
    def test_dashboard_search(self,
                              mock_create_engine: Any,
                              mock_session_maker: Any,
                              mock_dashboard_search_query: Any) -> None:
        dashboard = Dashboard(rk='test_dashboard//key', name='test_dashboard', dashboard_url='test://dashboard_url')
        dashboard.description = DashboardDescription(rk='test_dashboard_description_key',
                                                     description='test_dashboard_description')

        group = DashboardGroup(rk='test_group_key', name='test_group', dashboard_group_url='test://group_url')
        group.description = DashboardGroupDescription(rk='test_group_description_key',
                                                      description='test_group_description')
        dashboard.group = group

        cluster = DashboardCluster(rk='test_cluster_key', name='test_cluster')
        group.cluster = cluster

        last_exec = DashboardExecution(rk='test_dashboard_exec_key/_last_successful_execution', timestamp=123456789)
        dashboard.execution = [last_exec]

        usage1 = DashboardUsage(user_rk='test_user1_key', dashboard_rk='test_dashboard_key', read_count=10)
        usage2 = DashboardUsage(user_rk='test_user2_key', dashboard_rk='test_dashboard_key', read_count=5)
        dashboard.usage = [usage1, usage2]

        query = DashboardQuery(rk='test_query_key', name='test_query')
        query.charts = [DashboardChart(rk='test_chart_key', name='test_chart')]
        dashboard.queries = [query]

        tags = [Tag(rk='test_tag', tag_type='default')]
        dashboard.tags = tags

        badges = [Badge(rk='test_badge')]
        dashboard.badges = badges

        dashboards = [dashboard]

        expected_dict = dict(group_name='test_group',
                             name='test_dashboard',
                             description='test_dashboard_description',
                             product='test',
                             cluster='test_cluster',
                             group_description='test_group_description',
                             query_names=['test_query'],
                             chart_names=['test_chart'],
                             group_url='test://group_url',
                             url='test://dashboard_url',
                             uri='test_dashboard//key',
                             last_successful_run_timestamp=123456789,
                             total_usage=15,
                             tags=['test_tag'],
                             badges=['test_badge'])

        config_dict = {
            f'extractor.mysql_search_data.{MySQLSearchDataExtractor.CONN_STRING}': 'test_conn_string',
            f'extractor.mysql_search_data.{MySQLSearchDataExtractor.ENTITY_TYPE}': 'dashboard',
            f'extractor.mysql_search_data.{MySQLSearchDataExtractor.JOB_PUBLISH_TAG}': 'test_tag',
            f'extractor.mysql_search_data.{MySQLSearchDataExtractor.MODEL_CLASS}':
                'databuilder.models.dashboard_elasticsearch_document.DashboardESDocument'
        }
        self.conf = ConfigFactory.from_dict(config_dict)

        extractor = MySQLSearchDataExtractor()
        extractor.init(Scoped.get_scoped_conf(conf=self.conf,
                                              scope=extractor.get_scope()))

        mock_dashboard_search_query.side_effect = [dashboards, None]

        actual_obj = extractor.extract()

        self.assertIsInstance(actual_obj, DashboardESDocument)
        self.assertDictEqual(vars(actual_obj), expected_dict)


if __name__ == '__main__':
    unittest.main()
