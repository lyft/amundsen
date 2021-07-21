# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import unittest
from typing import Any
from unittest.mock import MagicMock, patch

from amundsen_common.entity.resource_type import ResourceType
from amundsen_common.models.dashboard import DashboardSummary
from amundsen_common.models.popular_table import PopularTable
from amundsen_common.models.table import (Application, Badge, Column,
                                          ProgrammaticDescription, Reader,
                                          Source, Stat, Table, Tag, User,
                                          Watermark)
from amundsen_common.models.user import User as UserEntity
from amundsen_rds.models.application import Application as RDSApplication
from amundsen_rds.models.badge import Badge as RDSBadge
from amundsen_rds.models.cluster import Cluster as RDSCluster
from amundsen_rds.models.column import \
    ColumnDescription as RDSColumnDescription
from amundsen_rds.models.column import ColumnStat as RDSColumnStat
from amundsen_rds.models.column import TableColumn as RDSColumn
from amundsen_rds.models.dashboard import Dashboard as RDSDashboard
from amundsen_rds.models.dashboard import DashboardChart as RDSDashboardChart
from amundsen_rds.models.dashboard import \
    DashboardDescription as RDSDashboardDescription
from amundsen_rds.models.dashboard import \
    DashboardExecution as RDSDashboardExecution
from amundsen_rds.models.dashboard import DashboardGroup as RDSDashboardGroup
from amundsen_rds.models.dashboard import DashboardQuery as RDSDashboardQuery
from amundsen_rds.models.dashboard import \
    DashboardTimestamp as RDSDashboardTimestamp
from amundsen_rds.models.dashboard import DashboardUsage as RDSDashboardUsage
from amundsen_rds.models.database import Database as RDSDatabase
from amundsen_rds.models.schema import Schema as RDSSchema
from amundsen_rds.models.table import Table as RDSTable
from amundsen_rds.models.table import TableDescription as RDSTableDescription
from amundsen_rds.models.table import \
    TableProgrammaticDescription as RDSTableProgrammaticDescription
from amundsen_rds.models.table import TableSource as RDSTableSource
from amundsen_rds.models.table import TableTimestamp as RDSTableTimestamp
from amundsen_rds.models.table import TableUsage as RDSTableUsage
from amundsen_rds.models.table import TableWatermark as RDSTableWatermark
from amundsen_rds.models.tag import Tag as RDSTag
from amundsen_rds.models.user import User as RDSUser

from metadata_service import create_app
from metadata_service.entity.dashboard_detail import DashboardDetail
from metadata_service.entity.dashboard_query import DashboardQuery
from metadata_service.entity.description import Description
from metadata_service.entity.tag_detail import TagDetail
from metadata_service.proxy import mysql_proxy
from metadata_service.proxy.mysql_proxy import MySQLProxy
from metadata_service.util import UserResourceRel


