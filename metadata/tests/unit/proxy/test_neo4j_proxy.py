# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import copy
import textwrap
import unittest
from typing import Any, Dict  # noqa: F401
from unittest.mock import MagicMock, patch

from amundsen_common.entity.resource_type import ResourceType
from amundsen_common.models.dashboard import DashboardSummary
from amundsen_common.models.feature import Feature, FeatureWatermark
from amundsen_common.models.generation_code import GenerationCode
from amundsen_common.models.lineage import Lineage, LineageItem
from amundsen_common.models.popular_table import PopularTable
from amundsen_common.models.table import (Application, Badge, Column,
                                          ProgrammaticDescription, Source,
                                          SqlJoin, SqlWhere, Stat, Table,
                                          TableSummary, Tag, User, Watermark)
from amundsen_common.models.user import User as UserModel
from neo4j import GraphDatabase

from metadata_service import create_app
from metadata_service.entity.dashboard_detail import DashboardDetail
from metadata_service.entity.dashboard_query import DashboardQuery
from metadata_service.entity.tag_detail import TagDetail
from metadata_service.exception import NotFoundException
from metadata_service.proxy.neo4j_proxy import Neo4jProxy
from metadata_service.util import UserResourceRel


class TestNeo4jProxy(unittest.TestCase):

    def setUp(self) -> None:
        self.app = create_app(config_module_class='metadata_service.config.LocalConfig')
        self.app_context = self.app.app_context()
        self.app_context.push()

        table_entry = {'db': {'name': 'hive'},
                       'clstr': {
                           'name': 'gold'},
                       'schema': {
                           'name': 'foo_schema'},
                       'tbl': {
                           'name': 'foo_table'},
                       'tbl_dscrpt': {
                           'description': 'foo description'}
                       }

        col1 = copy.deepcopy(table_entry)  # type: Dict[Any, Any]
        col1['col'] = {'name': 'bar_id_1',
                       'col_type': 'varchar',
                       'sort_order': 0}
        col1['col_dscrpt'] = {'description': 'bar col description'}
        col1['col_stats'] = [{'stat_type': 'avg', 'start_epoch': 1, 'end_epoch': 1, 'stat_val': '1'}]
        col1['col_badges'] = []

        col2 = copy.deepcopy(table_entry)  # type: Dict[Any, Any]
        col2['col'] = {'name': 'bar_id_2',
                       'col_type': 'bigint',
                       'sort_order': 1}
        col2['col_dscrpt'] = {'description': 'bar col2 description'}
        col2['col_stats'] = [{'stat_type': 'avg', 'start_epoch': 2, 'end_epoch': 2, 'stat_val': '2'}]
        col2['col_badges'] = [{'key': 'primary key', 'category': 'column'}]

        table_level_results = MagicMock()
        table_level_results.single.return_value = {
            'wmk_records': [
                {
                    'key': 'hive://gold.test_schema/test_table/high_watermark/',
                    'partition_key': 'ds',
                    'partition_value': 'fake_value',
                    'create_time': 'fake_time',
                },
                {
                    'key': 'hive://gold.test_schema/test_table/low_watermark/',
                    'partition_key': 'ds',
                    'partition_value': 'fake_value',
                    'create_time': 'fake_time',
                }
            ],
            'application': {
                'application_url': 'airflow_host/admin/airflow/tree?dag_id=test_table',
                'description': 'DAG generating a table',
                'name': 'Airflow',
                'id': 'dag/task_id'
            },
            'last_updated_timestamp': 1,
            'owner_records': [
                {
                    'key': 'tester@example.com',
                    'email': 'tester@example.com',
                    'updated_at': 0,
                }
            ],
            'tag_records': [
                {
                    'key': 'test',
                    'tag_type': 'default'
                }
            ],
            'badge_records': [
                {
                    'key': 'golden',
                    'category': 'table_status'
                }
            ],
            'src': {
                'source': '/source_file_loc',
                'key': 'some key',
                'source_type': 'github'
            },
            'prog_descriptions': [
                {
                    'description_source': 's3_crawler',
                    'description': 'Test Test Test'
                },
                {
                    'description_source': 'quality_report',
                    'description': 'Test Test'
                }
            ]
        }

        table_common_usage = MagicMock()
        table_common_usage.single.return_value = {
            'joins': [
                {
                    'join_exec_cnt': 2,
                    'join': {
                        'join_sql': (
                            'statewide_cases cases '
                            'join statewide_testing tests on cases.newcountconfirmed <= tests.tested'
                        ),
                        'join_type': 'inner join',
                        'joined_on_column': 'newcountconfirmed',
                        'joined_on_table': {
                            'schema': 'open_data',
                            'cluster': 'ca_covid',
                            'database': 'snowflake',
                            'name': 'statewide_testing'
                        },
                        'column': 'newcountconfirmed'
                    }
                }
            ],
            'filters': [
                {
                    'where_clause': 'b.countnewestcases <= 15',
                    'where_exec_cnt': 2
                }
            ]
        }

        table_writer = {
            'application_url': 'airflow_host/admin/airflow/tree?dag_id=test_table',
            'description': 'DAG generating a table',
            'name': 'Airflow',
            'id': 'dag/task_id'
        }

        last_updated_timestamp = '01'

        self.col_usage_return_value = [
            col1,
            col2
        ]
        self.table_level_return_value = table_level_results

        self.table_writer = table_writer

        self.last_updated_timestamp = last_updated_timestamp

        self.table_common_usage = table_common_usage

    def tearDown(self) -> None:
        pass

    def test_get_table(self) -> None:
        with patch.object(GraphDatabase, 'driver'), patch.object(Neo4jProxy, '_execute_cypher_query') as mock_execute:
            mock_execute.side_effect = [
                self.col_usage_return_value,
                [],
                self.table_level_return_value,
                self.table_common_usage,
                []
            ]

            neo4j_proxy = Neo4jProxy(host='DOES_NOT_MATTER', port=0000)
            table = neo4j_proxy.get_table(table_uri='dummy_uri')

            expected = Table(database='hive', cluster='gold', schema='foo_schema', name='foo_table',
                             tags=[Tag(tag_name='test', tag_type='default')],
                             badges=[Badge(badge_name='golden', category='table_status')],
                             table_readers=[], description='foo description',
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
                             owners=[User(email='tester@example.com', user_id='tester@example.com')],
                             table_writer=Application(application_url=self.table_writer['application_url'],
                                                      description=self.table_writer['description'],
                                                      name=self.table_writer['name'],
                                                      id=self.table_writer['id']),
                             last_updated_timestamp=1,
                             source=Source(source='/source_file_loc',
                                           source_type='github'),
                             is_view=False,
                             programmatic_descriptions=[
                                 ProgrammaticDescription(source='quality_report',
                                                         text='Test Test'),
                                 ProgrammaticDescription(source='s3_crawler',
                                                         text='Test Test Test')
                             ],
                             common_joins=[
                                 SqlJoin(
                                     join_sql=(
                                         'statewide_cases cases '
                                         'join statewide_testing tests on cases.newcountconfirmed <= tests.tested'
                                     ),
                                     join_type='inner join',
                                     joined_on_column='newcountconfirmed',
                                     joined_on_table=TableSummary(
                                         schema='open_data',
                                         cluster='ca_covid',
                                         database='snowflake',
                                         name='statewide_testing'
                                     ),
                                     column='newcountconfirmed'
                                 )
                             ],
                             common_filters=[
                                 SqlWhere(where_clause='b.countnewestcases <= 15')
                             ])

            self.assertEqual(str(expected), str(table))

    def test_get_table_view_only(self) -> None:
        col_usage_return_value = copy.deepcopy(self.col_usage_return_value)
        for col in col_usage_return_value:
            col['tbl']['is_view'] = True

        with patch.object(GraphDatabase, 'driver'), patch.object(Neo4jProxy, '_execute_cypher_query') as mock_execute:
            mock_execute.side_effect = [
                col_usage_return_value,
                [],
                self.table_level_return_value,
                self.table_common_usage,
                []
            ]

            neo4j_proxy = Neo4jProxy(host='DOES_NOT_MATTER', port=0000)
            table = neo4j_proxy.get_table(table_uri='dummy_uri')

            expected = Table(database='hive', cluster='gold', schema='foo_schema', name='foo_table',
                             tags=[Tag(tag_name='test', tag_type='default')],
                             badges=[Badge(badge_name='golden', category='table_status')],
                             table_readers=[], description='foo description',
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
                             owners=[User(email='tester@example.com', user_id='tester@example.com')],
                             table_writer=Application(application_url=self.table_writer['application_url'],
                                                      description=self.table_writer['description'],
                                                      name=self.table_writer['name'],
                                                      id=self.table_writer['id']),
                             last_updated_timestamp=1,
                             source=Source(source='/source_file_loc',
                                           source_type='github'),
                             is_view=True,
                             programmatic_descriptions=[
                                 ProgrammaticDescription(source='quality_report',
                                                         text='Test Test'),
                                 ProgrammaticDescription(source='s3_crawler',
                                                         text='Test Test Test')
                             ],
                             common_joins=[
                                 SqlJoin(
                                     join_sql=(
                                         'statewide_cases cases '
                                         'join statewide_testing tests on cases.newcountconfirmed <= tests.tested'
                                     ),
                                     join_type='inner join',
                                     joined_on_column='newcountconfirmed',
                                     joined_on_table=TableSummary(
                                         schema='open_data',
                                         cluster='ca_covid',
                                         database='snowflake',
                                         name='statewide_testing'
                                     ),
                                     column='newcountconfirmed'
                                 )
                             ],
                             common_filters=[
                                 SqlWhere(where_clause='b.countnewestcases <= 15')
                             ])

            self.assertEqual(str(expected), str(table))

    def test_get_table_with_valid_description(self) -> None:
        """
        Test description is returned for table
        :return:
        """
        with patch.object(GraphDatabase, 'driver'), patch.object(Neo4jProxy, '_execute_cypher_query') as mock_execute:
            mock_execute.return_value.single.return_value = dict(description='sample description')

            neo4j_proxy = Neo4jProxy(host='DOES_NOT_MATTER', port=0000)
            table_description = neo4j_proxy.get_table_description(table_uri='test_table')

            table_description_query = textwrap.dedent("""
            MATCH (n:Table {key: $key})-[:DESCRIPTION]->(d:Description)
            RETURN d.description AS description;
            """)
            mock_execute.assert_called_with(statement=table_description_query,
                                            param_dict={'key': 'test_table'})

            self.assertEqual(table_description, 'sample description')

    def test_get_table_with_no_description(self) -> None:
        """
        Test None is returned for table with no description
        :return:
        """
        with patch.object(GraphDatabase, 'driver'), patch.object(Neo4jProxy, '_execute_cypher_query') as mock_execute:
            mock_execute.return_value.single.return_value = None

            neo4j_proxy = Neo4jProxy(host='DOES_NOT_MATTER', port=0000)
            table_description = neo4j_proxy.get_table_description(table_uri='test_table')

            table_description_query = textwrap.dedent("""
            MATCH (n:Table {key: $key})-[:DESCRIPTION]->(d:Description)
            RETURN d.description AS description;
            """)
            mock_execute.assert_called_with(statement=table_description_query,
                                            param_dict={'key': 'test_table'})

            self.assertIsNone(table_description)

    def test_put_table_description(self) -> None:
        """
        Test updating table description
        :return:
        """
        with patch.object(GraphDatabase, 'driver') as mock_driver:
            mock_session = MagicMock()
            mock_driver.return_value.session.return_value = mock_session

            mock_transaction = MagicMock()
            mock_session.begin_transaction.return_value = mock_transaction

            mock_run = MagicMock()
            mock_transaction.run = mock_run
            mock_commit = MagicMock()
            mock_transaction.commit = mock_commit

            neo4j_proxy = Neo4jProxy(host='DOES_NOT_MATTER', port=0000)
            neo4j_proxy.put_table_description(table_uri='test_table',
                                              description='test_description')

            self.assertEqual(mock_run.call_count, 2)
            self.assertEqual(mock_commit.call_count, 1)

    def test_get_column_with_valid_description(self) -> None:
        """
        Test description is returned for column
        :return:
        """
        with patch.object(GraphDatabase, 'driver'), patch.object(Neo4jProxy, '_execute_cypher_query') as mock_execute:
            mock_execute.return_value.single.return_value = dict(description='sample description')

            neo4j_proxy = Neo4jProxy(host='DOES_NOT_MATTER', port=0000)
            col_description = neo4j_proxy.get_column_description(table_uri='test_table',
                                                                 column_name='test_column')

            column_description_query = textwrap.dedent("""
            MATCH (tbl:Table {key: $tbl_key})-[:COLUMN]->(c:Column {name: $column_name})-[:DESCRIPTION]->(d:Description)
            RETURN d.description AS description;
            """)
            mock_execute.assert_called_with(statement=column_description_query,
                                            param_dict={'tbl_key': 'test_table',
                                                        'column_name': 'test_column'})

            self.assertEqual(col_description, 'sample description')

    def test_get_column_with_no_description(self) -> None:
        """
        Test None is returned for column with no description
        :return:
        """
        with patch.object(GraphDatabase, 'driver'), patch.object(Neo4jProxy, '_execute_cypher_query') as mock_execute:
            mock_execute.return_value.single.return_value = None

            neo4j_proxy = Neo4jProxy(host='DOES_NOT_MATTER', port=0000)
            col_description = neo4j_proxy.get_column_description(table_uri='test_table',
                                                                 column_name='test_column')

            column_description_query = textwrap.dedent("""
            MATCH (tbl:Table {key: $tbl_key})-[:COLUMN]->(c:Column {name: $column_name})-[:DESCRIPTION]->(d:Description)
            RETURN d.description AS description;
            """)
            mock_execute.assert_called_with(statement=column_description_query,
                                            param_dict={'tbl_key': 'test_table',
                                                        'column_name': 'test_column'})

            self.assertIsNone(col_description)

    def test_put_column_description(self) -> None:
        """
        Test updating column description
        :return:
        """
        with patch.object(GraphDatabase, 'driver') as mock_driver:
            mock_session = MagicMock()
            mock_driver.return_value.session.return_value = mock_session

            mock_transaction = MagicMock()
            mock_session.begin_transaction.return_value = mock_transaction

            mock_run = MagicMock()
            mock_transaction.run = mock_run
            mock_commit = MagicMock()
            mock_transaction.commit = mock_commit

            neo4j_proxy = Neo4jProxy(host='DOES_NOT_MATTER', port=0000)
            neo4j_proxy.put_column_description(table_uri='test_table',
                                               column_name='test_column',
                                               description='test_description')

            self.assertEqual(mock_run.call_count, 2)
            self.assertEqual(mock_commit.call_count, 1)

    def test_add_owner(self) -> None:
        with patch.object(GraphDatabase, 'driver') as mock_driver:
            mock_session = MagicMock()
            mock_driver.return_value.session.return_value = mock_session

            mock_transaction = MagicMock()
            mock_session.begin_transaction.return_value = mock_transaction

            mock_run = MagicMock()
            mock_transaction.run = mock_run
            mock_commit = MagicMock()
            mock_transaction.commit = mock_commit

            neo4j_proxy = Neo4jProxy(host='DOES_NOT_MATTER', port=0000)
            neo4j_proxy.add_owner(table_uri='dummy_uri',
                                  owner='tester')
            # we call neo4j twice in add_owner call
            self.assertEqual(mock_run.call_count, 2)
            self.assertEqual(mock_commit.call_count, 1)

    def test_delete_owner(self) -> None:
        with patch.object(GraphDatabase, 'driver') as mock_driver:
            mock_session = MagicMock()
            mock_driver.return_value.session.return_value = mock_session

            mock_transaction = MagicMock()
            mock_session.begin_transaction.return_value = mock_transaction

            mock_run = MagicMock()
            mock_transaction.run = mock_run
            mock_commit = MagicMock()
            mock_transaction.commit = mock_commit

            neo4j_proxy = Neo4jProxy(host='DOES_NOT_MATTER', port=0000)
            neo4j_proxy.delete_owner(table_uri='dummy_uri',
                                     owner='tester')
            # we only call neo4j once in delete_owner call
            self.assertEqual(mock_run.call_count, 1)
            self.assertEqual(mock_commit.call_count, 1)

    def test_add_table_badge(self) -> None:
        with patch.object(GraphDatabase, 'driver') as mock_driver:
            mock_session = MagicMock()
            mock_driver.return_value.session.return_value = mock_session

            mock_transaction = MagicMock()
            mock_session.begin_transaction.return_value = mock_transaction

            mock_run = MagicMock()
            mock_transaction.run = mock_run
            mock_commit = MagicMock()
            mock_transaction.commit = mock_commit

            neo4j_proxy = Neo4jProxy(host='DOES_NOT_MATTER', port=0000)
            neo4j_proxy.add_badge(id='dummy_uri',
                                  badge_name='hive',
                                  resource_type=ResourceType.Table)
            # we call neo4j twice in add_tag call
            self.assertEqual(mock_run.call_count, 3)
            self.assertEqual(mock_commit.call_count, 1)

    def test_add_column_badge(self) -> None:
        with patch.object(GraphDatabase, 'driver') as mock_driver:
            mock_session = MagicMock()
            mock_driver.return_value.session.return_value = mock_session

            mock_transaction = MagicMock()
            mock_session.begin_transaction.return_value = mock_transaction

            mock_run = MagicMock()
            mock_transaction.run = mock_run
            mock_commit = MagicMock()
            mock_transaction.commit = mock_commit

            neo4j_proxy = Neo4jProxy(host='DOES_NOT_MATTER', port=0000)
            neo4j_proxy.add_badge(id='dummy_uri/dummy_column',
                                  badge_name='hive',
                                  resource_type=ResourceType.Column)
            # we call neo4j twice in add_tag call
            self.assertEqual(mock_run.call_count, 3)
            self.assertEqual(mock_commit.call_count, 1)

    def test_add_tag(self) -> None:
        with patch.object(GraphDatabase, 'driver') as mock_driver:
            mock_session = MagicMock()
            mock_driver.return_value.session.return_value = mock_session

            mock_transaction = MagicMock()
            mock_session.begin_transaction.return_value = mock_transaction

            mock_run = MagicMock()
            mock_transaction.run = mock_run
            mock_commit = MagicMock()
            mock_transaction.commit = mock_commit

            neo4j_proxy = Neo4jProxy(host='DOES_NOT_MATTER', port=0000)
            neo4j_proxy.add_tag(id='dummy_uri',
                                tag='hive')
            # we call neo4j twice in add_tag call
            self.assertEqual(mock_run.call_count, 3)
            self.assertEqual(mock_commit.call_count, 1)

    def test_delete_tag(self) -> None:
        with patch.object(GraphDatabase, 'driver') as mock_driver:
            mock_session = MagicMock()
            mock_driver.return_value.session.return_value = mock_session

            mock_transaction = MagicMock()
            mock_session.begin_transaction.return_value = mock_transaction

            mock_run = MagicMock()
            mock_transaction.run = mock_run
            mock_commit = MagicMock()
            mock_transaction.commit = mock_commit

            neo4j_proxy = Neo4jProxy(host='DOES_NOT_MATTER', port=0000)
            neo4j_proxy.delete_tag(id='dummy_uri',
                                   tag='hive')
            # we only call neo4j once in delete_tag call
            self.assertEqual(mock_run.call_count, 1)
            self.assertEqual(mock_commit.call_count, 1)

    def test_get_tags(self) -> None:
        with patch.object(GraphDatabase, 'driver'), patch.object(Neo4jProxy, '_execute_cypher_query') as mock_execute:
            mock_execute.return_value = [
                {'tag_name': {'key': 'tag1'}, 'tag_count': 2},
                {'tag_name': {'key': 'tag2'}, 'tag_count': 1}
            ]

            neo4j_proxy = Neo4jProxy(host='DOES_NOT_MATTER', port=0000)
            actual = neo4j_proxy.get_tags()

            expected = [
                TagDetail(tag_name='tag1', tag_count=2),
                TagDetail(tag_name='tag2', tag_count=1),
            ]

            self.assertEqual(actual.__repr__(), expected.__repr__())

    def test_get_neo4j_latest_updated_ts(self) -> None:
        with patch.object(GraphDatabase, 'driver'), patch.object(Neo4jProxy, '_execute_cypher_query') as mock_execute:
            mock_execute.return_value.single.return_value = {
                'ts': {
                    'latest_timestamp': '1000'
                }
            }
            neo4j_proxy = Neo4jProxy(host='DOES_NOT_MATTER', port=0000)
            neo4j_last_updated_ts = neo4j_proxy.get_latest_updated_ts()
            self.assertEqual(neo4j_last_updated_ts, '1000')

            mock_execute.return_value.single.return_value = {
                'ts': {

                }
            }
            neo4j_proxy = Neo4jProxy(host='DOES_NOT_MATTER', port=0000)
            neo4j_last_updated_ts = neo4j_proxy.get_latest_updated_ts()
            self.assertEqual(neo4j_last_updated_ts, 0)

            mock_execute.return_value.single.return_value = None
            neo4j_proxy = Neo4jProxy(host='DOES_NOT_MATTER', port=0000)
            neo4j_last_updated_ts = neo4j_proxy.get_latest_updated_ts()
            self.assertIsNone(neo4j_last_updated_ts)

    def test_get_statistics(self) -> None:
        with patch.object(GraphDatabase, 'driver'), patch.object(Neo4jProxy, '_execute_cypher_query') as mock_execute:
            mock_execute.return_value = [
                {'number_of_tables': '2', 'number_of_documented_tables': '1', 'number_of_documented_cols': '1',
                 'number_of_owners': '1', 'number_of_tables_with_owners': '1',
                 'number_of_documented_and_owned_tables': '1'}]
            neo4j_proxy = Neo4jProxy(host='DOES_NOT_MATTER', port=0000)
            neo4j_statistics = neo4j_proxy.get_statistics()
            self.assertEqual(neo4j_statistics, {'number_of_tables': '2', 'number_of_documented_tables': '1',
                                                'number_of_documented_cols': '1', 'number_of_owners': '1',
                                                'number_of_tables_with_owners': '1',
                                                'number_of_documented_and_owned_tables': '1'})

    def test_get_popular_tables(self) -> None:
        # Test cache hit for global popular tables
        with patch.object(GraphDatabase, 'driver'), patch.object(Neo4jProxy, '_execute_cypher_query') as mock_execute:
            mock_execute.return_value = [{'resource_key': 'foo'}, {'resource_key': 'bar'}]

            neo4j_proxy = Neo4jProxy(host='DOES_NOT_MATTER', port=0000)
            self.assertEqual(neo4j_proxy._get_global_popular_resources_uris(2), ['foo', 'bar'])
            self.assertEqual(neo4j_proxy._get_global_popular_resources_uris(2), ['foo', 'bar'])
            self.assertEqual(neo4j_proxy._get_global_popular_resources_uris(2), ['foo', 'bar'])

            self.assertEqual(mock_execute.call_count, 1)

        # Test cache hit for personal popular tables
        with patch.object(GraphDatabase, 'driver'), patch.object(Neo4jProxy, '_execute_cypher_query') as mock_execute:
            mock_execute.return_value = [{'resource_key': 'foo'}, {'resource_key': 'bar'}]

            neo4j_proxy = Neo4jProxy(host='DOES_NOT_MATTER', port=0000)
            self.assertEqual(neo4j_proxy._get_personal_popular_resources_uris(2, 'test_id'), ['foo', 'bar'])
            self.assertEqual(neo4j_proxy._get_personal_popular_resources_uris(2, 'test_id'), ['foo', 'bar'])
            self.assertEqual(neo4j_proxy._get_personal_popular_resources_uris(2, 'other_id'), ['foo', 'bar'])

            self.assertEqual(mock_execute.call_count, 2)

        with patch.object(GraphDatabase, 'driver'), patch.object(Neo4jProxy, '_execute_cypher_query') as mock_execute:
            mock_execute.return_value = [
                {'database_name': 'db', 'cluster_name': 'clstr', 'schema_name': 'sch', 'table_name': 'foo',
                 'table_description': 'test description'},
                {'database_name': 'db', 'cluster_name': 'clstr', 'schema_name': 'sch', 'table_name': 'bar'}
            ]

            neo4j_proxy = Neo4jProxy(host='DOES_NOT_MATTER', port=0000)
            actual = neo4j_proxy.get_popular_tables(num_entries=2)

            expected = [
                PopularTable(database='db', cluster='clstr', schema='sch', name='foo', description='test description'),
                PopularTable(database='db', cluster='clstr', schema='sch', name='bar'),
            ]

            self.assertEqual(actual.__repr__(), expected.__repr__())

    def test_get_popular_resources_table(self) -> None:
        with patch.object(GraphDatabase, 'driver'), patch.object(Neo4jProxy, '_get_popular_tables') as mock_execute:
            mock_execute.return_value = [
                TableSummary(**{'database': 'db', 'cluster': 'clstr', 'schema': 'sch', 'name': 'foo',
                                'description': 'test description'}),
                TableSummary(**{'database': 'db', 'cluster': 'clstr', 'schema': 'sch', 'name': 'bar'})
            ]

            neo4j_proxy = Neo4jProxy(host='DOES_NOT_MATTER', port=0000)
            actual = neo4j_proxy.get_popular_resources(num_entries=2, resource_types=["table"])

            expected = {
                ResourceType.Table.name: [
                    TableSummary(database='db', cluster='clstr', schema='sch', name='foo',
                                 description='test description'),
                    TableSummary(database='db', cluster='clstr', schema='sch', name='bar')
                ]
            }

            self.assertEqual(expected.__repr__(), actual.__repr__())

    def test_get_popular_resources_table_dashboard(self) -> None:
        with patch.object(GraphDatabase, 'driver'), patch.object(Neo4jProxy, '_get_popular_tables') as mock_execute:
            mock_execute.return_value = [
                TableSummary(**{'database': 'db', 'cluster': 'clstr', 'schema': 'sch', 'name': 'foo',
                                'description': 'test description'}),
                TableSummary(**{'database': 'db', 'cluster': 'clstr', 'schema': 'sch', 'name': 'bar'})
            ]

            neo4j_proxy = Neo4jProxy(host='DOES_NOT_MATTER', port=0000)
            actual = neo4j_proxy.get_popular_resources(num_entries=2, resource_types=["table", "dashboard"])

            expected = {
                ResourceType.Table.name: [
                    TableSummary(database='db', cluster='clstr', schema='sch', name='foo',
                                 description='test description'),
                    TableSummary(database='db', cluster='clstr', schema='sch', name='bar')
                ],
                ResourceType.Dashboard.name: []
            }

            self.assertEqual(expected.__repr__(), actual.__repr__())

    def test_get_user(self) -> None:
        with patch.object(GraphDatabase, 'driver'), patch.object(Neo4jProxy, '_execute_cypher_query') as mock_execute:
            mock_execute.return_value.single.return_value = {
                'user_record': {
                    'employee_type': 'teamMember',
                    'full_name': 'test_full_name',
                    'is_active': 'True',
                    'github_username': 'test-github',
                    'slack_id': 'test_id',
                    'last_name': 'test_last_name',
                    'first_name': 'test_first_name',
                    'team_name': 'test_team',
                    'email': 'test_email',
                },
                'manager_record': {
                    'full_name': 'test_manager_fullname'
                }
            }
            neo4j_proxy = Neo4jProxy(host='DOES_NOT_MATTER', port=0000)
            neo4j_user = neo4j_proxy.get_user(id='test_email')
            self.assertEqual(neo4j_user.email, 'test_email')

    def test_get_user_other_key_values(self) -> None:
        with patch.object(GraphDatabase, 'driver'), patch.object(Neo4jProxy, '_execute_cypher_query') as mock_execute:
            mock_execute.return_value.single.return_value = {
                'user_record': {
                    'employee_type': 'teamMember',
                    'full_name': 'test_full_name',
                    'is_active': 'True',
                    'github_username': 'test-github',
                    'slack_id': 'test_id',
                    'last_name': 'test_last_name',
                    'first_name': 'test_first_name',
                    'team_name': 'test_team',
                    'email': 'test_email',
                    'mode_user_id': 'mode_foo_bar',
                    'etc': 'etc_foo_bar',
                },
                'manager_record': {
                    'full_name': 'test_manager_fullname'
                }
            }
            neo4j_proxy = Neo4jProxy(host='DOES_NOT_MATTER', port=0000)
            neo4j_user = neo4j_proxy.get_user(id='test_email')
            self.assertEqual(neo4j_user.other_key_values, {'mode_user_id': 'mode_foo_bar'})

    def test_put_user_new_user(self) -> None:
        """
        Test creating a new user
        :return:
        """
        with patch.object(GraphDatabase, 'driver') as mock_driver:
            mock_transaction = mock_driver.return_value.session.return_value.begin_transaction.return_value
            mock_run = mock_transaction.run
            mock_commit = mock_transaction.commit

            test_user = MagicMock()

            neo4j_proxy = Neo4jProxy(host='DOES_NOT_MATTER', port=0000)
            neo4j_proxy.create_update_user(user=test_user)

            self.assertEqual(mock_run.call_count, 1)
            self.assertEqual(mock_commit.call_count, 1)

    def test_get_users(self) -> None:
        with patch.object(GraphDatabase, 'driver'), patch.object(Neo4jProxy, '_execute_cypher_query') as mock_execute:
            test_user = {
                'employee_type': 'teamMember',
                'full_name': 'test_full_name',
                'is_active': True,
                'github_username': 'test-github',
                'slack_id': 'test_id',
                'last_name': 'test_last_name',
                'first_name': 'test_first_name',
                'team_name': 'test_team',
                'email': 'test_email',
                'manager_fullname': 'test_manager',
            }
            test_user_obj = UserModel(email='test_email',
                                      first_name='test_first_name',
                                      last_name='test_last_name',
                                      full_name='test_full_name',
                                      is_active=True,
                                      github_username='test-github',
                                      team_name='test_team',
                                      slack_id='test_id',
                                      employee_type='teamMember',
                                      manager_fullname='test_manager')

    # TODO: Add frequent_used, bookmarked, & owned resources)
            mock_execute.return_value.single.return_value = {'users': [test_user]}
            neo4j_proxy = Neo4jProxy(host='DOES_NOT_MATTER', port=0000)
            users = neo4j_proxy.get_users()
            actual_data = [test_user_obj]
            for attr in ['employee_type',
                         'full_name',
                         'is_active',
                         'github_username',
                         'slack_id',
                         'last_name',
                         'first_name',
                         'team_name',
                         'email',
                         'manager_fullname']:
                self.assertEqual(getattr(users[0], attr),
                                 getattr(actual_data[0], attr))

    def test_get_table_by_user_relation(self) -> None:
        with patch.object(GraphDatabase, 'driver'), patch.object(Neo4jProxy, '_execute_cypher_query') as mock_execute:
            mock_execute.return_value = [
                {
                    'resource': {
                        'name': 'table_name'
                    },
                    'db': {
                        'name': 'db_name'
                    },
                    'clstr': {
                        'name': 'cluster'
                    },
                    'schema': {
                        'name': 'schema'
                    },
                }
            ]

            neo4j_proxy = Neo4jProxy(host='DOES_NOT_MATTER', port=0000)
            result = neo4j_proxy.get_table_by_user_relation(user_email='test_user',
                                                            relation_type=UserResourceRel.follow)
            self.assertEqual(len(result['table']), 1)
            self.assertEqual(result['table'][0].name, 'table_name')
            self.assertEqual(result['table'][0].database, 'db_name')
            self.assertEqual(result['table'][0].cluster, 'cluster')
            self.assertEqual(result['table'][0].schema, 'schema')

    def test_get_dashboard_by_user_relation(self) -> None:
        with patch.object(GraphDatabase, 'driver'), patch.object(Neo4jProxy, '_execute_cypher_query') as mock_execute:
            mock_execute.return_value = [
                {
                    'uri': 'dashboard_uri',
                    'cluster_name': 'cluster',
                    'dg_name': 'dashboard_group',
                    'dg_url': 'http://foo.bar/group',
                    'product': 'foobar',
                    'name': 'dashboard',
                    'url': 'http://foo.bar/dashboard',
                    'description': 'description',
                    'last_successful_run_timestamp': 1234567890
                }
            ]

            neo4j_proxy = Neo4jProxy(host='DOES_NOT_MATTER', port=0000)
            result = neo4j_proxy.get_dashboard_by_user_relation(user_email='test_user',
                                                                relation_type=UserResourceRel.follow)

            expected = DashboardSummary(uri='dashboard_uri',
                                        cluster='cluster',
                                        group_name='dashboard_group',
                                        group_url='http://foo.bar/group',
                                        product='foobar',
                                        name='dashboard',
                                        url='http://foo.bar/dashboard',
                                        description='description',
                                        last_successful_run_timestamp=1234567890)

            self.assertEqual(len(result['dashboard']), 1)
            self.assertEqual(expected, result['dashboard'][0])

    def test_add_resource_relation_by_user(self) -> None:
        with patch.object(GraphDatabase, 'driver') as mock_driver:
            mock_session = MagicMock()
            mock_driver.return_value.session.return_value = mock_session

            mock_transaction = MagicMock()
            mock_session.begin_transaction.return_value = mock_transaction

            mock_run = MagicMock()
            mock_transaction.run = mock_run
            mock_commit = MagicMock()
            mock_transaction.commit = mock_commit

            neo4j_proxy = Neo4jProxy(host='DOES_NOT_MATTER', port=0000)
            neo4j_proxy.add_resource_relation_by_user(id='dummy_uri',
                                                      user_id='tester',
                                                      relation_type=UserResourceRel.follow,
                                                      resource_type=ResourceType.Table)
            self.assertEqual(mock_run.call_count, 2)
            self.assertEqual(mock_commit.call_count, 1)

    def test_delete_resource_relation_by_user(self) -> None:
        with patch.object(GraphDatabase, 'driver') as mock_driver:
            mock_session = MagicMock()
            mock_driver.return_value.session.return_value = mock_session

            mock_transaction = MagicMock()
            mock_session.begin_transaction.return_value = mock_transaction

            mock_run = MagicMock()
            mock_transaction.run = mock_run
            mock_commit = MagicMock()
            mock_transaction.commit = mock_commit

            neo4j_proxy = Neo4jProxy(host='DOES_NOT_MATTER', port=0000)
            neo4j_proxy.delete_resource_relation_by_user(id='dummy_uri',
                                                         user_id='tester',
                                                         relation_type=UserResourceRel.follow,
                                                         resource_type=ResourceType.Table)
            self.assertEqual(mock_run.call_count, 1)
            self.assertEqual(mock_commit.call_count, 1)

    def test_get_invalid_user(self) -> None:
        with patch.object(GraphDatabase, 'driver'), patch.object(Neo4jProxy, '_execute_cypher_query') as mock_execute:
            mock_execute.return_value.single.return_value = None
            neo4j_proxy = Neo4jProxy(host='DOES_NOT_MATTER', port=0000)
            self.assertRaises(NotFoundException, neo4j_proxy.get_user, id='invalid_email')

    def test_get_dashboard(self) -> None:
        with patch.object(GraphDatabase, 'driver'), patch.object(Neo4jProxy, '_execute_cypher_query') as mock_execute:
            mock_execute.return_value.single.side_effect = [
                {
                    'cluster_name': 'cluster_name',
                    'uri': 'foo_dashboard://gold.bar/dashboard_id',
                    'url': 'http://www.foo.bar/dashboard_id',
                    'product': 'foobar',
                    'name': 'dashboard name',
                    'created_timestamp': 123456789,
                    'description': 'description',
                    'group_name': 'group_name',
                    'group_url': 'http://www.group_url.com',
                    'last_successful_run_timestamp': 9876543210,
                    'last_run_timestamp': 987654321,
                    'last_run_state': 'good_state',
                    'updated_timestamp': 123456654321,
                    'recent_view_count': 100,
                    'owners': [
                        {
                            'employee_type': 'teamMember',
                            'full_name': 'test_full_name',
                            'is_active': True,
                            'github_username': 'test-github',
                            'slack_id': 'test_id',
                            'last_name': 'test_last_name',
                            'first_name': 'test_first_name',
                            'team_name': 'test_team',
                            'email': 'test_email',
                        },
                        {
                            'employee_type': 'teamMember',
                            'full_name': 'test_full_name2',
                            'is_active': True,
                            'github_username': 'test-github2',
                            'slack_id': 'test_id2',
                            'last_name': 'test_last_name2',
                            'first_name': 'test_first_name2',
                            'team_name': 'test_team2',
                            'email': 'test_email2',
                        }

                    ],
                    'tags': [
                        {
                            'key': 'tag_key1',
                            'tag_type': 'tag_type1'
                        },
                        {
                            'key': 'tag_key2',
                            'tag_type': 'tag_type2'

                        }
                    ],
                    'badges': [
                        {
                            'key': 'golden',
                            'category': 'table_status'
                        }
                    ],
                    'charts': [{'name': 'chart1'}, {'name': 'chart2'}],
                    'queries': [{'name': 'query1'}, {'name': 'query2', 'url': 'http://foo.bar/query',
                                                     'query_text': 'SELECT * FROM foo.bar'}],
                    'tables': [
                        {
                            'database': 'db1',
                            'name': 'table1',
                            'description': 'table description 1',
                            'cluster': 'cluster1',
                            'schema': 'schema1'
                        },
                        {
                            'database': 'db2',
                            'name': 'table2',
                            'description': None,
                            'cluster': 'cluster2',
                            'schema': 'schema2'
                        }
                    ]
                },
                {
                    'cluster_name': 'cluster_name',
                    'uri': 'foo_dashboard://gold.bar/dashboard_id',
                    'url': 'http://www.foo.bar/dashboard_id',
                    'product': 'foobar',
                    'name': 'dashboard name',
                    'created_timestamp': 123456789,
                    'description': None,
                    'group_name': 'group_name',
                    'group_url': 'http://www.group_url.com',
                    'last_run_timestamp': None,
                    'last_run_state': None,
                    'updated_timestamp': None,
                    'recent_view_count': 0,
                    'owners': [],
                    'tags': [],
                    'badges': [],
                    'charts': [],
                    'queries': [],
                    'tables': []
                }
            ]
            neo4j_proxy = Neo4jProxy(host='DOES_NOT_MATTER', port=0000)
            dashboard = neo4j_proxy.get_dashboard(id='dashboard_id')
            expected = DashboardDetail(uri='foo_dashboard://gold.bar/dashboard_id', cluster='cluster_name',
                                       group_name='group_name', group_url='http://www.group_url.com',
                                       product='foobar',
                                       name='dashboard name', url='http://www.foo.bar/dashboard_id',
                                       description='description', created_timestamp=123456789,
                                       last_successful_run_timestamp=9876543210,
                                       updated_timestamp=123456654321, last_run_timestamp=987654321,
                                       last_run_state='good_state',
                                       owners=[User(email='test_email', user_id='test_email',
                                                    first_name='test_first_name',
                                                    last_name='test_last_name',
                                                    full_name='test_full_name', is_active=True,
                                                    github_username='test-github',
                                                    team_name='test_team', slack_id='test_id',
                                                    employee_type='teamMember', manager_fullname=None),
                                               User(email='test_email2', user_id='test_email2',
                                                    first_name='test_first_name2',
                                                    last_name='test_last_name2',
                                                    full_name='test_full_name2', is_active=True,
                                                    github_username='test-github2',
                                                    team_name='test_team2', slack_id='test_id2',
                                                    employee_type='teamMember', manager_fullname=None)],
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
                                       tags=[Tag(tag_type='tag_type1', tag_name='tag_key1'),
                                             Tag(tag_type='tag_type2', tag_name='tag_key2')],
                                       badges=[Badge(badge_name='golden', category='table_status')],
                                       recent_view_count=100)

            self.assertEqual(expected, dashboard)

            dashboard2 = neo4j_proxy.get_dashboard(id='dashboard_id')
            expected2 = DashboardDetail(uri='foo_dashboard://gold.bar/dashboard_id', cluster='cluster_name',
                                        group_name='group_name', group_url='http://www.group_url.com',
                                        product='foobar', name='dashboard name',
                                        url='http://www.foo.bar/dashboard_id', description=None,
                                        created_timestamp=123456789, updated_timestamp=None, last_run_timestamp=None,
                                        last_run_state=None, owners=[], frequent_users=[], chart_names=[],
                                        query_names=[], tables=[], tags=[], badges=[],
                                        last_successful_run_timestamp=None, recent_view_count=0)

            self.assertEqual(expected2, dashboard2)

    def test_get_dashboard_with_valid_description(self) -> None:
        """
        Test description is returned for dashboard
        :return:
        """
        with patch.object(GraphDatabase, 'driver'), patch.object(Neo4jProxy, '_execute_cypher_query') as mock_execute:
            mock_execute.return_value.single.return_value = dict(description='sample description')

            neo4j_proxy = Neo4jProxy(host='DOES_NOT_MATTER', port=0000)
            table_description = neo4j_proxy.get_dashboard_description(id='test_dashboard')

            dashboard_description_query = textwrap.dedent("""
            MATCH (n:Dashboard {key: $key})-[:DESCRIPTION]->(d:Description)
            RETURN d.description AS description;
            """)
            mock_execute.assert_called_with(statement=dashboard_description_query,
                                            param_dict={'key': 'test_dashboard'})

            self.assertEqual(table_description.description, 'sample description')

    def test_get_dashboard_with_no_description(self) -> None:
        """
        Test None is returned for table with no description
        :return:
        """
        with patch.object(GraphDatabase, 'driver'), patch.object(Neo4jProxy, '_execute_cypher_query') as mock_execute:
            mock_execute.return_value.single.return_value = None

            neo4j_proxy = Neo4jProxy(host='DOES_NOT_MATTER', port=0000)
            table_description = neo4j_proxy.get_dashboard_description(id='test_dashboard')

            dashboard_description_query = textwrap.dedent("""
            MATCH (n:Dashboard {key: $key})-[:DESCRIPTION]->(d:Description)
            RETURN d.description AS description;
            """)
            mock_execute.assert_called_with(statement=dashboard_description_query,
                                            param_dict={'key': 'test_dashboard'})

            self.assertIsNone(table_description.description)

    def test_put_dashboard_description(self) -> None:
        """
        Test updating table description
        :return:
        """
        with patch.object(GraphDatabase, 'driver') as mock_driver:
            mock_session = MagicMock()
            mock_driver.return_value.session.return_value = mock_session

            mock_transaction = MagicMock()
            mock_session.begin_transaction.return_value = mock_transaction

            mock_run = MagicMock()
            mock_transaction.run = mock_run
            mock_commit = MagicMock()
            mock_transaction.commit = mock_commit

            neo4j_proxy = Neo4jProxy(host='DOES_NOT_MATTER', port=0000)
            neo4j_proxy.put_dashboard_description(id='test_dashboard',
                                                  description='test_description')

            self.assertEqual(mock_run.call_count, 2)
            self.assertEqual(mock_commit.call_count, 1)

            expected_stmt = textwrap.dedent("""
            MATCH (n1:Description {key: $desc_key}), (n2:Dashboard {key: $key})
            MERGE (n2)-[r2:DESCRIPTION]->(n1)
            RETURN n1.key, n2.key
            """)
            mock_run.assert_called_with(expected_stmt, {'desc_key': 'test_dashboard/_description',
                                                        'key': 'test_dashboard'})

    def test_user_resource_relation_clause(self) -> None:
        with patch.object(GraphDatabase, 'driver'):
            neo4j_proxy = Neo4jProxy(host='DOES_NOT_MATTER', port=0000)
            actual = neo4j_proxy._get_user_resource_relationship_clause(UserResourceRel.follow,
                                                                        id='foo',
                                                                        user_key='bar',
                                                                        resource_type=ResourceType.Table)
            expected = '(resource:Table {key: $resource_key})-[r1:FOLLOWED_BY]->(usr:User {key: $user_key})-' \
                       '[r2:FOLLOW]->(resource:Table {key: $resource_key})'
            self.assertEqual(expected, actual)

            actual = neo4j_proxy._get_user_resource_relationship_clause(UserResourceRel.read,
                                                                        id='foo',
                                                                        user_key='bar',
                                                                        resource_type=ResourceType.Table)
            expected = '(resource:Table {key: $resource_key})-[r1:READ_BY]->(usr:User {key: $user_key})-[r2:READ]->' \
                       '(resource:Table {key: $resource_key})'
            self.assertEqual(expected, actual)

            actual = neo4j_proxy._get_user_resource_relationship_clause(UserResourceRel.own,
                                                                        id='foo',
                                                                        user_key='bar',
                                                                        resource_type=ResourceType.Table)
            expected = '(resource:Table {key: $resource_key})-[r1:OWNER]->(usr:User {key: $user_key})-[r2:OWNER_OF]->' \
                       '(resource:Table {key: $resource_key})'
            self.assertEqual(expected, actual)

            actual = neo4j_proxy._get_user_resource_relationship_clause(UserResourceRel.follow,
                                                                        id='foo',
                                                                        user_key='bar',
                                                                        resource_type=ResourceType.Dashboard)
            expected = '(resource:Dashboard {key: $resource_key})-[r1:FOLLOWED_BY]->(usr:User {key: $user_key})-' \
                       '[r2:FOLLOW]->(resource:Dashboard {key: $resource_key})'
            self.assertEqual(expected, actual)

    def test_get_lineage_no_lineage_information(self) -> None:
        with patch.object(GraphDatabase, 'driver'), patch.object(Neo4jProxy, '_execute_cypher_query') as mock_execute:
            key = "alpha"
            mock_execute.return_value.single.side_effect = [{}]

            expected = Lineage(
                key=key,
                upstream_entities=[],
                downstream_entities=[],
                direction="both",
                depth=1
            )

            neo4j_proxy = Neo4jProxy(host='DOES_NOT_MATTER', port=0000)
            actual = neo4j_proxy.get_lineage(id=key, resource_type=ResourceType.Table, direction="both", depth=1)
            self.assertEqual(expected, actual)

    def test_get_lineage_success(self) -> None:
        with patch.object(GraphDatabase, 'driver'), patch.object(Neo4jProxy, '_execute_cypher_query') as mock_execute:
            key = "alpha"
            mock_execute.return_value.single.side_effect = [{
                "upstream_entities": [
                    {"key": "beta", "source": "gold", "level": 1, "badges": [], "usage":100, "parent": None},
                    {"key": "gamma", "source": "dyno", "level": 1,
                     "badges":
                        [
                            {"key": "badge1", "category": "default"},
                            {"key": "badge2", "category": "default"},
                        ],
                     "usage": 200, "parent": None},
                ],
                "downstream_entities": [
                    {"key": "delta", "source": "gold", "level": 1, "badges": [], "usage": 50, "parent": None},
                ]
            }]

            expected = Lineage(
                key=key,
                upstream_entities=[
                    LineageItem(**{"key": "beta", "source": "gold", "level": 1, "badges": [], "usage":100}),
                    LineageItem(**{"key": "gamma", "source": "dyno", "level": 1,
                                   "badges":
                                       [
                                           Badge(**{"badge_name": "badge1", "category": "default"}),
                                           Badge(**{"badge_name": "badge2", "category": "default"})
                                       ],
                                   "usage": 200}),
                ],
                downstream_entities=[
                    LineageItem(**{"key": "delta", "source": "gold", "level": 1, "badges": [], "usage": 50})
                ],
                direction="both",
                depth=1
            )

            neo4j_proxy = Neo4jProxy(host='DOES_NOT_MATTER', port=0000)
            actual = neo4j_proxy.get_lineage(id=key, resource_type=ResourceType.Table, direction="both", depth=1)
            self.assertEqual(expected.__repr__(), actual.__repr__())

    def test_get_feature_success(self) -> None:
        with patch.object(GraphDatabase, 'driver'), patch.object(Neo4jProxy, '_execute_cypher_query') as mock_execute:
            mock_execute.return_value.single.side_effect = [{
                'wmk_records': [
                    {
                        'key': 'test_feature_group/test_feature_name/1.2.3/high_watermark',
                        'time': 'fake_time',
                    },
                    {
                        'key': 'test_feature_group/test_feature_name/1.2.3/low_watermark',
                        'time': 'fake_time',
                    }
                ],
                'availability_records': [
                    {
                        'name': 'hive',
                        'publisher_last_updated_epoch_ms': 1621250037268,
                        'published_tag': '2021-05-16',
                        'key': 'database://hive'
                    },
                    {
                        'name': 'dynamodb',
                        'publisher_last_updated_epoch_ms': 1621250037268,
                        'published_tag': '2021-05-16',
                        'key': 'database://dynamodb'
                    }
                ],
                'prog_descriptions': [
                    {
                        'description_source': 'quality_report',
                        'description': 'Test Test'
                    }
                ],
                'owner_records': [
                    {
                        'key': 'tester@example.com',
                        'email': 'tester@example.com'
                    }
                ],
                'badge_records': [
                    {
                        'key': 'pii',
                        'category': 'data'
                    }
                ],
                'tag_records': [
                    {
                        'tag_type': 'default', 'key': 'test'
                    },
                ],
                'desc': {
                    'description': 'test feature description',
                    'key': 'test_feature_group/test_feature_name/1.2.3/_description',
                    'description_source': 'description'
                },
                'feat': {
                    'last_updated_timestamp': 1,
                    'data_type': 'bigint',
                    'name': 'test_feature_name',
                    'created_timestamp': 1,
                    'version': '1.2.3',
                    'key': 'test_feature_group/test_feature_name/1.2.3',
                    'status': 'active',
                    'entity': 'test_entity'
                },
                'fg': {
                    'name': 'test_feature_group',
                }
            }]

            neo4j_proxy = Neo4jProxy(host='DOES_NOT_MATTER', port=0000)
            feature = neo4j_proxy.get_feature(feature_uri='dummy_uri')
            expected = Feature(key='test_feature_group/test_feature_name/1.2.3',
                               name='test_feature_name',
                               version='1.2.3', status='active',
                               feature_group='test_feature_group', entity='test_entity',
                               data_type='bigint', availability=['hive', 'dynamodb'],
                               description='test feature description',
                               owners=[User(email='tester@example.com')],
                               badges=[Badge(badge_name='pii', category='data')],
                               tags=[Tag(tag_name='test', tag_type='default')],
                               programmatic_descriptions=[
                                   ProgrammaticDescription(source='quality_report',
                                                           text='Test Test'),
                               ],
                               watermarks=[FeatureWatermark(
                                   key='test_feature_group/test_feature_name/1.2.3/high_watermark',
                                   watermark_type='high_watermark',
                                   time='fake_time'),
                                   FeatureWatermark(
                                       key='test_feature_group/test_feature_name/1.2.3/low_watermark',
                                       watermark_type='low_watermark',
                                       time='fake_time')],
                               last_updated_timestamp=1,
                               created_timestamp=1,
                               )

            self.assertEqual(str(expected), str(feature))

    def test_get_feature_not_found(self) -> None:
        with patch.object(GraphDatabase, 'driver'), patch.object(Neo4jProxy, '_execute_cypher_query') as mock_execute:
            mock_execute.return_value = None
            neo4j_proxy = Neo4jProxy(host='DOES_NOT_MATTER', port=0000)

            self.assertRaises(NotFoundException, neo4j_proxy._exec_feature_query, feature_key='invalid_feat_uri')
            self.assertRaises(NotFoundException, neo4j_proxy.get_feature, feature_uri='invalid_feat_uri')

    def test_get_resource_generation_code_success(self) -> None:
        with patch.object(GraphDatabase, 'driver'), patch.object(Neo4jProxy, '_execute_cypher_query') as mock_execute:
            mock_execute.return_value.single.side_effect = [
                {'query_records': {
                    'key': 'test_feature_group/test_feature_name/1.2.3/_generation_code',
                    'text': 'SELECT * FROM test_table',
                    'source': 'test_source'}}]

            neo4j_proxy = Neo4jProxy(host='DOES_NOT_MATTER', port=0000)
            gen_code = neo4j_proxy.get_resource_generation_code(uri='dummy_uri',
                                                                resource_type=ResourceType.Feature)
            expected = GenerationCode(key='test_feature_group/test_feature_name/1.2.3/_generation_code',
                                      text='SELECT * FROM test_table',
                                      source='test_source')
        self.assertEqual(str(expected), str(gen_code))

    def test_get_resource_generation_code_not_found(self) -> None:
        with patch.object(GraphDatabase, 'driver'), patch.object(Neo4jProxy, '_execute_cypher_query') as mock_execute:
            mock_execute.return_value = None
            neo4j_proxy = Neo4jProxy(host='DOES_NOT_MATTER', port=0000)

            self.assertRaises(NotFoundException,
                              neo4j_proxy.get_resource_generation_code,
                              uri='invalid_feat_uri',
                              resource_type=ResourceType.Feature)


if __name__ == '__main__':
    unittest.main()
