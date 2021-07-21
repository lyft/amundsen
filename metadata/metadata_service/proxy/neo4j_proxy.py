# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import logging
import textwrap
import time
from random import randint
from typing import (Any, Dict, Iterable, List, Optional, Tuple,  # noqa: F401
                    Union, no_type_check)

import neo4j
import neobolt
from amundsen_common.entity.resource_type import ResourceType, to_resource_type
from amundsen_common.models.api import health_check
from amundsen_common.models.dashboard import DashboardSummary
from amundsen_common.models.feature import Feature, FeatureWatermark
from amundsen_common.models.generation_code import GenerationCode
from amundsen_common.models.lineage import Lineage, LineageItem
from amundsen_common.models.popular_table import PopularTable
from amundsen_common.models.table import (Application, Badge, Column,
                                          ProgrammaticDescription, Reader,
                                          Source, SqlJoin, SqlWhere, Stat,
                                          Table, TableSummary, Tag, User,
                                          Watermark)
from amundsen_common.models.user import User as UserEntity
from amundsen_common.models.user import UserSchema
from beaker.cache import CacheManager
from beaker.util import parse_cache_config_options
from flask import current_app, has_app_context
from neo4j import BoltStatementResult, Driver, GraphDatabase  # noqa: F401

from metadata_service import config
from metadata_service.entity.dashboard_detail import \
    DashboardDetail as DashboardDetailEntity
from metadata_service.entity.dashboard_query import \
    DashboardQuery as DashboardQueryEntity
from metadata_service.entity.description import Description
from metadata_service.entity.tag_detail import TagDetail
from metadata_service.exception import NotFoundException
from metadata_service.proxy.base_proxy import BaseProxy
from metadata_service.proxy.statsd_utilities import timer_with_counter
from metadata_service.util import UserResourceRel

_CACHE = CacheManager(**parse_cache_config_options({'cache.type': 'memory'}))

# Expire cache every 11 hours + jitter
_GET_POPULAR_RESOURCES_CACHE_EXPIRY_SEC = 11 * 60 * 60 + randint(0, 3600)


CREATED_EPOCH_MS = 'publisher_created_epoch_ms'
LAST_UPDATED_EPOCH_MS = 'publisher_last_updated_epoch_ms'
PUBLISHED_TAG_PROPERTY_NAME = 'published_tag'


LOGGER = logging.getLogger(__name__)