class TestMySQLProxy(unittest.TestCase):

    def setUp(self) -> None:
        self.app = create_app(config_module_class='metadata_service.config.MySQLConfig')
        self.app_context = self.app.app_context()
        self.app_context.push()

    @patch.object(mysql_proxy, 'RDSClient')
    def test_get_table(self, mock_rds_client: Any) -> None:
        database = RDSDatabase(name='hive')
        cluster = RDSCluster(name='gold')
        schema = RDSSchema(name='foo_schema')
        schema.cluster = cluster
        cluster.database = database

        table = RDSTable(name='foo_table')
        table.schema = schema
        table.description = RDSTableDescription(description='foo description')

        col1 = RDSColumn(name='bar_id_1', type='varchar', sort_order=0)
        col1.description = RDSColumnDescription(description='bar col description')
        col1.stats = [RDSColumnStat(stat_type='avg', start_epoch='1', end_epoch='1', stat_val='1')]

        col2 = RDSColumn(name='bar_id_2', type='bigint', sort_order=1)
        col2.description = RDSColumnDescription(description='bar col2 description')
        col2.stats = [RDSColumnStat(stat_type='avg', start_epoch='2', end_epoch='2', stat_val='2')]
        col2.badges = [RDSBadge(rk='primary key', category='column')]
        columns = [col1, col2]

        table.watermarks = [
            RDSTableWatermark(rk='hive://gold.test_schema/test_table/high_watermark/',
                              partition_key='ds',
                              partition_value='fake_value',
                              create_time='fake_time'),
            RDSTableWatermark(rk='hive://gold.test_schema/test_table/low_watermark/',
                              partition_key='ds',
                              partition_value='fake_value',
                              create_time='fake_time')
        ]

        table.application = RDSApplication(application_url='airflow_host/admin/airflow/tree?dag_id=test_table',
                                           description='DAG generating a table',
                                           name='Airflow',
                                           id='dag/task_id')
        table.timestamp = RDSTableTimestamp(last_updated_timestamp=1)

        table.owners = [RDSUser(rk='tester@example.com', email='tester@example.com')]
        table.tags = [RDSTag(rk='test', tag_type='default')]
        table.badges = [RDSBadge(rk='golden', category='table_status')]
        table.source = RDSTableSource(rk='some key', source_type='github', source='/source_file_loc')
        table.programmatic_descriptions = [
            RDSTableProgrammaticDescription(description_source='s3_crawler', description='Test Test Test'),
            RDSTableProgrammaticDescription(description_source='quality_report', description='Test Test')
        ]

        readers = [RDSTableUsage(user_rk='tester@example.com', read_count=5)]

        mock_client = MagicMock()
        mock_rds_client.return_value = mock_client

        mock_create_session = MagicMock()
        mock_client.create_session.return_value = mock_create_session

        mock_session = MagicMock()
        mock_create_session.__enter__.return_value = mock_session

        mock_session_query = MagicMock()
        mock_session.query.return_value = mock_session_query

        mock_session_query_filter = MagicMock()
        mock_session_query.filter.return_value = mock_session_query_filter
        mock_session_query_filter.first.return_value = table

        mock_session_query_filter_orderby = MagicMock()
        mock_session_query_filter.order_by.return_value = mock_session_query_filter_orderby

        mock_session_query_filter_orderby_limit = MagicMock()
        mock_session_query_filter_orderby.limit.return_value = mock_session_query_filter_orderby_limit
        mock_session_query_filter_orderby_limit.all.return_value = readers

        mock_session_query_filter_options = MagicMock()
        mock_session_query_filter.options.return_value = mock_session_query_filter_options
        mock_session_query_filter_options.all.return_value = columns

        proxy = MySQLProxy()
        actual_table = proxy.get_table(table_uri='dummy_uri')

        expected = Table(database='hive', cluster='gold', schema='foo_schema', name='foo_table',
                         tags=[Tag(tag_name='test', tag_type='default')],
                         badges=[Badge(badge_name='golden', category='table_status')],
                         table_readers=[Reader(user=User(email='tester@example.com'), read_count=5)],
                         description='foo description',
                         watermarks=[Watermark(watermark_type='high_watermark',
                                               partition_key='ds',
                                               partition_value='fake_value',
                                               create_time='fake_time'),
                                     Watermark(watermark_type='low_watermark',
                                               partition_key='ds',
                                               partition_value='fake_value',
                                               create_time='fake_time')],
                         columns=[Column(name='bar_id_1', description='bar col description', col_type='varchar',
                                         sort_order=0, stats=[Stat(start_epoch=1,
                                                                   end_epoch=1,
                                                                   stat_type='avg',
                                                                   stat_val='1')], badges=[]),
                                  Column(name='bar_id_2', description='bar col2 description', col_type='bigint',
                                         sort_order=1, stats=[Stat(start_epoch=2,
                                                                   end_epoch=2,
                                                                   stat_type='avg',
                                                                   stat_val='2')],
                                         badges=[Badge(badge_name='primary key', category='column')])],
                         owners=[User(email='tester@example.com')],
                         table_writer=Application(application_url='airflow_host/admin/airflow/tree?dag_id=test_table',
                                                  description='DAG generating a table',
                                                  name='Airflow',
                                                  id='dag/task_id'),
                         last_updated_timestamp=1,
                         source=Source(source='/source_file_loc',
                                       source_type='github'),
                         is_view=False,
                         programmatic_descriptions=[
                             ProgrammaticDescription(source='quality_report',
                                                     text='Test Test'),
                             ProgrammaticDescription(source='s3_crawler',
                                                     text='Test Test Test')
                         ])

        self.assertEqual(str(expected), str(actual_table))

    @patch.object(mysql_proxy, 'RDSClient')
    def test_get_table_description(self, mock_rds_client: Any) -> None:
        mock_client = MagicMock()
        mock_rds_client.return_value = mock_client

        mock_create_session = MagicMock()
        mock_client.create_session.return_value = mock_create_session

        mock_session = MagicMock()
        mock_create_session.__enter__.return_value = mock_session

        mock_session_query = MagicMock()
        mock_session.query.return_value = mock_session_query

        mock_session_query_filter = MagicMock()
        mock_session_query.filter.return_value = mock_session_query_filter

        mock_session_query_filter.scalar.return_value = 'test_description'

        expected = 'test_description'

        proxy = MySQLProxy()
        actual = proxy.get_table_description(table_uri='test_table')

        self.assertEqual(expected, actual)

    @patch.object(mysql_proxy, 'RDSClient')
    def test_put_table_description(self, mock_rds_client: Any) -> None:
        mock_client = MagicMock()
        mock_rds_client.return_value = mock_client

        mock_create_session = MagicMock()
        mock_client.create_session.return_value = mock_create_session

        mock_session = MagicMock()
        mock_create_session.__enter__.return_value = mock_session

        mock_session_merge = MagicMock()
        mock_session.merge = mock_session_merge

        mock_session_commit = MagicMock()
        mock_session.commit = mock_session_commit

        proxy = MySQLProxy()
        proxy.put_table_description(table_uri='test_table',
                                    description='test_description')

        self.assertEqual(1, mock_session_merge.call_count)
        self.assertEqual(1, mock_session_commit.call_count)

    @patch.object(mysql_proxy, 'RDSClient')
    def test_put_column_description(self, mock_rds_client: Any) -> None:
        mock_client = MagicMock()
        mock_rds_client.return_value = mock_client

        mock_create_session = MagicMock()
        mock_client.create_session.return_value = mock_create_session

        mock_session = MagicMock()
        mock_create_session.__enter__.return_value = mock_session

        mock_session_merge = MagicMock()
        mock_session.merge = mock_session_merge

        mock_session_commit = MagicMock()
        mock_session.commit = mock_session_commit

        proxy = MySQLProxy()
        proxy.put_column_description(table_uri='test_table',
                                     column_name='test_column',
                                     description='test_description')

        self.assertEqual(1, mock_session_merge.call_count)
        self.assertEqual(1, mock_session_commit.call_count)

    @patch.object(mysql_proxy, 'RDSClient')
    def test_add_owner(self, mock_rds_client: Any) -> None:
        mock_client = MagicMock()
        mock_rds_client.return_value = mock_client

        mock_create_session = MagicMock()
        mock_client.create_session.return_value = mock_create_session

        mock_session = MagicMock()
        mock_create_session.__enter__.return_value = mock_session

        mock_session_merge = MagicMock()
        mock_session.merge = mock_session_merge

        mock_session_commit = MagicMock()
        mock_session.commit = mock_session_commit

        proxy = MySQLProxy()
        proxy.add_owner(table_uri='dummy_uri',
                        owner='tester')

        self.assertEqual(2, mock_session_merge.call_count)
        self.assertEqual(1, mock_session_commit.call_count)

    @patch.object(mysql_proxy, 'RDSClient')
    def test_delete_owner(self, mock_rds_client: Any) -> None:
        mock_client = MagicMock()
        mock_rds_client.return_value = mock_client

        mock_create_session = MagicMock()
        mock_client.create_session.return_value = mock_create_session

        mock_session = MagicMock()
        mock_create_session.__enter__.return_value = mock_session

        mock_session_query = MagicMock()
        mock_session.query.return_value = mock_session_query

        mock_session_query_filter = MagicMock()
        mock_session_query.filter.return_value = mock_session_query_filter

        mock_session_query_filter_delete = MagicMock()
        mock_session_query_filter.delete = mock_session_query_filter_delete

        mock_session_commit = MagicMock()
        mock_session.commit = mock_session_commit

        proxy = MySQLProxy()
        proxy.delete_owner(table_uri='dummy_uri',
                           owner='tester')

        self.assertEqual(1, mock_session_query_filter_delete.call_count)
        self.assertEqual(1, mock_session_commit.call_count)

    @patch.object(mysql_proxy, 'RDSClient')
    def test_add_badge(self, mock_rds_client: Any) -> None:
        mock_client = MagicMock()
        mock_rds_client.return_value = mock_client

        mock_create_session = MagicMock()
        mock_client.create_session.return_value = mock_create_session

        mock_session = MagicMock()
        mock_create_session.__enter__.return_value = mock_session

        mock_session_merge = MagicMock()
        mock_session.merge = mock_session_merge

        mock_session_commit = MagicMock()
        mock_session.commit = mock_session_commit

        proxy = MySQLProxy()
        proxy.add_badge(id='dummy_uri',
                        badge_name='hive')

        self.assertEqual(2, mock_session_merge.call_count)
        self.assertEqual(1, mock_session_commit.call_count)

    @patch.object(mysql_proxy, 'RDSClient')
    def test_add_tag(self, mock_rds_client: Any) -> None:
        mock_client = MagicMock()
        mock_rds_client.return_value = mock_client

        mock_create_session = MagicMock()
        mock_client.create_session.return_value = mock_create_session

        mock_session = MagicMock()
        mock_create_session.__enter__.return_value = mock_session

        mock_session_merge = MagicMock()
        mock_session.merge = mock_session_merge

        mock_session_commit = MagicMock()
        mock_session.commit = mock_session_commit

        proxy = MySQLProxy()
        proxy.add_tag(id='dummy_uri', tag='hive')

        self.assertEqual(2, mock_session_merge.call_count)
        self.assertEqual(1, mock_session_commit.call_count)

    @patch.object(mysql_proxy, 'RDSClient')
    def test_delete_tag(self, mock_rds_client: Any) -> None:
        mock_client = MagicMock()
        mock_rds_client.return_value = mock_client

        mock_create_session = MagicMock()
        mock_client.create_session.return_value = mock_create_session

        mock_session = MagicMock()
        mock_create_session.__enter__.return_value = mock_session

        mock_session_query = MagicMock()
        mock_session.query.return_value = mock_session_query

        mock_session_query_filter = MagicMock()
        mock_session_query.filter.return_value = mock_session_query_filter

        mock_session_query_filter_delete = MagicMock()
        mock_session_query_filter.delete = mock_session_query_filter_delete

        mock_session_commit = MagicMock()
        mock_session.commit = mock_session_commit

        proxy = MySQLProxy()
        proxy.delete_tag(id='dummy_uri', tag='hive')

        self.assertEqual(1, mock_session_query_filter_delete.call_count)
        self.assertEqual(1, mock_session_commit.call_count)

    @patch.object(mysql_proxy, 'RDSClient')
    def test_get_tags(self, mock_rds_client: Any) -> None:
        mock_client = MagicMock()
        mock_rds_client.return_value = mock_client

        mock_create_session = MagicMock()
        mock_client.create_session.return_value = mock_create_session

        mock_session = MagicMock()
        mock_create_session.__enter__.return_value = mock_session

        mock_session_query = MagicMock()
        mock_session.query.return_value = mock_session_query

        mock_outerjoin = MagicMock()
        mock_session_query.outerjoin.return_value = mock_outerjoin

        mock_outerjoin_outerjoin = MagicMock()
        mock_outerjoin.outerjoin.return_value = mock_outerjoin_outerjoin

        mock_outerjoin_outerjoin_filter = MagicMock()
        mock_outerjoin_outerjoin.filter.return_value = mock_outerjoin_outerjoin_filter

        mock_filter_groupby = MagicMock()
        mock_outerjoin_outerjoin_filter.group_by.return_value = mock_filter_groupby

        mock_groupby_having = MagicMock()
        mock_filter_groupby.having.return_value = mock_groupby_having

        mock_groupby_having.all.return_value = [MagicMock(tag_name='tag1', tag_count=2),
                                                MagicMock(tag_name='tag2', tag_count=1)]

        proxy = MySQLProxy()
        actual = proxy.get_tags()
        expected = [
            TagDetail(tag_name='tag1', tag_count=2),
            TagDetail(tag_name='tag2', tag_count=1),
        ]

        self.assertEqual(expected.__repr__(), actual.__repr__())

    @patch.object(mysql_proxy, 'RDSClient')
    def test_get_latest_updated_ts(self, mock_rds_client: Any) -> None:
        mock_client = MagicMock()
        mock_rds_client.return_value = mock_client

        mock_create_session = MagicMock()
        mock_client.create_session.return_value = mock_create_session

        mock_session = MagicMock()
        mock_create_session.__enter__.return_value = mock_session

        mock_session_query = MagicMock()
        mock_session.query.return_value = mock_session_query

        mock_session_query.scalar.return_value = 1000

        proxy = MySQLProxy()
        actual = proxy.get_latest_updated_ts()

        self.assertEqual(1000, actual)

    @patch.object(MySQLProxy, '_get_global_popular_tables_uris')
    @patch.object(mysql_proxy, 'RDSClient')
    def test_get_popular_tables(self, mock_rds_client: Any, mock_get_global_popular_tables_uris: Any) -> None:
        database = RDSDatabase(name='db')
        cluster = RDSCluster(name='cluster')
        schema = RDSSchema(name='schema')

        table1 = RDSTable(name='foo')
        table2 = RDSTable(name='bar')
        table_description = RDSTableDescription(description='test description')

        cluster.database = database
        schema.cluster = cluster
        table1.schema = schema
        table2.schema = schema
        table1.description = table_description

        mock_client = MagicMock()
        mock_rds_client.return_value = mock_client

        mock_create_session = MagicMock()
        mock_client.create_session.return_value = mock_create_session

        mock_session = MagicMock()
        mock_create_session.__enter__.return_value = mock_session

        mock_session_query = MagicMock()
        mock_session.query.return_value = mock_session_query

        mock_session_query_filter = MagicMock()
        mock_session_query.filter.return_value = mock_session_query_filter

        mock_session_query_filter_options = MagicMock()
        mock_session_query_filter.options.return_value = mock_session_query_filter_options

        mock_session_query_filter_options_options = MagicMock()
        mock_session_query_filter_options.options.return_value = mock_session_query_filter_options_options

        mock_session_query_filter_options_options.all.return_value = [table1, table2]

        expected = [
            PopularTable(database='db', cluster='cluster', schema='schema', name='foo', description='test description'),
            PopularTable(database='db', cluster='cluster', schema='schema', name='bar'),
        ]

        proxy = MySQLProxy()
        actual = proxy.get_popular_tables(num_entries=2)

        self.assertEqual(expected.__repr__(), actual.__repr__())

    @patch.object(mysql_proxy, 'RDSClient')
    def test_get_popular_tables_cache_hit(self, mock_rds_client: Any) -> None:
        mock_client = MagicMock()
        mock_rds_client.return_value = mock_client

        mock_create_session = MagicMock()
        mock_client.create_session.return_value = mock_create_session

        mock_session = MagicMock()
        mock_create_session.__enter__.return_value = mock_session

        mock_session_query = MagicMock()
        mock_session.query.return_value = mock_session_query

        mock_session_query_orderby = MagicMock()
        mock_session_query.order_by.return_value = mock_session_query_orderby

        mock_session_query_orderby_limit = MagicMock()
        mock_session_query_orderby.limit.return_value = mock_session_query_orderby_limit

        mock_session_query_orderby_limit_all = MagicMock()
        mock_session_query_orderby_limit.all = mock_session_query_orderby_limit_all

        proxy = MySQLProxy()
        proxy._get_global_popular_tables_uris(num_entries=2)
        proxy._get_global_popular_tables_uris(num_entries=2)

        self.assertEqual(1, mock_session_query_orderby_limit_all.call_count)

    @patch.object(mysql_proxy, 'RDSClient')
    def test_get_user(self, mock_rds_client: Any) -> None:
        user = RDSUser(employee_type='teamMember',
                       full_name='test_full_name',
                       is_active=True,
                       github_username='test-github',
                       slack_id='test_id',
                       last_name='test_last_name',
                       first_name='test_first_name',
                       team_name='test_team',
                       email='test_email')
        user.manager = RDSUser(full_name='test_manager_fullname')

        mock_client = MagicMock()
        mock_rds_client.return_value = mock_client

        mock_create_session = MagicMock()
        mock_client.create_session.return_value = mock_create_session

        mock_session = MagicMock()
        mock_create_session.__enter__.return_value = mock_session

        mock_session_query = MagicMock()
        mock_session.query.return_value = mock_session_query

        mock_session_query_filter = MagicMock()
        mock_session_query.filter.return_value = mock_session_query_filter

        mock_session_query_filter.first.return_value = user

        expected = UserEntity(email='test_email',
                              first_name='test_first_name',
                              last_name='test_last_name',
                              full_name='test_full_name',
                              is_active=True,
                              github_username='test-github',
                              team_name='test_team',
                              slack_id='test_id',
                              employee_type='teamMember',
                              manager_fullname='test_manager_fullname')

        proxy = MySQLProxy()
        actual = proxy.get_user(id='test_email')

        self.assertEqual(expected, actual)

    @patch.object(mysql_proxy, 'RDSClient')
    def test_get_users(self, mock_rds_client: Any) -> None:
        user = RDSUser(employee_type='teamMember',
                       full_name='test_full_name',
                       is_active=True,
                       github_username='test-github',
                       slack_id='test_id',
                       last_name='test_last_name',
                       first_name='test_first_name',
                       team_name='test_team',
                       email='test_email')
        user.manager = RDSUser(full_name='test_manager_fullname')

        mock_client = MagicMock()
        mock_rds_client.return_value = mock_client

        mock_create_session = MagicMock()
        mock_client.create_session.return_value = mock_create_session

        mock_session = MagicMock()
        mock_create_session.__enter__.return_value = mock_session

        mock_session_query = MagicMock()
        mock_session.query.return_value = mock_session_query

        mock_session_query_filter = MagicMock()
        mock_session_query.filter.return_value = mock_session_query_filter

        mock_session_query_filter.all.return_value = [user]

        expected = [UserEntity(email='test_email',
                               first_name='test_first_name',
                               last_name='test_last_name',
                               full_name='test_full_name',
                               is_active=True,
                               github_username='test-github',
                               team_name='test_team',
                               slack_id='test_id',
                               employee_type='teamMember',
                               manager_fullname='')]
        proxy = MySQLProxy()
        actual = proxy.get_users()

        self.assertEqual(expected, actual)

    @patch.object(mysql_proxy, 'RDSClient')
    def test_get_table_by_user_relation(self, mock_rds_client: Any) -> None:
        table = RDSTable(name='test_table')
        table_description = RDSTableDescription(description='test_description')
        schema = RDSSchema(name='test_schema')
        cluster = RDSCluster(name='test_cluster')
        database = RDSDatabase(name='test_database')
        cluster.database = database
        schema.cluster = cluster
        table.schema = schema
        table.description = table_description

        mock_client = MagicMock()
        mock_rds_client.return_value = mock_client

        mock_create_session = MagicMock()
        mock_client.create_session.return_value = mock_create_session

        mock_session = MagicMock()
        mock_create_session.__enter__.return_value = mock_session

        mock_session_query = MagicMock()
        mock_session.query.return_value = mock_session_query

        mock_session_query_filter = MagicMock()
        mock_session_query.filter.return_value = mock_session_query_filter

        mock_session_query_filter_options = MagicMock()
        mock_session_query_filter.options.return_value = mock_session_query_filter_options

        mock_session_query_filter_options.all.return_value = [table]

        expected = {'table': [PopularTable(database='test_database',
                                           cluster='test_cluster',
                                           schema='test_schema',
                                           name='test_table',
                                           description='test_description')]}
        proxy = MySQLProxy()
        actual = proxy.get_table_by_user_relation(user_email='test_user',
                                                  relation_type=UserResourceRel.follow)

        self.assertEqual(len(actual['table']), 1)
        self.assertEqual(expected, actual)

    @patch.object(mysql_proxy, 'RDSClient')
    def test_get_dashboard_by_user_relation(self, mock_rds_client: Any) -> None:
        dashboard = RDSDashboard(rk='foobar_dashboard',
                                 name='dashboard',
                                 dashboard_url='http://foo.bar/dashboard',)
        dashboard_group = RDSDashboardGroup(name='dashboard_group',
                                            dashboard_group_url='http://foo.bar/group')
        cluster = RDSCluster(name='cluster')
        description = RDSDashboardDescription(description='description')
        execution = RDSDashboardExecution(rk='foobar_last_successful_execution',
                                          timestamp=1234567890)

        dashboard_group.cluster = cluster
        dashboard.group = dashboard_group
        dashboard.description = description
        dashboard.execution = [execution]

        mock_client = MagicMock()
        mock_rds_client.return_value = mock_client

        mock_create_session = MagicMock()
        mock_client.create_session.return_value = mock_create_session

        mock_session = MagicMock()
        mock_create_session.__enter__.return_value = mock_session

        mock_session_query = MagicMock()
        mock_session.query.return_value = mock_session_query

        mock_session_query_filter = MagicMock()
        mock_session_query.filter.return_value = mock_session_query_filter

        mock_session_query_filter_options = MagicMock()
        mock_session_query_filter.options.return_value = mock_session_query_filter_options

        mock_session_query_filter_options.all.return_value = [dashboard]

        expected = {'dashboard': [DashboardSummary(uri='foobar_dashboard',
                                                   cluster='cluster',
                                                   group_name='dashboard_group',
                                                   group_url='http://foo.bar/group',
                                                   product='foobar',
                                                   name='dashboard',
                                                   url='http://foo.bar/dashboard',
                                                   description='description',
                                                   last_successful_run_timestamp=1234567890)]}

        proxy = MySQLProxy()
        actual = proxy.get_dashboard_by_user_relation(user_email='test_user',
                                                      relation_type=UserResourceRel.follow)

        self.assertEqual(len(actual['dashboard']), 1)
        self.assertEqual(expected, actual)

    @patch.object(mysql_proxy, 'RDSClient')
    def test_add_resource_relation_by_user(self, mock_rds_client: Any) -> None:
        mock_client = MagicMock()
        mock_rds_client.return_value = mock_client

        mock_create_session = MagicMock()
        mock_client.create_session.return_value = mock_create_session

        mock_session = MagicMock()
        mock_create_session.__enter__.return_value = mock_session

        mock_session_merge = MagicMock()
        mock_session.merge = mock_session_merge

        mock_session_commit = MagicMock()
        mock_session.commit = mock_session_commit

        proxy = MySQLProxy()
        proxy.add_resource_relation_by_user(id='dummy_uri',
                                            user_id='tester',
                                            relation_type=UserResourceRel.follow,
                                            resource_type=ResourceType.Table)
        self.assertEqual(2, mock_session_merge.call_count)
        self.assertEqual(1, mock_session_commit.call_count)

    @patch.object(mysql_proxy, 'RDSClient')
    def test_delete_resource_relation_by_user(self, mock_rds_client: Any) -> None:
        mock_client = MagicMock()
        mock_rds_client.return_value = mock_client

        mock_create_session = MagicMock()
        mock_client.create_session.return_value = mock_create_session

        mock_session = MagicMock()
        mock_create_session.__enter__.return_value = mock_session

        mock_session_query = MagicMock()
        mock_session.query.return_value = mock_session_query

        mock_session_query_filter = MagicMock()
        mock_session_query.filter.return_value = mock_session_query_filter

        mock_session_query_filter_delete = MagicMock()
        mock_session_query_filter.delete = mock_session_query_filter_delete

        mock_session_commit = MagicMock()
        mock_session.commit = mock_session_commit

        proxy = MySQLProxy()
        proxy.delete_resource_relation_by_user(id='dummy_uri',
                                               user_id='tester',
                                               relation_type=UserResourceRel.follow,
                                               resource_type=ResourceType.Table)

        self.assertEqual(1, mock_session_query_filter_delete.call_count)
        self.assertEqual(1, mock_session_commit.call_count)

    @patch.object(mysql_proxy, 'RDSClient')
    def test_get_dashboard(self, mock_rds_client: Any) -> None:
        # dashboard_metadata
        dashboard = RDSDashboard(rk='foo_dashboard://gold.bar/dashboard_id',
                                 name='dashboard name',
                                 dashboard_url='http://www.foo.bar/dashboard_id',
                                 created_timestamp=123456789)
        dashboard_group = RDSDashboardGroup(name='group_name',
                                            dashboard_group_url='http://www.group_url.com')
        dashboard_group.cluster = RDSCluster(name='cluster_name')
        dashboard.group = dashboard_group
        dashboard.description = RDSDashboardDescription(description='description')
        dashboard.execution = [RDSDashboardExecution(rk='dashboard_last_successful_execution',
                                                     timestamp=9876543210),
                               RDSDashboardExecution(rk='dashboard_last_execution',
                                                     timestamp=987654321,
                                                     state='good_state')]
        dashboard.timestamp = RDSDashboardTimestamp(timestamp=123456654321)
        dashboard.tags = [RDSTag(rk='tag_key1', tag_type='default'),
                          RDSTag(rk='tag_key2', tag_type='default')]
        dashboard.badges = [RDSBadge(rk='golden', category='table_status')]
        dashboard.owners = [RDSUser(email='test_email',
                                    first_name='test_first_name',
                                    last_name='test_last_name',
                                    full_name='test_full_name',
                                    is_active=True,
                                    github_username='test-github',
                                    team_name='test_team',
                                    slack_id='test_id',
                                    employee_type='teamMember'),
                            RDSUser(email='test_email2',
                                    first_name='test_first_name2',
                                    last_name='test_last_name2',
                                    full_name='test_full_name2',
                                    is_active=True,
                                    github_username='test-github2',
                                    team_name='test_team2',
                                    slack_id='test_id2',
                                    employee_type='teamMember')]
        dashboard.usage = [RDSDashboardUsage(read_count=100)]

        mock_client = MagicMock()
        mock_rds_client.return_value = mock_client

        mock_create_session = MagicMock()
        mock_client.create_session.return_value = mock_create_session

        mock_session = MagicMock()
        mock_create_session.__enter__.return_value = mock_session

        mock_session_query = MagicMock()
        mock_session.query.return_value = mock_session_query

        mock_session_query_filter = MagicMock()
        mock_session_query.filter.return_value = mock_session_query_filter

        mock_session_query_filter.first.return_value = dashboard

        # queries
        query1 = RDSDashboardQuery(name='query1')
        query2 = RDSDashboardQuery(name='query2',
                                   url='http://foo.bar/query',
                                   query_text='SELECT * FROM foo.bar')
        query1.charts = [RDSDashboardChart(name='chart1')]
        query2.charts = [RDSDashboardChart(name='chart2')]
        queries = [query1, query2]

        # tables
        database1 = RDSDatabase(name='db1')
        database2 = RDSDatabase(name='db2')
        cluster1 = RDSCluster(name='cluster1')
        cluster2 = RDSCluster(name='cluster2')
        schema1 = RDSSchema(name='schema1')
        schema2 = RDSSchema(name='schema2')
        table1 = RDSTable(name='table1')
        table2 = RDSTable(name='table2')
        description1 = RDSTableDescription(description='table description 1')

        schema1.cluster = cluster1
        cluster1.database = database1
        schema2.cluster = cluster2
        cluster2.database = database2
        table1.schema = schema1
        table2.schema = schema2
        table1.description = description1
        tables = [table1, table2]

        mock_session_query_filter_options = MagicMock()
        mock_session_query_filter.options.return_value = mock_session_query_filter_options

        mock_session_query_filter_options.all.side_effect = [queries, tables]

        expected = DashboardDetail(uri='foo_dashboard://gold.bar/dashboard_id', cluster='cluster_name',
                                   group_name='group_name', group_url='http://www.group_url.com',
                                   product='foo',
                                   name='dashboard name', url='http://www.foo.bar/dashboard_id',
                                   description='description', created_timestamp=123456789,
                                   last_successful_run_timestamp=9876543210,
                                   updated_timestamp=123456654321, last_run_timestamp=987654321,
                                   last_run_state='good_state',
                                   owners=[User(email='test_email', first_name='test_first_name',
                                                last_name='test_last_name',
                                                full_name='test_full_name', is_active=True,
                                                github_username='test-github',
                                                team_name='test_team', slack_id='test_id',
                                                employee_type='teamMember', manager_fullname=''),
                                           User(email='test_email2', first_name='test_first_name2',
                                                last_name='test_last_name2',
                                                full_name='test_full_name2', is_active=True,
                                                github_username='test-github2',
                                                team_name='test_team2', slack_id='test_id2',
                                                employee_type='teamMember', manager_fullname='')],
                                   frequent_users=[], chart_names=['chart1', 'chart2'],
                                   query_names=['query1', 'query2'],
                                   queries=[DashboardQuery(name='query1'),
                                            DashboardQuery(name='query2', url='http://foo.bar/query',
                                                           query_text='SELECT * FROM foo.bar')],
                                   tables=[
                                       PopularTable(database='db1',
                                                    name='table1',
                                                    description='table description 1',
                                                    cluster='cluster1',
                                                    schema='schema1'),
                                       PopularTable(database='db2',
                                                    name='table2',
                                                    cluster='cluster2',
                                                    schema='schema2'),
                                   ],
                                   tags=[Tag(tag_type='default', tag_name='tag_key1'),
                                         Tag(tag_type='default', tag_name='tag_key2')],
                                   badges=[Badge(badge_name='golden', category='table_status')],
                                   recent_view_count=100)

        proxy = MySQLProxy()
        actual = proxy.get_dashboard(id='dashboard_id')

        self.assertEqual(expected, actual)

    @patch.object(mysql_proxy, 'RDSClient')
    def test_get_dashboard_description(self, mock_rds_client: Any) -> None:
        mock_client = MagicMock()
        mock_rds_client.return_value = mock_client

        mock_create_session = MagicMock()
        mock_client.create_session.return_value = mock_create_session

        mock_session = MagicMock()
        mock_create_session.__enter__.return_value = mock_session

        mock_session_query = MagicMock()
        mock_session.query.return_value = mock_session_query

        mock_session_query_filter = MagicMock()
        mock_session_query.filter.return_value = mock_session_query_filter

        mock_session_query_filter.scalar.return_value = 'test_description'

        expected = Description(description='test_description')

        proxy = MySQLProxy()
        actual = proxy.get_dashboard_description(id='test_dashboard')

        self.assertEqual(expected, actual)

    @patch.object(mysql_proxy, 'RDSClient')
    def test_put_dashboard_description(self, mock_rds_client: Any) -> None:
        mock_client = MagicMock()
        mock_rds_client.return_value = mock_client

        mock_create_session = MagicMock()
        mock_client.create_session.return_value = mock_create_session

        mock_session = MagicMock()
        mock_create_session.__enter__.return_value = mock_session

        mock_session_merge = MagicMock()
        mock_session.merge = mock_session_merge

        mock_session_commit = MagicMock()
        mock_session.commit = mock_session_commit

        proxy = MySQLProxy()
        proxy.put_dashboard_description(id='test_dashboard', description='test_description')

        self.assertEqual(1, mock_session_merge.call_count)
        self.assertEqual(1, mock_session_commit.call_count)

    @patch.object(mysql_proxy, 'RDSClient')
    def test_put_user_new_user(self, mock_rds_client: Any) -> None:
        mock_client = MagicMock()
        mock_rds_client.return_value = mock_client

        mock_create_session = MagicMock()
        mock_client.create_session.return_value = mock_create_session

        mock_session = MagicMock()
        mock_create_session.__enter__.return_value = mock_session

        mock_session_merge = MagicMock()
        mock_session.merge = mock_session_merge

        mock_session_commit = MagicMock()
        mock_session.commit = mock_session_commit

        test_user = MagicMock()

        proxy = MySQLProxy()
        proxy.create_update_user(user=test_user)

        self.assertEqual(1, mock_session_merge.call_count)
        self.assertEqual(1, mock_session_commit.call_count)


if __name__ == '__main__':
    unittest.main()