class Neo4jProxy(BaseProxy):
    """
    A proxy to Neo4j (Gateway to Neo4j)
    """

    def __init__(self, *,
                 host: str,
                 port: int,
                 user: str = 'neo4j',
                 password: str = '',
                 num_conns: int = 50,
                 max_connection_lifetime_sec: int = 100,
                 encrypted: bool = False,
                 validate_ssl: bool = False,
                 **kwargs: dict) -> None:
        """
        There's currently no request timeout from client side where server
        side can be enforced via "dbms.transaction.timeout"
        By default, it will set max number of connections to 50 and connection time out to 10 seconds.
        :param endpoint: neo4j endpoint
        :param num_conns: number of connections
        :param max_connection_lifetime_sec: max life time the connection can have when it comes to reuse. In other
        words, connection life time longer than this value won't be reused and closed on garbage collection. This
        value needs to be smaller than surrounding network environment's timeout.
        """
        endpoint = f'{host}:{port}'
        LOGGER.info('NEO4J endpoint: {}'.format(endpoint))
        trust = neo4j.TRUST_SYSTEM_CA_SIGNED_CERTIFICATES if validate_ssl else neo4j.TRUST_ALL_CERTIFICATES
        self._driver = GraphDatabase.driver(endpoint, max_connection_pool_size=num_conns,
                                            connection_timeout=10,
                                            max_connection_lifetime=max_connection_lifetime_sec,
                                            auth=(user, password),
                                            encrypted=encrypted,
                                            trust=trust)  # type: Driver

    def health(self) -> health_check.HealthCheck:
        """
        Runs one or more series of checks on the service. Can also
        optionally return additional metadata about each check (e.g.
        latency to database, cpu utilization, etc.).
        """
        checks = {}
        try:
            # dbms.cluster.overview() is only available for enterprise neo4j users
            cluster_overview = self._execute_cypher_query(statement='CALL dbms.cluster.overview()', param_dict={})
            checks = dict(cluster_overview.single())
            checks['overview_enabled'] = True
            status = health_check.OK
        except neobolt.exceptions.ClientError:
            checks = {'overview_enabled': False}
            status = health_check.OK  # Can connect to database but plugin is not available
        except Exception:
            status = health_check.FAIL
        final_checks = {f'{type(self).__name__}:connection': checks}
        return health_check.HealthCheck(status=status, checks=final_checks)

    @timer_with_counter
    def get_table(self, *, table_uri: str) -> Table:
        """
        :param table_uri: Table URI
        :return:  A Table object
        """

        cols, last_neo4j_record = self._exec_col_query(table_uri)

        readers = self._exec_usage_query(table_uri)

        wmk_results, table_writer, timestamp_value, owners, tags, source, badges, prog_descs = \
            self._exec_table_query(table_uri)

        joins, filters = self._exec_table_query_query(table_uri)

        table = Table(database=last_neo4j_record['db']['name'],
                      cluster=last_neo4j_record['clstr']['name'],
                      schema=last_neo4j_record['schema']['name'],
                      name=last_neo4j_record['tbl']['name'],
                      tags=tags,
                      badges=badges,
                      description=self._safe_get(last_neo4j_record, 'tbl_dscrpt', 'description'),
                      columns=cols,
                      owners=owners,
                      table_readers=readers,
                      watermarks=wmk_results,
                      table_writer=table_writer,
                      last_updated_timestamp=timestamp_value,
                      source=source,
                      is_view=self._safe_get(last_neo4j_record, 'tbl', 'is_view'),
                      programmatic_descriptions=prog_descs,
                      common_joins=joins,
                      common_filters=filters
                      )

        return table

    @timer_with_counter
    def _exec_col_query(self, table_uri: str) -> Tuple:
        # Return Value: (Columns, Last Processed Record)

        column_level_query = textwrap.dedent("""
        MATCH (db:Database)-[:CLUSTER]->(clstr:Cluster)-[:SCHEMA]->(schema:Schema)
        -[:TABLE]->(tbl:Table {key: $tbl_key})-[:COLUMN]->(col:Column)
        OPTIONAL MATCH (tbl)-[:DESCRIPTION]->(tbl_dscrpt:Description)
        OPTIONAL MATCH (col:Column)-[:DESCRIPTION]->(col_dscrpt:Description)
        OPTIONAL MATCH (col:Column)-[:STAT]->(stat:Stat)
        OPTIONAL MATCH (col:Column)-[:HAS_BADGE]->(badge:Badge)
        RETURN db, clstr, schema, tbl, tbl_dscrpt, col, col_dscrpt, collect(distinct stat) as col_stats,
        collect(distinct badge) as col_badges
        ORDER BY col.sort_order;""")

        tbl_col_neo4j_records = self._execute_cypher_query(
            statement=column_level_query, param_dict={'tbl_key': table_uri})
        cols = []
        last_neo4j_record = None
        for tbl_col_neo4j_record in tbl_col_neo4j_records:
            # Getting last record from this for loop as Neo4j's result's random access is O(n) operation.
            col_stats = []
            for stat in tbl_col_neo4j_record['col_stats']:
                col_stat = Stat(
                    stat_type=stat['stat_type'],
                    stat_val=stat['stat_val'],
                    start_epoch=int(float(stat['start_epoch'])),
                    end_epoch=int(float(stat['end_epoch']))
                )
                col_stats.append(col_stat)

            column_badges = self._make_badges(tbl_col_neo4j_record['col_badges'])

            last_neo4j_record = tbl_col_neo4j_record
            col = Column(name=tbl_col_neo4j_record['col']['name'],
                         description=self._safe_get(tbl_col_neo4j_record, 'col_dscrpt', 'description'),
                         col_type=tbl_col_neo4j_record['col']['col_type'],
                         sort_order=int(tbl_col_neo4j_record['col']['sort_order']),
                         stats=col_stats,
                         badges=column_badges)

            cols.append(col)

        if not cols:
            raise NotFoundException('Table URI( {table_uri} ) does not exist'.format(table_uri=table_uri))

        return sorted(cols, key=lambda item: item.sort_order), last_neo4j_record

    @timer_with_counter
    def _exec_usage_query(self, table_uri: str) -> List[Reader]:
        # Return Value: List[Reader]

        usage_query = textwrap.dedent("""\
        MATCH (user:User)-[read:READ]->(table:Table {key: $tbl_key})
        RETURN user.email as email, read.read_count as read_count, table.name as table_name
        ORDER BY read.read_count DESC LIMIT 5;
        """)

        usage_neo4j_records = self._execute_cypher_query(statement=usage_query,
                                                         param_dict={'tbl_key': table_uri})
        readers = []  # type: List[Reader]
        for usage_neo4j_record in usage_neo4j_records:
            reader_data = self._get_user_details(user_id=usage_neo4j_record['email'])
            reader = Reader(user=self._build_user_from_record(record=reader_data),
                            read_count=usage_neo4j_record['read_count'])
            readers.append(reader)

        return readers

    @timer_with_counter
    def _exec_table_query(self, table_uri: str) -> Tuple:
        """
        Queries one Cypher record with watermark list, Application,
        ,timestamp, owner records and tag records.
        """

        # Return Value: (Watermark Results, Table Writer, Last Updated Timestamp, owner records, tag records)

        table_level_query = textwrap.dedent("""\
        MATCH (tbl:Table {key: $tbl_key})
        OPTIONAL MATCH (wmk:Watermark)-[:BELONG_TO_TABLE]->(tbl)
        OPTIONAL MATCH (application:Application)-[:GENERATES]->(tbl)
        OPTIONAL MATCH (tbl)-[:LAST_UPDATED_AT]->(t:Timestamp)
        OPTIONAL MATCH (owner:User)<-[:OWNER]-(tbl)
        OPTIONAL MATCH (tbl)-[:TAGGED_BY]->(tag:Tag{tag_type: $tag_normal_type})
        OPTIONAL MATCH (tbl)-[:HAS_BADGE]->(badge:Badge)
        OPTIONAL MATCH (tbl)-[:SOURCE]->(src:Source)
        OPTIONAL MATCH (tbl)-[:DESCRIPTION]->(prog_descriptions:Programmatic_Description)
        RETURN collect(distinct wmk) as wmk_records,
        application,
        t.last_updated_timestamp as last_updated_timestamp,
        collect(distinct owner) as owner_records,
        collect(distinct tag) as tag_records,
        collect(distinct badge) as badge_records,
        src,
        collect(distinct prog_descriptions) as prog_descriptions
        """)

        table_records = self._execute_cypher_query(statement=table_level_query,
                                                   param_dict={'tbl_key': table_uri,
                                                               'tag_normal_type': 'default'})

        table_records = table_records.single()

        wmk_results = []
        table_writer = None

        wmk_records = table_records['wmk_records']

        for record in wmk_records:
            if record['key'] is not None:
                watermark_type = record['key'].split('/')[-2]
                wmk_result = Watermark(watermark_type=watermark_type,
                                       partition_key=record['partition_key'],
                                       partition_value=record['partition_value'],
                                       create_time=record['create_time'])
                wmk_results.append(wmk_result)

        tags = []
        if table_records.get('tag_records'):
            tag_records = table_records['tag_records']
            for record in tag_records:
                tag_result = Tag(tag_name=record['key'],
                                 tag_type=record['tag_type'])
                tags.append(tag_result)

        # this is for any badges added with BadgeAPI instead of TagAPI
        badges = self._make_badges(table_records.get('badge_records'))

        application_record = table_records['application']
        if application_record is not None:
            table_writer = Application(
                application_url=application_record['application_url'],
                description=application_record['description'],
                name=application_record['name'],
                id=application_record.get('id', '')
            )

        timestamp_value = table_records['last_updated_timestamp']

        owner_record = []

        for owner in table_records.get('owner_records', []):
            owner_data = self._get_user_details(user_id=owner['email'])
            owner_record.append(self._build_user_from_record(record=owner_data))

        src = None

        if table_records['src']:
            src = Source(source_type=table_records['src']['source_type'],
                         source=table_records['src']['source'])

        prog_descriptions = self._extract_programmatic_descriptions_from_query(
            table_records.get('prog_descriptions', [])
        )

        return wmk_results, table_writer, timestamp_value, owner_record, tags, src, badges, prog_descriptions

    @timer_with_counter
    def _exec_table_query_query(self, table_uri: str) -> Tuple:
        """
        Queries one Cypher record with results that contain information about queries
        and entities (e.g. joins, where clauses, etc.) associated to queries that are executed
        on the table.
        """

        # Return Value: (Watermark Results, Table Writer, Last Updated Timestamp, owner records, tag records)
        table_query_level_query = textwrap.dedent("""
        MATCH (tbl:Table {key: $tbl_key})
        OPTIONAL MATCH (tbl)-[:COLUMN]->(col:Column)-[COLUMN_JOINS_WITH]->(j:Join)
        OPTIONAL MATCH (j)-[JOIN_OF_COLUMN]->(col2:Column)
        OPTIONAL MATCH (j)-[JOIN_OF_QUERY]->(jq:Query)-[:HAS_EXECUTION]->(exec:Execution)
        WITH tbl, j, col, col2,
            sum(coalesce(exec.execution_count, 0)) as join_exec_cnt
        ORDER BY join_exec_cnt desc
        LIMIT 5
        WITH tbl,
            COLLECT(DISTINCT {
            join: {
                joined_on_table: {
                    database: case when j.left_table_key = $tbl_key
                              then j.right_database
                              else j.left_database
                              end,
                    cluster: case when j.left_table_key = $tbl_key
                             then j.right_cluster
                             else j.left_cluster
                             end,
                    schema: case when j.left_table_key = $tbl_key
                            then j.right_schema
                            else j.left_schema
                            end,
                    name: case when j.left_table_key = $tbl_key
                          then j.right_table
                          else j.left_table
                          end
                },
                joined_on_column: col2.name,
                column: col.name,
                join_type: j.join_type,
                join_sql: j.join_sql
            },
            join_exec_cnt: join_exec_cnt
        }) as joins
        WITH tbl, joins
        OPTIONAL MATCH (tbl)-[:COLUMN]->(col:Column)-[USES_WHERE_CLAUSE]->(whr:Where)
        OPTIONAL MATCH (whr)-[WHERE_CLAUSE_OF]->(wq:Query)-[:HAS_EXECUTION]->(whrexec:Execution)
        WITH tbl, joins,
            whr, sum(coalesce(whrexec.execution_count, 0)) as where_exec_cnt
        ORDER BY where_exec_cnt desc
        LIMIT 5
        RETURN tbl, joins,
          COLLECT(DISTINCT {
            where_clause: whr.where_clause,
            where_exec_cnt: where_exec_cnt
          }) as filters
        """)

        query_records = self._execute_cypher_query(statement=table_query_level_query, param_dict={'tbl_key': table_uri})

        table_query_records = query_records.single()

        joins = self._extract_joins_from_query(table_query_records.get('joins', [{}]))
        filters = self._extract_filters_from_query(table_query_records.get('filters', [{}]))

        return joins, filters

    def _extract_programmatic_descriptions_from_query(self, raw_prog_descriptions: dict) -> list:
        prog_descriptions = []
        for prog_description in raw_prog_descriptions:
            source = prog_description['description_source']
            if source is None:
                LOGGER.error("A programmatic description with no source was found... skipping.")
            else:
                prog_descriptions.append(ProgrammaticDescription(source=source, text=prog_description['description']))
        prog_descriptions.sort(key=lambda x: x.source)
        return prog_descriptions

    def _extract_joins_from_query(self, joins: List[Dict]) -> List[Dict]:
        valid_joins = []
        for join in joins:
            join_data = join['join']
            if all(join_data.values()):
                new_sql_join = SqlJoin(join_sql=join_data['join_sql'],
                                       join_type=join_data['join_type'],
                                       joined_on_column=join_data['joined_on_column'],
                                       joined_on_table=TableSummary(**join_data['joined_on_table']),
                                       column=join_data['column'])
                valid_joins.append(new_sql_join)
        return valid_joins

    def _extract_filters_from_query(self, filters: List[Dict]) -> List[Dict]:
        return_filters = []
        for filt in filters:
            filter_where = filt.get('where_clause')
            if filter_where:
                return_filters.append(SqlWhere(where_clause=filter_where))
        return return_filters

    @no_type_check
    def _safe_get(self, dct, *keys):
        """
        Helper method for getting value from nested dict. This also works either key does not exist or value is None.
        :param dct:
        :param keys:
        :return:
        """
        for key in keys:
            dct = dct.get(key)
            if dct is None:
                return None
        return dct

    @timer_with_counter
    def _execute_cypher_query(self, *,
                              statement: str,
                              param_dict: Dict[str, Any]) -> BoltStatementResult:
        if LOGGER.isEnabledFor(logging.DEBUG):
            LOGGER.debug('Executing Cypher query: {statement} with params {params}: '.format(statement=statement,
                                                                                             params=param_dict))
        start = time.time()
        try:
            with self._driver.session() as session:
                return session.run(statement, **param_dict)

        finally:
            # TODO: Add support on statsd
            if LOGGER.isEnabledFor(logging.DEBUG):
                LOGGER.debug('Cypher query execution elapsed for {} seconds'.format(time.time() - start))

    # noinspection PyMethodMayBeStatic
    def _make_badges(self, badges: Iterable) -> List[Badge]:
        """
        Generates a list of Badges objects

        :param badges: A list of badges of a table or a column
        :return: a list of Badge objects
        """
        _badges = []
        for badge in badges:
            _badges.append(Badge(badge_name=badge["key"], category=badge["category"]))
        return _badges

    @timer_with_counter
    def get_resource_description(self, *,
                                 resource_type: ResourceType,
                                 uri: str) -> Description:
        """
        Get the resource description based on the uri. Any exception will propagate back to api server.

        :param resource_type:
        :param id:
        :return:
        """

        description_query = textwrap.dedent("""
        MATCH (n:{node_label} {{key: $key}})-[:DESCRIPTION]->(d:Description)
        RETURN d.description AS description;
        """.format(node_label=resource_type.name))

        result = self._execute_cypher_query(statement=description_query,
                                            param_dict={'key': uri})

        result = result.single()
        return Description(description=result['description'] if result else None)

    @timer_with_counter
    def get_table_description(self, *,
                              table_uri: str) -> Union[str, None]:
        """
        Get the table description based on table uri. Any exception will propagate back to api server.

        :param table_uri:
        :return:
        """

        return self.get_resource_description(resource_type=ResourceType.Table, uri=table_uri).description

    @timer_with_counter
    def put_resource_description(self, *,
                                 resource_type: ResourceType,
                                 uri: str,
                                 description: str) -> None:
        """
        Update resource description with one from user
        :param uri: Resource uri (key in Neo4j)
        :param description: new value for resource description
        """
        # start neo4j transaction
        desc_key = uri + '/_description'

        upsert_desc_query = textwrap.dedent("""
        MERGE (u:Description {key: $desc_key})
        on CREATE SET u={description: $description, key: $desc_key}
        on MATCH SET u={description: $description, key: $desc_key}
        """)

        upsert_desc_tab_relation_query = textwrap.dedent("""
        MATCH (n1:Description {{key: $desc_key}}), (n2:{node_label} {{key: $key}})
        MERGE (n2)-[r2:DESCRIPTION]->(n1)
        RETURN n1.key, n2.key
        """.format(node_label=resource_type.name))

        start = time.time()

        try:
            tx = self._driver.session().begin_transaction()

            tx.run(upsert_desc_query, {'description': description,
                                       'desc_key': desc_key})

            result = tx.run(upsert_desc_tab_relation_query, {'desc_key': desc_key,
                                                             'key': uri})

            if not result.single():
                raise NotFoundException(f'Failed to update the description as resource {uri} does not exist')

            # end neo4j transaction
            tx.commit()

        except Exception as e:
            LOGGER.exception('Failed to execute update process')
            if not tx.closed():
                tx.rollback()

            # propagate exception back to api
            raise e

        finally:
            if LOGGER.isEnabledFor(logging.DEBUG):
                LOGGER.debug('Update process elapsed for {} seconds'.format(time.time() - start))

    @timer_with_counter
    def put_table_description(self, *,
                              table_uri: str,
                              description: str) -> None:
        """
        Update table description with one from user
        :param table_uri: Table uri (key in Neo4j)
        :param description: new value for table description
        """

        self.put_resource_description(resource_type=ResourceType.Table,
                                      uri=table_uri,
                                      description=description)

    @timer_with_counter
    def get_column_description(self, *,
                               table_uri: str,
                               column_name: str) -> Union[str, None]:
        """
        Get the column description based on table uri. Any exception will propagate back to api server.

        :param table_uri:
        :param column_name:
        :return:
        """
        column_description_query = textwrap.dedent("""
        MATCH (tbl:Table {key: $tbl_key})-[:COLUMN]->(c:Column {name: $column_name})-[:DESCRIPTION]->(d:Description)
        RETURN d.description AS description;
        """)

        result = self._execute_cypher_query(statement=column_description_query,
                                            param_dict={'tbl_key': table_uri, 'column_name': column_name})

        column_descrpt = result.single()

        column_description = column_descrpt['description'] if column_descrpt else None

        return column_description

    @timer_with_counter
    def put_column_description(self, *,
                               table_uri: str,
                               column_name: str,
                               description: str) -> None:
        """
        Update column description with input from user
        :param table_uri:
        :param column_name:
        :param description:
        :return:
        """

        column_uri = table_uri + '/' + column_name  # type: str
        desc_key = column_uri + '/_description'

        upsert_desc_query = textwrap.dedent("""
            MERGE (u:Description {key: $desc_key})
            on CREATE SET u={description: $description, key: $desc_key}
            on MATCH SET u={description: $description, key: $desc_key}
            """)

        upsert_desc_col_relation_query = textwrap.dedent("""
            MATCH (n1:Description {key: $desc_key}), (n2:Column {key: $column_key})
            MERGE (n2)-[r2:DESCRIPTION]->(n1)
            RETURN n1.key, n2.key
            """)

        start = time.time()

        try:
            tx = self._driver.session().begin_transaction()

            tx.run(upsert_desc_query, {'description': description,
                                       'desc_key': desc_key})

            result = tx.run(upsert_desc_col_relation_query, {'desc_key': desc_key,
                                                             'column_key': column_uri})

            if not result.single():
                raise NotFoundException(f'Failed to update the table {table_uri} column '
                                        f'{column_uri} description as either table or column does not exist')

            # end neo4j transaction
            tx.commit()

        except Exception as e:

            LOGGER.exception('Failed to execute update process')

            if not tx.closed():
                tx.rollback()

            # propagate error to api
            raise e

        finally:
            if LOGGER.isEnabledFor(logging.DEBUG):
                LOGGER.debug('Update process elapsed for {} seconds'.format(time.time() - start))

    @timer_with_counter
    def add_owner(self, *,
                  table_uri: str,
                  owner: str) -> None:
        """
        Update table owner informations.
        1. Do a create if not exists query of the owner(user) node.
        2. Do a upsert of the owner/owned_by relation.
        :param table_uri:
        :param owner:
        :return:
        """

        self.add_resource_owner(uri=table_uri,
                                resource_type=ResourceType.Table,
                                owner=owner)

    @timer_with_counter
    def add_resource_owner(self, *,
                           uri: str,
                           resource_type: ResourceType,
                           owner: str) -> None:
        """
        Update table owner informations.
        1. Do a create if not exists query of the owner(user) node.
        2. Do a upsert of the owner/owned_by relation.

        :param table_uri:
        :param owner:
        :return:
        """
        create_owner_query = textwrap.dedent("""
        MERGE (u:User {key: $user_email})
        on CREATE SET u={email: $user_email, key: $user_email}
        """)

        upsert_owner_relation_query = textwrap.dedent("""
        MATCH (n1:User {{key: $user_email}}), (n2:{resource_type} {{key: $res_key}})
        MERGE (n1)-[r1:OWNER_OF]->(n2)-[r2:OWNER]->(n1)
        RETURN n1.key, n2.key
        """.format(resource_type=resource_type.name))

        try:
            tx = self._driver.session().begin_transaction()
            # upsert the node
            tx.run(create_owner_query, {'user_email': owner})
            result = tx.run(upsert_owner_relation_query, {'user_email': owner,
                                                          'res_key': uri})

            if not result.single():
                raise RuntimeError('Failed to create relation between '
                                   'owner {owner} and resource {uri}'.format(owner=owner,
                                                                             uri=uri))
            tx.commit()
        except Exception as e:
            if not tx.closed():
                tx.rollback()
            # propagate the exception back to api
            raise e

    @timer_with_counter
    def delete_owner(self, *,
                     table_uri: str,
                     owner: str) -> None:
        """
        Delete the owner / owned_by relationship.
        :param table_uri:
        :param owner:
        :return:
        """
        self.delete_resource_owner(uri=table_uri,
                                   resource_type=ResourceType.Table,
                                   owner=owner)

    @timer_with_counter
    def delete_resource_owner(self, *,
                              uri: str,
                              resource_type: ResourceType,
                              owner: str) -> None:
        """
        Delete the owner / owned_by relationship.
        :param table_uri:
        :param owner:
        :return:
        """
        delete_query = textwrap.dedent("""
        MATCH (n1:User{{key: $user_email}}), (n2:{resource_type} {{key: $res_key}})
        OPTIONAL MATCH (n1)-[r1:OWNER_OF]->(n2)
        OPTIONAL MATCH (n2)-[r2:OWNER]->(n1)
        DELETE r1,r2
        """.format(resource_type=resource_type.name))
        try:
            tx = self._driver.session().begin_transaction()
            tx.run(delete_query, {'user_email': owner,
                                  'res_key': uri})
        except Exception as e:
            # propagate the exception back to api
            if not tx.closed():
                tx.rollback()
            raise e
        finally:
            tx.commit()

    @timer_with_counter
    def add_badge(self, *,
                  id: str,
                  badge_name: str,
                  category: str = '',
                  resource_type: ResourceType) -> None:

        LOGGER.info('New badge {} for id {} with category {} '
                    'and resource type {}'.format(badge_name, id, category, resource_type.name))

        validation_query = \
            'MATCH (n:{resource_type} {{key: $key}}) return n'.format(resource_type=resource_type.name)

        upsert_badge_query = textwrap.dedent("""
        MERGE (u:Badge {key: $badge_name})
        on CREATE SET u={key: $badge_name, category: $category}
        on MATCH SET u={key: $badge_name, category: $category}
        """)

        upsert_badge_relation_query = textwrap.dedent("""
        MATCH(n1:Badge {{key: $badge_name, category: $category}}),
        (n2:{resource_type} {{key: $key}})
        MERGE (n1)-[r1:BADGE_FOR]->(n2)-[r2:HAS_BADGE]->(n1)
        RETURN n1.key, n2.key
        """.format(resource_type=resource_type.name))

        try:
            tx = self._driver.session().begin_transaction()
            tbl_result = tx.run(validation_query, {'key': id})
            if not tbl_result.single():
                raise NotFoundException('id {} does not exist'.format(id))

            tx.run(upsert_badge_query, {'badge_name': badge_name,
                                        'category': category})

            result = tx.run(upsert_badge_relation_query, {'badge_name': badge_name,
                                                          'key': id,
                                                          'category': category})

            if not result.single():
                raise RuntimeError('failed to create relation between '
                                   'badge {badge} and resource {resource} of resource type '
                                   '{resource_type} MORE {q}'.format(badge=badge_name,
                                                                     resource=id,
                                                                     resource_type=resource_type,
                                                                     q=upsert_badge_relation_query))
            tx.commit()
        except Exception as e:
            if not tx.closed():
                tx.rollback()
            raise e

    @timer_with_counter
    def delete_badge(self, id: str,
                     badge_name: str,
                     category: str,
                     resource_type: ResourceType) -> None:

        # TODO for some reason when deleting it will say it was successful
        # even when the badge never existed to begin with
        LOGGER.info('Delete badge {} for id {} with category {}'.format(badge_name, id, category))

        # only deletes relationshop between badge and resource
        delete_query = textwrap.dedent("""
        MATCH (b:Badge {{key:$badge_name, category:$category}})-
        [r1:BADGE_FOR]->(n:{resource_type} {{key: $key}})-[r2:HAS_BADGE]->(b) DELETE r1,r2
        """.format(resource_type=resource_type.name))

        try:
            tx = self._driver.session().begin_transaction()
            tx.run(delete_query, {'badge_name': badge_name,
                                  'key': id,
                                  'category': category})
            tx.commit()
        except Exception as e:
            # propagate the exception back to api
            if not tx.closed():
                tx.rollback()
            raise e

    @timer_with_counter
    def get_badges(self) -> List:
        LOGGER.info('Get all badges')
        query = textwrap.dedent("""
        MATCH (b:Badge) RETURN b as badge
        """)
        records = self._execute_cypher_query(statement=query,
                                             param_dict={})
        results = []
        for record in records:
            results.append(Badge(badge_name=record['badge']['key'],
                                 category=record['badge']['category']))

        return results

    @timer_with_counter
    def add_tag(self, *,
                id: str,
                tag: str,
                tag_type: str = 'default',
                resource_type: ResourceType = ResourceType.Table) -> None:
        """
        Add new tag
        1. Create the node with type Tag if the node doesn't exist.
        2. Create the relation between tag and table if the relation doesn't exist.

        :param id:
        :param tag:
        :param tag_type:
        :param resource_type:
        :return: None
        """
        LOGGER.info('New tag {} for id {} with type {} and resource type {}'.format(tag, id, tag_type,
                                                                                    resource_type.name))

        validation_query = \
            'MATCH (n:{resource_type} {{key: $key}}) return n'.format(resource_type=resource_type.name)

        upsert_tag_query = textwrap.dedent("""
        MERGE (u:Tag {key: $tag})
        on CREATE SET u={tag_type: $tag_type, key: $tag}
        on MATCH SET u={tag_type: $tag_type, key: $tag}
        """)

        upsert_tag_relation_query = textwrap.dedent("""
        MATCH (n1:Tag {{key: $tag, tag_type: $tag_type}}), (n2:{resource_type} {{key: $key}})
        MERGE (n1)-[r1:TAG]->(n2)-[r2:TAGGED_BY]->(n1)
        RETURN n1.key, n2.key
        """.format(resource_type=resource_type.name))

        try:
            tx = self._driver.session().begin_transaction()
            tbl_result = tx.run(validation_query, {'key': id})
            if not tbl_result.single():
                raise NotFoundException('id {} does not exist'.format(id))

            # upsert the node
            tx.run(upsert_tag_query, {'tag': tag,
                                      'tag_type': tag_type})
            result = tx.run(upsert_tag_relation_query, {'tag': tag,
                                                        'key': id,
                                                        'tag_type': tag_type})
            if not result.single():
                raise RuntimeError('Failed to create relation between '
                                   'tag {tag} and resource {resource} of resource type: {resource_type}'
                                   .format(tag=tag,
                                           resource=id,
                                           resource_type=resource_type.name))
            tx.commit()
        except Exception as e:
            if not tx.closed():
                tx.rollback()
            # propagate the exception back to api
            raise e

    @timer_with_counter
    def delete_tag(self, *,
                   id: str,
                   tag: str,
                   tag_type: str = 'default',
                   resource_type: ResourceType = ResourceType.Table) -> None:
        """
        Deletes tag
        1. Delete the relation between resource and the tag
        2. todo(Tao): need to think about whether we should delete the tag if it is an orphan tag.

        :param id:
        :param tag:
        :param tag_type: {default-> normal tag, badge->non writable tag from UI}
        :param resource_type:
        :return:
        """

        LOGGER.info('Delete tag {} for id {} with type {} and resource type: {}'.format(tag, id,
                                                                                        tag_type, resource_type.name))
        delete_query = textwrap.dedent("""
        MATCH (n1:Tag{{key: $tag, tag_type: $tag_type}})-
        [r1:TAG]->(n2:{resource_type} {{key: $key}})-[r2:TAGGED_BY]->(n1) DELETE r1,r2
        """.format(resource_type=resource_type.name))

        try:
            tx = self._driver.session().begin_transaction()
            tx.run(delete_query, {'tag': tag,
                                  'key': id,
                                  'tag_type': tag_type})
            tx.commit()
        except Exception as e:
            # propagate the exception back to api
            if not tx.closed():
                tx.rollback()
            raise e

    @timer_with_counter
    def get_tags(self) -> List:
        """
        Get all existing tags from neo4j

        :return:
        """
        LOGGER.info('Get all the tags')
        # todo: Currently all the tags are default type, we could open it up if we want to include badge
        query = textwrap.dedent("""
        MATCH (t:Tag{tag_type: 'default'})
        OPTIONAL MATCH (resource)-[:TAGGED_BY]->(t)
        WITH t as tag_name, count(distinct resource.key) as tag_count
        WHERE tag_count > 0
        RETURN tag_name, tag_count
        """)

        records = self._execute_cypher_query(statement=query,
                                             param_dict={})
        results = []
        for record in records:
            results.append(TagDetail(tag_name=record['tag_name']['key'],
                                     tag_count=record['tag_count']))
        return results

    @timer_with_counter
    def get_latest_updated_ts(self) -> Optional[int]:
        """
        API method to fetch last updated / index timestamp for neo4j, es

        :return:
        """
        query = textwrap.dedent("""
        MATCH (n:Updatedtimestamp{key: 'amundsen_updated_timestamp'}) RETURN n as ts
        """)
        record = self._execute_cypher_query(statement=query,
                                            param_dict={})
        # None means we don't have record for neo4j, es last updated / index ts
        record = record.single()
        if record:
            return record.get('ts', {}).get('latest_timestamp', 0)
        else:
            return None

    @timer_with_counter
    def get_statistics(self) -> Dict[str, Any]:
        """
        API method to fetch statistics metrics for neo4j
        :return: dictionary of statistics
        """
        query = textwrap.dedent("""
        MATCH (table_node:Table) with count(table_node) as number_of_tables
        MATCH p=(item_node)-[r:DESCRIPTION]->(description_node)
        WHERE size(description_node.description)>2 and exists(item_node.is_view)
        with count(item_node) as number_of_documented_tables, number_of_tables
        MATCH p=(item_node)-[r:DESCRIPTION]->(description_node)
        WHERE  size(description_node.description)>2 and exists(item_node.sort_order)
        with count(item_node) as number_of_documented_cols, number_of_documented_tables, number_of_tables
        MATCH p=(table_node)-[r:OWNER]->(user_node) with count(distinct table_node) as number_of_tables_with_owners,
        count(distinct user_node) as number_of_owners, number_of_documented_cols,
        number_of_documented_tables, number_of_tables
        MATCH (item_node)-[:DESCRIPTION]->(description_node)
        WHERE  size(description_node.description)>2 and exists(item_node.is_view)
        MATCH  (item_node)-[:OWNER]->(user_node)
        with count(item_node) as number_of_documented_and_owned_tables,
        number_of_tables_with_owners, number_of_owners, number_of_documented_cols,
        number_of_documented_tables, number_of_tables
        Return number_of_tables, number_of_documented_tables, number_of_documented_cols,
        number_of_owners, number_of_tables_with_owners, number_of_documented_and_owned_tables
        """)
        LOGGER.info('Getting Neo4j Statistics')
        records = self._execute_cypher_query(statement=query,
                                             param_dict={})
        for record in records:
            neo4j_statistics = {'number_of_tables': record['number_of_tables'],
                                'number_of_documented_tables': record['number_of_documented_tables'],
                                'number_of_documented_cols': record['number_of_documented_cols'],
                                'number_of_owners': record['number_of_owners'],
                                'number_of_tables_with_owners': record['number_of_tables_with_owners'],
                                'number_of_documented_and_owned_tables': record['number_of_documented_and_owned_tables']
                                }
            return neo4j_statistics
        return {}

    @_CACHE.cache('_get_global_popular_resources_uris', expire=_GET_POPULAR_RESOURCES_CACHE_EXPIRY_SEC)
    def _get_global_popular_resources_uris(self, num_entries: int,
                                           resource_type: ResourceType = ResourceType.Table) -> List[str]:
        """
        Retrieve popular table uris. Will provide tables with top x popularity score.
        Popularity score = number of distinct readers * log(total number of reads)
        The result of this method will be cached based on the key (num_entries), and the cache will be expired based on
        _GET_POPULAR_TABLE_CACHE_EXPIRY_SEC

        For score computation, it uses logarithm on total number of reads so that score won't be affected by small
        number of users reading a lot of times.
        :return: Iterable of table uri
        """
        query = textwrap.dedent("""
        MATCH (resource:{resource_type})-[r:READ_BY]->(u:User)
        WITH resource.key as resource_key, count(distinct u) as readers, sum(r.read_count) as total_reads
        WHERE readers >= $num_readers
        RETURN resource_key, readers, total_reads, (readers * log(total_reads)) as score
        ORDER BY score DESC LIMIT $num_entries;
        """).format(resource_type=resource_type.name)
        LOGGER.info('Querying popular tables URIs')
        num_readers = current_app.config['POPULAR_RESOURCES_MINIMUM_READER_COUNT']
        records = self._execute_cypher_query(statement=query,
                                             param_dict={'num_readers': num_readers,
                                                         'num_entries': num_entries})

        return [record['resource_key'] for record in records]

    @timer_with_counter
    @_CACHE.cache('_get_personal_popular_tables_uris', _GET_POPULAR_RESOURCES_CACHE_EXPIRY_SEC)
    def _get_personal_popular_resources_uris(self, num_entries: int,
                                             user_id: str,
                                             resource_type: ResourceType = ResourceType.Table) -> List[str]:
        """
        Retrieve personalized popular resources uris. Will provide resources with top
        popularity score that have been read by a peer of the user_id provided.
        The popularity score is defined in the same way as `_get_global_popular_resources_uris`

        The result of this method will be cached based on the key (num_entries, user_id),
        and the cache will be expired based on _GET_POPULAR_TABLE_CACHE_EXPIRY_SEC

        :return: Iterable of table uri
        """
        statement = textwrap.dedent("""
        MATCH (:User {{key:$user_id}})<-[:READ_BY]-(:{resource_type})-[:READ_BY]->
             (coUser:User)<-[coRead:READ_BY]-(resource:{resource_type})
        WITH resource.key AS resource_key, count(DISTINCT coUser) AS co_readers,
             sum(coRead.read_count) AS total_co_reads
        WHERE co_readers >= $num_readers
        RETURN resource_key, (co_readers * log(total_co_reads)) AS score
        ORDER BY score DESC LIMIT $num_entries;
        """).format(resource_type=resource_type.name)
        LOGGER.info('Querying popular tables URIs')
        num_readers = current_app.config['POPULAR_RESOURCES_MINIMUM_READER_COUNT']
        records = self._execute_cypher_query(statement=statement,
                                             param_dict={'user_id': user_id,
                                                         'num_readers': num_readers,
                                                         'num_entries': num_entries})

        return [record['resource_key'] for record in records]

    @timer_with_counter
    def get_popular_tables(self, *,
                           num_entries: int,
                           user_id: Optional[str] = None) -> List[PopularTable]:
        """

        Retrieve popular tables. As popular table computation requires full scan of table and user relationship,
        it will utilize cached method _get_popular_tables_uris.

        :param num_entries:
        :return: Iterable of PopularTable
        """
        if user_id is None:
            # Get global popular table URIs
            table_uris = self._get_global_popular_resources_uris(num_entries)
        else:
            # Get personalized popular table URIs
            table_uris = self._get_personal_popular_resources_uris(num_entries, user_id)

        if not table_uris:
            return []

        query = textwrap.dedent("""
        MATCH (db:Database)-[:CLUSTER]->(clstr:Cluster)-[:SCHEMA]->(schema:Schema)-[:TABLE]->(tbl:Table)
        WHERE tbl.key IN $table_uris
        WITH db.name as database_name, clstr.name as cluster_name, schema.name as schema_name, tbl
        OPTIONAL MATCH (tbl)-[:DESCRIPTION]->(dscrpt:Description)
        RETURN database_name, cluster_name, schema_name, tbl.name as table_name,
        dscrpt.description as table_description;
        """)

        records = self._execute_cypher_query(statement=query,
                                             param_dict={'table_uris': table_uris})

        popular_tables = []
        for record in records:
            popular_table = PopularTable(database=record['database_name'],
                                         cluster=record['cluster_name'],
                                         schema=record['schema_name'],
                                         name=record['table_name'],
                                         description=self._safe_get(record, 'table_description'))
            popular_tables.append(popular_table)
        return popular_tables

    def _get_popular_tables(self, *, resource_uris: List[str]) -> List[TableSummary]:
        """

        """
        if not resource_uris:
            return []

        query = textwrap.dedent("""
        MATCH (db:Database)-[:CLUSTER]->(clstr:Cluster)-[:SCHEMA]->(schema:Schema)-[:TABLE]->(tbl:Table)
        WHERE tbl.key IN $table_uris
        WITH db.name as database_name, clstr.name as cluster_name, schema.name as schema_name, tbl
        OPTIONAL MATCH (tbl)-[:DESCRIPTION]->(dscrpt:Description)
        RETURN database_name, cluster_name, schema_name, tbl.name as table_name,
        dscrpt.description as table_description;
        """)
        records = self._execute_cypher_query(statement=query,
                                             param_dict={'table_uris': resource_uris})

        popular_tables = []
        for record in records:
            popular_table = TableSummary(database=record['database_name'],
                                         cluster=record['cluster_name'],
                                         schema=record['schema_name'],
                                         name=record['table_name'],
                                         description=self._safe_get(record, 'table_description'))
            popular_tables.append(popular_table)
        return popular_tables

    def _get_popular_dashboards(self, *, resource_uris: List[str]) -> List[DashboardSummary]:
        """

        """
        if not resource_uris:
            return []

        query = textwrap.dedent(f"""
        MATCH (d:Dashboard)-[:DASHBOARD_OF]->(dg:Dashboardgroup)-[:DASHBOARD_GROUP_OF]->(c:Cluster)
        WHERE d.key IN $dashboards_uris
        OPTIONAL MATCH (d)-[:DESCRIPTION]->(dscrpt:Description)
        OPTIONAL MATCH (d)-[:EXECUTED]->(last_exec:Execution)
        WHERE split(last_exec.key, '/')[5] = '_last_successful_execution'
        RETURN c.name as cluster_name, dg.name as dg_name, dg.dashboard_group_url as dg_url,
        d.key as uri, d.name as name, d.dashboard_url as url,
        split(d.key, '_')[0] as product,
        dscrpt.description as description, last_exec.timestamp as last_successful_run_timestamp""")

        records = self._execute_cypher_query(statement=query,
                                             param_dict={'dashboards_uris': resource_uris})

        popular_dashboards = []
        for record in records:
            popular_dashboards.append(DashboardSummary(
                uri=record['uri'],
                cluster=record['cluster_name'],
                group_name=record['dg_name'],
                group_url=record['dg_url'],
                product=record['product'],
                name=record['name'],
                url=record['url'],
                description=record['description'],
                last_successful_run_timestamp=record['last_successful_run_timestamp'],
            ))

        return popular_dashboards

    @timer_with_counter
    def get_popular_resources(self, *,
                              num_entries: int,
                              resource_types: List[str],
                              user_id: Optional[str] = None) -> Dict[str, List]:
        popular_resources: Dict[str, List] = dict()
        for resource in resource_types:
            resource_type = to_resource_type(label=resource)
            popular_resources[resource_type.name] = list()
            if user_id is None:
                # Get global popular Table/Dashboard URIs
                resource_uris = self._get_global_popular_resources_uris(num_entries,
                                                                        resource_type=resource_type)
            else:
                # Get personalized popular Table/Dashboard URIs
                resource_uris = self._get_personal_popular_resources_uris(num_entries,
                                                                          user_id,
                                                                          resource_type=resource_type)

            if resource_type == ResourceType.Table:
                popular_resources[resource_type.name] = self._get_popular_tables(
                    resource_uris=resource_uris
                )
            elif resource_type == ResourceType.Dashboard:
                popular_resources[resource_type.name] = self._get_popular_dashboards(
                    resource_uris=resource_uris
                )

        return popular_resources

    @timer_with_counter
    def get_user(self, *, id: str) -> Union[UserEntity, None]:
        """
        Retrieve user detail based on user_id(email).

        :param user_id: the email for the given user
        :return:
        """

        query = textwrap.dedent("""
        MATCH (user:User {key: $user_id})
        OPTIONAL MATCH (user)-[:MANAGE_BY]->(manager:User)
        RETURN user as user_record, manager as manager_record
        """)

        record = self._execute_cypher_query(statement=query,
                                            param_dict={'user_id': id})
        single_result = record.single()

        if not single_result:
            raise NotFoundException('User {user_id} '
                                    'not found in the graph'.format(user_id=id))

        record = single_result.get('user_record', {})
        manager_record = single_result.get('manager_record', {})
        if manager_record:
            manager_name = manager_record.get('full_name', '')
        else:
            manager_name = ''

        return self._build_user_from_record(record=record, manager_name=manager_name)

    def create_update_user(self, *, user: User) -> Tuple[User, bool]:
        """
        Create a user if it does not exist, otherwise update the user. Required
        fields for creating / updating a user are validated upstream to this when
        the User object is created.

        :param user:
        :return:
        """
        user_data = UserSchema().dump(user)
        user_props = self._create_props_body(user_data, 'usr')

        create_update_user_query = textwrap.dedent("""
        MERGE (usr:User {key: $user_id})
        on CREATE SET %s, usr.%s=timestamp()
        on MATCH SET %s
        RETURN usr, usr.%s = timestamp() as created
        """ % (user_props, CREATED_EPOCH_MS, user_props, CREATED_EPOCH_MS))

        try:
            tx = self._driver.session().begin_transaction()
            result = tx.run(create_update_user_query, user_data)

            user_result = result.single()
            if not user_result:
                raise RuntimeError('Failed to create user with data %s' % user_data)
            tx.commit()

            new_user = self._build_user_from_record(user_result['usr'])
            new_user_created = True if user_result['created'] is True else False

        except Exception as e:
            if not tx.closed():
                tx.rollback()
            # propagate the exception back to api
            raise e

        return new_user, new_user_created

    def _create_props_body(self,
                           record_dict: dict,
                           identifier: str) -> str:
        """
        Creates a Neo4j property body by converting a dictionary into a comma
        separated string of KEY = VALUE.
        """
        props = []
        for k, v in record_dict.items():
            if v:
                props.append(f'{identifier}.{k} = ${k}')

        props.append(f"{identifier}.{PUBLISHED_TAG_PROPERTY_NAME} = 'api_create_update_user'")
        props.append(f"{identifier}.{LAST_UPDATED_EPOCH_MS} = timestamp()")
        return ', '.join(props)

    def get_users(self) -> List[UserEntity]:
        statement = "MATCH (usr:User) WHERE usr.is_active = true RETURN collect(usr) as users"

        record = self._execute_cypher_query(statement=statement, param_dict={})
        result = record.single()
        if not result or not result.get('users'):
            raise NotFoundException('Error getting users')

        return [self._build_user_from_record(record=rec) for rec in result['users']]

    @staticmethod
    def _build_user_from_record(record: dict, manager_name: Optional[str] = None) -> UserEntity:
        """
        Builds user record from Cypher query result. Other than the one defined in amundsen_common.models.user.User,
        you could add more fields from User node into the User model by specifying keys in config.USER_OTHER_KEYS
        :param record:
        :param manager_name:
        :return:
        """
        other_key_values = {}
        if has_app_context() and current_app.config[config.USER_OTHER_KEYS]:
            for k in current_app.config[config.USER_OTHER_KEYS]:
                if k in record:
                    other_key_values[k] = record[k]

        return UserEntity(email=record['email'],
                          user_id=record.get('user_id', record['email']),
                          first_name=record.get('first_name'),
                          last_name=record.get('last_name'),
                          full_name=record.get('full_name'),
                          is_active=record.get('is_active', True),
                          github_username=record.get('github_username'),
                          team_name=record.get('team_name'),
                          slack_id=record.get('slack_id'),
                          employee_type=record.get('employee_type'),
                          role_name=record.get('role_name'),
                          manager_fullname=record.get('manager_fullname', manager_name),
                          other_key_values=other_key_values)

    @staticmethod
    def _get_user_resource_relationship_clause(relation_type: UserResourceRel, id: str = None,
                                               user_key: str = None,
                                               resource_type: ResourceType = ResourceType.Table) -> str:
        """
        Returns the relationship clause of a cypher query between users and tables
        The User node is 'usr', the table node is 'tbl', and the relationship is 'rel'
        e.g. (usr:User)-[rel:READ]->(tbl:Table), (usr)-[rel:READ]->(tbl)
        """
        resource_matcher: str = ''
        user_matcher: str = ''

        if id is not None:
            resource_matcher += ':{}'.format(resource_type.name)
            if id != '':
                resource_matcher += ' {key: $resource_key}'

        if user_key is not None:
            user_matcher += ':User'
            if user_key != '':
                user_matcher += ' {key: $user_key}'

        if relation_type == UserResourceRel.follow:
            relation = f'(resource{resource_matcher})-[r1:FOLLOWED_BY]->(usr{user_matcher})-[r2:FOLLOW]->' \
                       f'(resource{resource_matcher})'
        elif relation_type == UserResourceRel.own:
            relation = f'(resource{resource_matcher})-[r1:OWNER]->(usr{user_matcher})-[r2:OWNER_OF]->' \
                       f'(resource{resource_matcher})'
        elif relation_type == UserResourceRel.read:
            relation = f'(resource{resource_matcher})-[r1:READ_BY]->(usr{user_matcher})-[r2:READ]->' \
                       f'(resource{resource_matcher})'
        else:
            raise NotImplementedError(f'The relation type {relation_type} is not defined!')
        return relation

    @timer_with_counter
    def get_dashboard_by_user_relation(self, *, user_email: str, relation_type: UserResourceRel) \
            -> Dict[str, List[DashboardSummary]]:
        """
        Retrieve all follow the Dashboard per user based on the relation.

        :param user_email: the email of the user
        :param relation_type: the relation between the user and the resource
        :return:
        """
        rel_clause: str = self._get_user_resource_relationship_clause(relation_type=relation_type,
                                                                      id='',
                                                                      resource_type=ResourceType.Dashboard,
                                                                      user_key=user_email)

        # FYI, to extract last_successful_execution, it searches for its execution ID which is always
        # _last_successful_execution
        # https://github.com/amundsen-io/amundsendatabuilder/blob/master/databuilder/models/dashboard/dashboard_execution.py#L18
        # https://github.com/amundsen-io/amundsendatabuilder/blob/master/databuilder/models/dashboard/dashboard_execution.py#L24

        query = textwrap.dedent(f"""
        MATCH {rel_clause}<-[:DASHBOARD]-(dg:Dashboardgroup)<-[:DASHBOARD_GROUP]-(clstr:Cluster)
        OPTIONAL MATCH (resource)-[:DESCRIPTION]->(dscrpt:Description)
        OPTIONAL MATCH (resource)-[:EXECUTED]->(last_exec:Execution)
        WHERE split(last_exec.key, '/')[5] = '_last_successful_execution'
        RETURN clstr.name as cluster_name, dg.name as dg_name, dg.dashboard_group_url as dg_url,
        resource.key as uri, resource.name as name, resource.dashboard_url as url,
        split(resource.key, '_')[0] as product,
        dscrpt.description as description, last_exec.timestamp as last_successful_run_timestamp""")

        records = self._execute_cypher_query(statement=query, param_dict={'user_key': user_email})

        if not records:
            raise NotFoundException('User {user_id} does not {relation} on {resource_type} resources'.format(
                user_id=user_email,
                relation=relation_type,
                resource_type=ResourceType.Dashboard.name))

        results = []
        for record in records:
            results.append(DashboardSummary(
                uri=record['uri'],
                cluster=record['cluster_name'],
                group_name=record['dg_name'],
                group_url=record['dg_url'],
                product=record['product'],
                name=record['name'],
                url=record['url'],
                description=record['description'],
                last_successful_run_timestamp=record['last_successful_run_timestamp'],
            ))

        return {ResourceType.Dashboard.name.lower(): results}

    @timer_with_counter
    def get_table_by_user_relation(self, *, user_email: str, relation_type: UserResourceRel) \
            -> Dict[str, List[PopularTable]]:
        """
        Retrive all follow the Table per user based on the relation.

        :param user_email: the email of the user
        :param relation_type: the relation between the user and the resource
        :return:
        """
        rel_clause: str = self._get_user_resource_relationship_clause(relation_type=relation_type,
                                                                      id='',
                                                                      resource_type=ResourceType.Table,
                                                                      user_key=user_email)

        query = textwrap.dedent(f"""
            MATCH {rel_clause}<-[:TABLE]-(schema:Schema)<-[:SCHEMA]-(clstr:Cluster)<-[:CLUSTER]-(db:Database)
            WITH db, clstr, schema, resource
            OPTIONAL MATCH (resource)-[:DESCRIPTION]->(tbl_dscrpt:Description)
            RETURN db, clstr, schema, resource, tbl_dscrpt""")

        table_records = self._execute_cypher_query(statement=query, param_dict={'user_key': user_email})

        if not table_records:
            raise NotFoundException('User {user_id} does not {relation} any resources'.format(user_id=user_email,
                                                                                              relation=relation_type))
        results = []
        for record in table_records:
            results.append(PopularTable(
                database=record['db']['name'],
                cluster=record['clstr']['name'],
                schema=record['schema']['name'],
                name=record['resource']['name'],
                description=self._safe_get(record, 'tbl_dscrpt', 'description')))
        return {ResourceType.Table.name.lower(): results}

    @timer_with_counter
    def get_frequently_used_tables(self, *, user_email: str) -> Dict[str, Any]:
        """
        Retrieves all Table the resources per user on READ relation.

        :param user_email: the email of the user
        :return:
        """

        query = textwrap.dedent("""
        MATCH (user:User {key: $query_key})-[r:READ]->(tbl:Table)
        WHERE EXISTS(r.published_tag) AND r.published_tag IS NOT NULL
        WITH user, r, tbl ORDER BY r.published_tag DESC, r.read_count DESC LIMIT 50
        MATCH (tbl:Table)<-[:TABLE]-(schema:Schema)<-[:SCHEMA]-(clstr:Cluster)<-[:CLUSTER]-(db:Database)
        OPTIONAL MATCH (tbl)-[:DESCRIPTION]->(tbl_dscrpt:Description)
        RETURN db, clstr, schema, tbl, tbl_dscrpt
        """)

        table_records = self._execute_cypher_query(statement=query, param_dict={'query_key': user_email})

        if not table_records:
            raise NotFoundException('User {user_id} does not READ any resources'.format(user_id=user_email))
        results = []

        for record in table_records:
            results.append(PopularTable(
                database=record['db']['name'],
                cluster=record['clstr']['name'],
                schema=record['schema']['name'],
                name=record['tbl']['name'],
                description=self._safe_get(record, 'tbl_dscrpt', 'description')))
        return {'table': results}

    @timer_with_counter
    def add_resource_relation_by_user(self, *,
                                      id: str,
                                      user_id: str,
                                      relation_type: UserResourceRel,
                                      resource_type: ResourceType) -> None:
        """
        Update table user informations.
        1. Do a upsert of the user node.
        2. Do a upsert of the relation/reverse-relation edge.

        :param table_uri:
        :param user_id:
        :param relation_type:
        :return:
        """

        upsert_user_query = textwrap.dedent("""
        MERGE (u:User {key: $user_email})
        on CREATE SET u={email: $user_email, key: $user_email}
        """)

        rel_clause: str = self._get_user_resource_relationship_clause(relation_type=relation_type,
                                                                      resource_type=resource_type)

        upsert_user_relation_query = textwrap.dedent("""
        MATCH (usr:User {{key: $user_key}}), (resource:{resource_type} {{key: $resource_key}})
        MERGE {rel_clause}
        RETURN usr.key, resource.key
        """.format(resource_type=resource_type.name,
                   rel_clause=rel_clause))

        try:
            tx = self._driver.session().begin_transaction()
            # upsert the node
            tx.run(upsert_user_query, {'user_email': user_id})
            result = tx.run(upsert_user_relation_query, {'user_key': user_id, 'resource_key': id})

            if not result.single():
                raise RuntimeError('Failed to create relation between '
                                   'user {user} and resource {id}'.format(user=user_id,
                                                                          id=id))
            tx.commit()
        except Exception as e:
            if not tx.closed():
                tx.rollback()
            # propagate the exception back to api
            raise e

    @timer_with_counter
    def delete_resource_relation_by_user(self, *,
                                         id: str,
                                         user_id: str,
                                         relation_type: UserResourceRel,
                                         resource_type: ResourceType) -> None:
        """
        Delete the relationship between user and resources.

        :param table_uri:
        :param user_id:
        :param relation_type:
        :return:
        """
        rel_clause: str = self._get_user_resource_relationship_clause(relation_type=relation_type,
                                                                      resource_type=resource_type,
                                                                      user_key=user_id,
                                                                      id=id
                                                                      )

        delete_query = textwrap.dedent("""
                MATCH {rel_clause}
                DELETE r1, r2
                """.format(rel_clause=rel_clause))

        try:
            tx = self._driver.session().begin_transaction()
            tx.run(delete_query, {'user_key': user_id, 'resource_key': id})
            tx.commit()
        except Exception as e:
            # propagate the exception back to api
            if not tx.closed():
                tx.rollback()
            raise e

    @timer_with_counter
    def get_dashboard(self,
                      id: str,
                      ) -> DashboardDetailEntity:

        get_dashboard_detail_query = textwrap.dedent(u"""
        MATCH (d:Dashboard {key: $query_key})-[:DASHBOARD_OF]->(dg:Dashboardgroup)-[:DASHBOARD_GROUP_OF]->(c:Cluster)
        OPTIONAL MATCH (d)-[:DESCRIPTION]->(description:Description)
        OPTIONAL MATCH (d)-[:EXECUTED]->(last_exec:Execution) WHERE split(last_exec.key, '/')[5] = '_last_execution'
        OPTIONAL MATCH (d)-[:EXECUTED]->(last_success_exec:Execution)
        WHERE split(last_success_exec.key, '/')[5] = '_last_successful_execution'
        OPTIONAL MATCH (d)-[:LAST_UPDATED_AT]->(t:Timestamp)
        OPTIONAL MATCH (d)-[:OWNER]->(owner:User)
        WITH c, dg, d, description, last_exec, last_success_exec, t, collect(owner) as owners
        OPTIONAL MATCH (d)-[:TAGGED_BY]->(tag:Tag{tag_type: $tag_normal_type})
        OPTIONAL MATCH (d)-[:HAS_BADGE]->(badge:Badge)
        WITH c, dg, d, description, last_exec, last_success_exec, t, owners, collect(tag) as tags,
        collect(badge) as badges
        OPTIONAL MATCH (d)-[read:READ_BY]->(:User)
        WITH c, dg, d, description, last_exec, last_success_exec, t, owners, tags, badges,
        sum(read.read_count) as recent_view_count
        OPTIONAL MATCH (d)-[:HAS_QUERY]->(query:Query)
        WITH c, dg, d, description, last_exec, last_success_exec, t, owners, tags, badges,
        recent_view_count, collect({name: query.name, url: query.url, query_text: query.query_text}) as queries
        OPTIONAL MATCH (d)-[:HAS_QUERY]->(query:Query)-[:HAS_CHART]->(chart:Chart)
        WITH c, dg, d, description, last_exec, last_success_exec, t, owners, tags, badges,
        recent_view_count, queries, collect(chart) as charts
        OPTIONAL MATCH (d)-[:DASHBOARD_WITH_TABLE]->(table:Table)<-[:TABLE]-(schema:Schema)
        <-[:SCHEMA]-(cluster:Cluster)<-[:CLUSTER]-(db:Database)
        OPTIONAL MATCH (table)-[:DESCRIPTION]->(table_description:Description)
        WITH c, dg, d, description, last_exec, last_success_exec, t, owners, tags, badges,
        recent_view_count, queries, charts,
        collect({name: table.name, schema: schema.name, cluster: cluster.name, database: db.name,
        description: table_description.description}) as tables
        RETURN
        c.name as cluster_name,
        d.key as uri,
        d.dashboard_url as url,
        d.name as name,
        split(d.key, '_')[0] as product,
        toInteger(d.created_timestamp) as created_timestamp,
        description.description as description,
        dg.name as group_name,
        dg.dashboard_group_url as group_url,
        toInteger(last_success_exec.timestamp) as last_successful_run_timestamp,
        toInteger(last_exec.timestamp) as last_run_timestamp,
        last_exec.state as last_run_state,
        toInteger(t.timestamp) as updated_timestamp,
        owners,
        tags,
        badges,
        recent_view_count,
        queries,
        charts,
        tables;
        """
                                                     )
        dashboard_record = self._execute_cypher_query(statement=get_dashboard_detail_query,
                                                      param_dict={'query_key': id,
                                                                  'tag_normal_type': 'default'}).single()

        if not dashboard_record:
            raise NotFoundException('No dashboard exist with URI: {}'.format(id))

        owners = []

        for owner in dashboard_record.get('owners', []):
            owner_data = self._get_user_details(user_id=owner['email'], user_data=owner)
            owners.append(self._build_user_from_record(record=owner_data))

        tags = [Tag(tag_type=tag['tag_type'], tag_name=tag['key']) for tag in dashboard_record['tags']]

        badges = self._make_badges(dashboard_record['badges'])

        chart_names = [chart['name'] for chart in dashboard_record['charts'] if 'name' in chart and chart['name']]
        # TODO Deprecate query_names in favor of queries after several releases from v2.5.0
        query_names = [query['name'] for query in dashboard_record['queries'] if 'name' in query and query['name']]
        queries = [DashboardQueryEntity(**query) for query in dashboard_record['queries']
                   if query.get('name') or query.get('url') or query.get('text')]
        tables = [PopularTable(**table) for table in dashboard_record['tables'] if 'name' in table and table['name']]

        return DashboardDetailEntity(uri=dashboard_record['uri'],
                                     cluster=dashboard_record['cluster_name'],
                                     url=dashboard_record['url'],
                                     name=dashboard_record['name'],
                                     product=dashboard_record['product'],
                                     created_timestamp=dashboard_record['created_timestamp'],
                                     description=self._safe_get(dashboard_record, 'description'),
                                     group_name=self._safe_get(dashboard_record, 'group_name'),
                                     group_url=self._safe_get(dashboard_record, 'group_url'),
                                     last_successful_run_timestamp=self._safe_get(dashboard_record,
                                                                                  'last_successful_run_timestamp'),
                                     last_run_timestamp=self._safe_get(dashboard_record, 'last_run_timestamp'),
                                     last_run_state=self._safe_get(dashboard_record, 'last_run_state'),
                                     updated_timestamp=self._safe_get(dashboard_record, 'updated_timestamp'),
                                     owners=owners,
                                     tags=tags,
                                     badges=badges,
                                     recent_view_count=dashboard_record['recent_view_count'],
                                     chart_names=chart_names,
                                     query_names=query_names,
                                     queries=queries,
                                     tables=tables
                                     )

    @timer_with_counter
    def get_dashboard_description(self, *,
                                  id: str) -> Description:
        """
        Get the dashboard description based on dashboard uri. Any exception will propagate back to api server.

        :param id:
        :return:
        """

        return self.get_resource_description(resource_type=ResourceType.Dashboard, uri=id)

    @timer_with_counter
    def put_dashboard_description(self, *,
                                  id: str,
                                  description: str) -> None:
        """
        Update Dashboard description
        :param id: Dashboard URI
        :param description: new value for Dashboard description
        """

        self.put_resource_description(resource_type=ResourceType.Dashboard,
                                      uri=id,
                                      description=description)

    @timer_with_counter
    def get_resources_using_table(self, *,
                                  id: str,
                                  resource_type: ResourceType) -> Dict[str, List[DashboardSummary]]:
        """

        :param id:
        :param resource_type:
        :return:
        """
        if resource_type != ResourceType.Dashboard:
            raise NotImplementedError('{} is not supported'.format(resource_type))

        get_dashboards_using_table_query = textwrap.dedent(u"""
        MATCH (d:Dashboard)-[:DASHBOARD_WITH_TABLE]->(table:Table {key: $query_key}),
        (d)-[:DASHBOARD_OF]->(dg:Dashboardgroup)-[:DASHBOARD_GROUP_OF]->(c:Cluster)
        OPTIONAL MATCH (d)-[:DESCRIPTION]->(description:Description)
        OPTIONAL MATCH (d)-[:EXECUTED]->(last_success_exec:Execution)
        WHERE split(last_success_exec.key, '/')[5] = '_last_successful_execution'
        OPTIONAL MATCH (d)-[read:READ_BY]->(:User)
        WITH c, dg, d, description, last_success_exec, sum(read.read_count) as recent_view_count
        RETURN
        d.key as uri,
        c.name as cluster,
        dg.name as group_name,
        dg.dashboard_group_url as group_url,
        d.name as name,
        d.dashboard_url as url,
        description.description as description,
        split(d.key, '_')[0] as product,
        toInteger(last_success_exec.timestamp) as last_successful_run_timestamp
        ORDER BY recent_view_count DESC;
        """)

        records = self._execute_cypher_query(statement=get_dashboards_using_table_query,
                                             param_dict={'query_key': id})

        results = []

        for record in records:
            results.append(DashboardSummary(**record))
        return {'dashboards': results}

    @timer_with_counter
    def get_lineage(self, *,
                    id: str, resource_type: ResourceType, direction: str, depth: int = 1) -> Lineage:
        """
        Retrieves the lineage information for the specified resource type.

        :param id: key of a table or a column
        :param resource_type: Type of the entity for which lineage is being retrieved
        :param direction: Whether to get the upstream/downstream or both directions
        :param depth: depth or level of lineage information
        :return: The Lineage object with upstream & downstream lineage items
        """

        get_both_lineage_query = textwrap.dedent(u"""
        MATCH (source:{resource} {{key: $query_key}})
        OPTIONAL MATCH dpath=(source)-[downstream_len:HAS_DOWNSTREAM*..{depth}]->(downstream_entity:{resource})
        OPTIONAL MATCH upath=(source)-[upstream_len:HAS_UPSTREAM*..{depth}]->(upstream_entity:{resource})
        WITH downstream_entity, upstream_entity, downstream_len, upstream_len, upath, dpath
        OPTIONAL MATCH (upstream_entity)-[:HAS_BADGE]->(upstream_badge:Badge)
        OPTIONAL MATCH (downstream_entity)-[:HAS_BADGE]->(downstream_badge:Badge)
        WITH CASE WHEN downstream_badge IS NULL THEN []
        ELSE collect(distinct {{key:downstream_badge.key,category:downstream_badge.category}})
        END AS downstream_badges, CASE WHEN upstream_badge IS NULL THEN []
        ELSE collect(distinct {{key:upstream_badge.key,category:upstream_badge.category}})
        END AS upstream_badges, upstream_entity, downstream_entity, upstream_len, downstream_len, upath, dpath
        OPTIONAL MATCH (downstream_entity:{resource})-[downstream_read:READ_BY]->(:User)
        WITH upstream_entity, downstream_entity, upstream_len, downstream_len, upath, dpath,
        downstream_badges, upstream_badges, sum(downstream_read.read_count) as downstream_read_count
        OPTIONAL MATCH (upstream_entity:{resource})-[upstream_read:READ_BY]->(:User)
        WITH upstream_entity, downstream_entity, upstream_len, downstream_len,
        downstream_badges, upstream_badges, downstream_read_count,
        sum(upstream_read.read_count) as upstream_read_count, upath, dpath
        WITH CASE WHEN upstream_len IS NULL THEN []
        ELSE COLLECT(distinct{{level:SIZE(upstream_len), source:split(upstream_entity.key,'://')[0],
        key:upstream_entity.key, badges:upstream_badges, usage:upstream_read_count, parent:nodes(upath)[-2].key}})
        END AS upstream_entities, CASE WHEN downstream_len IS NULL THEN []
        ELSE COLLECT(distinct{{level:SIZE(downstream_len), source:split(downstream_entity.key,'://')[0],
        key:downstream_entity.key, badges:downstream_badges, usage:downstream_read_count, parent:nodes(dpath)[-2].key}})
        END AS downstream_entities RETURN downstream_entities, upstream_entities
        """).format(depth=depth, resource=resource_type.name)

        get_upstream_lineage_query = textwrap.dedent(u"""
        MATCH (source:{resource} {{key: $query_key}})
        OPTIONAL MATCH path=(source)-[upstream_len:HAS_UPSTREAM*..{depth}]->(upstream_entity:{resource})
        WITH upstream_entity, upstream_len, path
        OPTIONAL MATCH (upstream_entity)-[:HAS_BADGE]->(upstream_badge:Badge)
        WITH CASE WHEN upstream_badge IS NULL THEN []
        ELSE collect(distinct {{key:upstream_badge.key,category:upstream_badge.category}})
        END AS upstream_badges, upstream_entity, upstream_len, path
        OPTIONAL MATCH (upstream_entity:{resource})-[upstream_read:READ_BY]->(:User)
        WITH upstream_entity, upstream_len, upstream_badges,
        sum(upstream_read.read_count) as upstream_read_count, path
        WITH CASE WHEN upstream_len IS NULL THEN []
        ELSE COLLECT(distinct{{level:SIZE(upstream_len), source:split(upstream_entity.key,'://')[0],
        key:upstream_entity.key, badges:upstream_badges, usage:upstream_read_count, parent:nodes(path)[-2].key}})
        END AS upstream_entities RETURN upstream_entities
        """).format(depth=depth, resource=resource_type.name)

        get_downstream_lineage_query = textwrap.dedent(u"""
        MATCH (source:{resource} {{key: $query_key}})
        OPTIONAL MATCH path=(source)-[downstream_len:HAS_DOWNSTREAM*..{depth}]->(downstream_entity:{resource})
        WITH downstream_entity, downstream_len, path
        OPTIONAL MATCH (downstream_entity)-[:HAS_BADGE]->(downstream_badge:Badge)
        WITH CASE WHEN downstream_badge IS NULL THEN []
        ELSE collect(distinct {{key:downstream_badge.key,category:downstream_badge.category}})
        END AS downstream_badges, downstream_entity, downstream_len, path
        OPTIONAL MATCH (downstream_entity:{resource})-[downstream_read:READ_BY]->(:User)
        WITH downstream_entity, downstream_len, downstream_badges,
        sum(downstream_read.read_count) as downstream_read_count, path
        WITH CASE WHEN downstream_len IS NULL THEN []
        ELSE COLLECT(distinct{{level:SIZE(downstream_len), source:split(downstream_entity.key,'://')[0],
        key:downstream_entity.key, badges:downstream_badges, usage:downstream_read_count, parent:nodes(path)[-2].key}})
        END AS downstream_entities RETURN downstream_entities
        """).format(depth=depth, resource=resource_type.name)

        if direction == 'upstream':
            lineage_query = get_upstream_lineage_query

        elif direction == 'downstream':
            lineage_query = get_downstream_lineage_query

        else:
            lineage_query = get_both_lineage_query

        records = self._execute_cypher_query(statement=lineage_query,
                                             param_dict={'query_key': id})
        result = records.single()

        downstream_tables = []
        upstream_tables = []

        for downstream in result.get("downstream_entities") or []:
            downstream_tables.append(LineageItem(**{"key": downstream["key"],
                                                    "source": downstream["source"],
                                                    "level": downstream["level"],
                                                    "badges": self._make_badges(downstream["badges"]),
                                                    "usage": downstream.get("usage", 0),
                                                    "parent": downstream.get("parent", '')
                                                    }))

        for upstream in result.get("upstream_entities") or []:
            upstream_tables.append(LineageItem(**{"key": upstream["key"],
                                                  "source": upstream["source"],
                                                  "level": upstream["level"],
                                                  "badges": self._make_badges(upstream["badges"]),
                                                  "usage": upstream.get("usage", 0),
                                                  "parent": upstream.get("parent", '')
                                                  }))

        # ToDo: Add a root_entity as an item, which will make it easier for lineage graph
        return Lineage(**{"key": id,
                          "upstream_entities": upstream_tables,
                          "downstream_entities": downstream_tables,
                          "direction": direction, "depth": depth})

    def _create_watermarks(self, wmk_records: List) -> List[Watermark]:
        watermarks = []
        for record in wmk_records:
            if record['key'] is not None:
                watermark_type = record['key'].split('/')[-2]
                watermarks.append(Watermark(watermark_type=watermark_type,
                                            partition_key=record['partition_key'],
                                            partition_value=record['partition_value'],
                                            create_time=record['create_time']))
        return watermarks

    def _create_feature_watermarks(self, wmk_records: List) -> List[Watermark]:
        watermarks = []
        for record in wmk_records:
            if record['key'] is not None:
                watermark_type = record['key'].split('/')[-1]

                watermarks.append(FeatureWatermark(key=record['key'],
                                                   watermark_type=watermark_type,
                                                   time=record['time']))
        return watermarks

    def _create_programmatic_descriptions(self, prog_desc_records: List) -> List[ProgrammaticDescription]:
        programmatic_descriptions = []
        for pg in prog_desc_records:
            source = pg['description_source']
            if source is None:
                LOGGER.error("A programmatic description with no source was found... skipping.")
            else:
                programmatic_descriptions.append(ProgrammaticDescription(source=source,
                                                                         text=pg['description']))
        return programmatic_descriptions

    def _create_owners(self, owner_records: List) -> List[User]:
        owners = []
        for owner in owner_records:
            owners.append(User(email=owner['email']))
        return owners

    @timer_with_counter
    def _exec_feature_query(self, *, feature_key: str) -> Dict:
        """
        Executes cypher query to get feature and related nodes
        """

        feature_query = textwrap.dedent("""\
        MATCH (feat:Feature {key: $feature_key})
        OPTIONAL MATCH (db:Database)-[:AVAILABLE_FEATURE]->(feat)
        OPTIONAL MATCH (fg:Feature_Group)-[:GROUPS]->(feat)
        OPTIONAL MATCH (feat)-[:OWNER]->(owner:User)
        OPTIONAL MATCH (feat)-[:TAGGED_BY]->(tag:Tag)
        OPTIONAL MATCH (feat)-[:HAS_BADGE]->(badge:Badge)
        OPTIONAL MATCH (feat)-[:DESCRIPTION]->(desc:Description)
        OPTIONAL MATCH (feat)-[:DESCRIPTION]->(prog_descriptions:Programmatic_Description)
        OPTIONAL MATCH (wmk:Feature_Watermark)-[:BELONG_TO_FEATURE]->(feat)
        RETURN feat, desc, fg,
        collect(distinct wmk) as wmk_records,
        collect(distinct db) as availability_records,
        collect(distinct owner) as owner_records,
        collect(distinct tag) as tag_records,
        collect(distinct badge) as badge_records,
        collect(distinct prog_descriptions) as prog_descriptions
        """)

        results = self._execute_cypher_query(statement=feature_query,
                                             param_dict={'feature_key': feature_key})

        if results is None:
            raise NotFoundException('Feature with key {} does not exist'.format(feature_key))

        feature_records = results.single()
        if feature_records is None:
            raise NotFoundException('Feature with key {} does not exist'.format(feature_key))

        watermarks = self._create_feature_watermarks(wmk_records=feature_records['wmk_records'])

        availability_records = [db['name'] for db in feature_records.get('availability_records')]

        description = None
        if feature_records.get('desc'):
            description = feature_records.get('desc')['description']

        programmatic_descriptions = self._create_programmatic_descriptions(feature_records['prog_descriptions'])

        owners = self._create_owners(feature_records['owner_records'])

        tags = []
        for record in feature_records.get('tag_records'):
            tag_result = Tag(tag_name=record['key'],
                             tag_type=record['tag_type'])
            tags.append(tag_result)

        feature_node = feature_records['feat']

        feature_group = feature_records['fg']

        return {
            'key': feature_node.get('key'),
            'name': feature_node.get('name'),
            'version': feature_node.get('version'),
            'feature_group': feature_group.get('name'),
            'data_type': feature_node.get('data_type'),
            'entity': feature_node.get('entity'),
            'description': description,
            'programmatic_descriptions': programmatic_descriptions,
            'last_updated_timestamp': feature_node.get('last_updated_timestamp'),
            'created_timestamp': feature_node.get('created_timestamp'),
            'watermarks': watermarks,
            'availability': availability_records,
            'tags': tags,
            'badges': self._make_badges(feature_records.get('badge_records')),
            'owners': owners,
            'status': feature_node.get('status')
        }

    def get_feature(self, *, feature_uri: str) -> Feature:
        """
        :param feature_uri: uniquely identifying key for a feature node
        :return: a Feature object
        """
        feature_metadata = self._exec_feature_query(feature_key=feature_uri)

        feature = Feature(
            key=feature_metadata['key'],
            name=feature_metadata['name'],
            version=feature_metadata['version'],
            status=feature_metadata['status'],
            feature_group=feature_metadata['feature_group'],
            entity=feature_metadata['entity'],
            data_type=feature_metadata['data_type'],
            availability=feature_metadata['availability'],
            description=feature_metadata['description'],
            owners=feature_metadata['owners'],
            badges=feature_metadata['badges'],
            tags=feature_metadata['tags'],
            programmatic_descriptions=feature_metadata['programmatic_descriptions'],
            last_updated_timestamp=feature_metadata['last_updated_timestamp'],
            created_timestamp=feature_metadata['created_timestamp'],
            watermarks=feature_metadata['watermarks'])
        return feature

    def get_resource_generation_code(self, *, uri: str, resource_type: ResourceType) -> GenerationCode:
        """
        Executes cypher query to get query nodes associated with resource
        """

        neo4j_query = textwrap.dedent("""\
        MATCH (feat:{resource_type} {{key: $resource_key}})
        OPTIONAL MATCH (q:Feature_Generation_Code)-[:GENERATION_CODE_OF]->(feat)
        RETURN q as query_records
        """.format(resource_type=resource_type.name))

        records = self._execute_cypher_query(statement=neo4j_query,
                                             param_dict={'resource_key': uri})
        if records is None:
            raise NotFoundException('Generation code for id {} does not exist'.format(id))

        query_result = records.single()['query_records']
        if query_result is None:
            raise NotFoundException('Generation code for id {} does not exist'.format(id))

        return GenerationCode(key=query_result['key'],
                              text=query_result['text'],
                              source=query_result['source'])
