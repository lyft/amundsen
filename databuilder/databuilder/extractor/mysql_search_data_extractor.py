# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import importlib
import logging
from typing import (
    Any, Callable, Dict, Iterator, List, Optional,
)

from amundsen_rds.models.badge import Badge
from amundsen_rds.models.cluster import Cluster
from amundsen_rds.models.column import ColumnDescription, TableColumn
from amundsen_rds.models.dashboard import (
    Dashboard, DashboardChart, DashboardCluster, DashboardDescription, DashboardExecution, DashboardFollower,
    DashboardGroup, DashboardGroupDescription, DashboardOwner, DashboardQuery, DashboardUsage,
)
from amundsen_rds.models.database import Database
from amundsen_rds.models.schema import Schema, SchemaDescription
from amundsen_rds.models.table import (
    Table, TableDescription, TableFollower, TableOwner, TableProgrammaticDescription, TableTimestamp, TableUsage,
)
from amundsen_rds.models.tag import Tag
from amundsen_rds.models.user import User
from pyhocon import ConfigTree
from sqlalchemy import create_engine, func
from sqlalchemy.orm import (
    Session, load_only, sessionmaker, subqueryload,
)

from databuilder.extractor.base_extractor import Extractor

LOGGER = logging.getLogger(__name__)


def _table_search_query(session: Session, table_filter: List, offset: int, limit: int) -> List:
    """
    Table query
    :param session:
    :param table_filter:
    :param offset:
    :param limit:
    :return:
    """
    # table
    query = session.query(Table).filter(*table_filter).options(
        load_only(Table.rk, Table.name, Table.schema_rk)
    )

    # description
    query = query.options(
        subqueryload(Table.description).options(
            load_only(TableDescription.description)
        )
    ).options(
        subqueryload(Table.programmatic_descriptions).options(
            load_only(TableProgrammaticDescription.description)
        )
    )

    # schema, cluster, database
    query = query.options(
        subqueryload(Table.schema).options(
            load_only(Schema.name, Schema.cluster_rk),
            subqueryload(Schema.description).options(
                load_only(SchemaDescription.description)
            ),
            subqueryload(Schema.cluster).options(
                load_only(Cluster.name, Cluster.database_rk),
                subqueryload(Cluster.database).options(
                    load_only(Database.name)
                )
            )
        )
    )

    # column
    query = query.options(
        subqueryload(Table.columns).options(
            load_only(TableColumn.rk, TableColumn.name),
            subqueryload(TableColumn.description).options(
                load_only(ColumnDescription.description)
            )
        )
    )

    # tag, badge
    query = query.options(
        subqueryload(Table.tags).options(
            load_only(Tag.rk, Tag.tag_type)
        )
    ).options(
        subqueryload(Table.badges).options(
            load_only(Badge.rk)
        )
    )

    # usage
    query = query.options(
        subqueryload(Table.usage).options(
            load_only(TableUsage.read_count)
        )
    )

    # timestamp
    query = query.options(
        subqueryload(Table.timestamp).options(
            load_only(TableTimestamp.last_updated_timestamp)
        )
    )

    query = query.order_by(Table.rk).offset(offset).limit(limit)

    return query.all()


def _table_search(session: Session, published_tag: str, limit: int) -> List[Dict]:
    """
    Query table metadata.
    :param session:
    :param published_tag:
    :param limit:
    :return:
    """
    LOGGER.info('Querying table metadata.')

    table_filter = []
    if published_tag:
        table_filter.append(Table.published_tag == published_tag)

    table_results = []

    offset = 0
    tables = _table_search_query(session, table_filter, offset, limit)
    while tables:
        for table in tables:
            schema = table.schema
            schema_description = schema.description.description if schema.description else None
            cluster = schema.cluster
            database = cluster.database
            description = table.description.description if table.description else ''
            programmatic_descriptions = [description.description
                                         for description in table.programmatic_descriptions]

            columns = table.columns
            column_names = [column.name for column in columns]
            column_descriptions = [column.description.description if column.description else ''
                                   for column in columns]

            total_usage = sum(usage.read_count for usage in table.usage)
            unique_usage = len(table.usage)

            tags = [tag.rk for tag in table.tags if tag.tag_type == 'default']
            badges = [badge.rk for badge in table.badges]
            last_updated_timestamp = table.timestamp.last_updated_timestamp if table.timestamp else None

            table_result = dict(database=database.name,
                                cluster=cluster.name,
                                schema=schema.name,
                                name=table.name,
                                key=table.rk,
                                description=description,
                                last_updated_timestamp=last_updated_timestamp,
                                column_names=column_names,
                                column_descriptions=column_descriptions,
                                total_usage=total_usage,
                                unique_usage=unique_usage,
                                tags=tags,
                                badges=badges,
                                schema_description=schema_description,
                                programmatic_descriptions=programmatic_descriptions)
            table_results.append(table_result)

        offset += limit
        tables = _table_search_query(session, table_filter, offset, limit)

    return table_results


def _dashboard_search_query(session: Session, dashboard_filter: List, offset: int, limit: int) -> List:
    """
    Dashboard query
    :param session:
    :param dashboard_filter:
    :param offset:
    :param limit:
    :return:
    """
    # dashboard
    query = session.query(Dashboard).filter(*dashboard_filter).options(
        load_only(Dashboard.rk,
                  Dashboard.name,
                  Dashboard.dashboard_url,
                  Dashboard.dashboard_group_rk)
    )

    # group, cluster
    query = query.options(
        subqueryload(Dashboard.group).options(
            load_only(DashboardGroup.rk,
                      DashboardGroup.name,
                      DashboardGroup.dashboard_group_url,
                      DashboardGroup.cluster_rk),
            subqueryload(DashboardGroup.description).options(
                load_only(DashboardGroupDescription.description)
            ),
            subqueryload(DashboardGroup.cluster).options(
                load_only(DashboardCluster.name)
            )
        )
    )

    # description
    query = query.options(
        subqueryload(Dashboard.description).options(
            load_only(DashboardDescription.description)
        )
    )

    # execution
    query = query.options(
        subqueryload(Dashboard.execution).options(
            load_only(DashboardExecution.rk, DashboardExecution.timestamp)
        )
    )

    # usage
    query = query.options(
        subqueryload(Dashboard.usage).options(
            load_only(DashboardUsage.read_count)
        )
    )

    # query, chart
    query = query.options(
        subqueryload(Dashboard.queries).options(
            load_only(DashboardQuery.name),
            subqueryload(DashboardQuery.charts).options(
                load_only(DashboardChart.name)
            )
        )
    )

    # tag, badge
    query = query.options(
        subqueryload(Dashboard.tags).options(
            load_only(Tag.rk, Tag.tag_type)
        )
    ).options(
        subqueryload(Dashboard.badges).options(
            load_only(Badge.rk)
        )
    )

    query = query.order_by(Dashboard.rk).offset(offset).limit(limit)

    return query.all()


def _dashboard_search(session: Session, published_tag: str, limit: int) -> List[Dict]:
    """
    Query dashboard metadata.
    :param session:
    :param published_tag:
    :param limit:
    :return:
    """
    LOGGER.info('Querying dashboard metadata.')

    dashboard_filter = []
    if published_tag:
        dashboard_filter.append(Dashboard.published_tag == published_tag)

    dashboard_results = []

    offset = 0
    dashboards = _dashboard_search_query(session, dashboard_filter, offset, limit)
    while dashboards:
        for dashboard in dashboards:
            group = dashboard.group
            description = dashboard.description.description if dashboard.description else None
            group_description = group.description.description if group.description else None
            cluster = group.cluster
            product = dashboard.rk.split('_')[0]
            last_exec = next((execution for execution in dashboard.execution
                              if execution.rk.endswith('_last_successful_execution')), None)
            last_successful_run_timestamp = last_exec.timestamp if last_exec else None
            total_usage = sum(usage.read_count for usage in dashboard.usage)

            queries = dashboard.queries
            query_names = [query.name for query in queries]
            chart_names = [chart.name for query in queries for chart in query.charts]

            tags = [tag.rk for tag in dashboard.tags if tag.tag_type == 'default']
            badges = [badge.rk for badge in dashboard.badges]

            dashboard_result = dict(group_name=group.name,
                                    name=dashboard.name,
                                    description=description,
                                    total_usage=total_usage,
                                    product=product,
                                    cluster=cluster.name,
                                    group_description=group_description,
                                    query_names=query_names,
                                    chart_names=chart_names,
                                    group_url=group.dashboard_group_url,
                                    url=dashboard.dashboard_url,
                                    uri=dashboard.rk,
                                    last_successful_run_timestamp=last_successful_run_timestamp,
                                    tags=tags,
                                    badges=badges)

            dashboard_results.append(dashboard_result)

        offset += limit
        dashboards = _dashboard_search_query(session, dashboard_filter, offset, limit)

    return dashboard_results


def _user_search_query(session: Session, user_filter: List, offset: int, limit: int) -> List:
    """
    User query
    :param session:
    :param user_filter:
    :param offset:
    :param limit:
    :return:
    """
    # read
    table_usage_subquery = session \
        .query(User.rk, func.sum(TableUsage.read_count).label('table_read_count')) \
        .outerjoin(TableUsage) \
        .filter(*user_filter) \
        .group_by(User.rk).order_by(User.rk).offset(offset).limit(limit).subquery()

    dashboard_usage_subquery = session \
        .query(User.rk, func.sum(DashboardUsage.read_count).label('dashboard_read_count')) \
        .outerjoin(DashboardUsage) \
        .filter(*user_filter) \
        .group_by(User.rk).order_by(User.rk).offset(offset).limit(limit).subquery()

    # own
    table_owner_subquery = session \
        .query(User.rk, func.count(TableOwner.table_rk).label('table_own_count')) \
        .outerjoin(TableOwner) \
        .filter(*user_filter) \
        .group_by(User.rk).order_by(User.rk).offset(offset).limit(limit).subquery()

    dashboard_owner_subquery = session \
        .query(User.rk, func.count(DashboardOwner.dashboard_rk).label('dashboard_own_count')) \
        .outerjoin(DashboardOwner) \
        .filter(*user_filter) \
        .group_by(User.rk).order_by(User.rk).offset(offset).limit(limit).subquery()

    # follow
    table_follower_subquery = session \
        .query(User.rk, func.count(TableFollower.table_rk).label('table_follow_count')) \
        .outerjoin(TableFollower) \
        .filter(*user_filter) \
        .group_by(User.rk).order_by(User.rk).offset(offset).limit(limit).subquery()

    dashboard_follower_subquery = session \
        .query(User.rk, func.count(DashboardFollower.dashboard_rk).label('dashboard_follow_count')) \
        .outerjoin(DashboardFollower) \
        .filter(*user_filter) \
        .group_by(User.rk).order_by(User.rk).offset(offset).limit(limit).subquery()

    # user
    query = session \
        .query(User,
               table_usage_subquery.c.table_read_count,
               dashboard_usage_subquery.c.dashboard_read_count,
               table_owner_subquery.c.table_own_count,
               dashboard_owner_subquery.c.dashboard_own_count,
               table_follower_subquery.c.table_follow_count,
               dashboard_follower_subquery.c.dashboard_follow_count) \
        .join(table_usage_subquery, table_usage_subquery.c.rk == User.rk) \
        .join(dashboard_usage_subquery, dashboard_usage_subquery.c.rk == User.rk) \
        .join(table_owner_subquery, table_owner_subquery.c.rk == User.rk) \
        .join(dashboard_owner_subquery, dashboard_owner_subquery.c.rk == User.rk) \
        .join(table_follower_subquery, table_follower_subquery.c.rk == User.rk) \
        .join(dashboard_follower_subquery, dashboard_follower_subquery.c.rk == User.rk)

    # manager
    query = query.options(
        subqueryload(User.manager).options(
            load_only(User.email)
        )
    )

    return query.all()


def _user_search(session: Session, published_tag: str, limit: int) -> List[Dict]:
    """
    Query user metadata.
    :param session:
    :param published_tag:
    :param limit:
    :return:
    """
    LOGGER.info('Querying user metadata.')

    user_filter = [User.full_name.isnot(None)]
    if published_tag:
        user_filter.append(User.published_tag == published_tag)

    user_results = []

    offset = 0
    query_results = _user_search_query(session, user_filter, offset, limit)
    while query_results:
        for query_result in query_results:
            user = query_result.User
            table_read_count = int(query_result.table_read_count) if query_result.table_read_count else 0
            dashboard_read_count = int(query_result.dashboard_read_count) if query_result.dashboard_read_count else 0
            total_read_count = table_read_count + dashboard_read_count

            table_own_count = query_result.table_own_count
            dashboard_own_count = query_result.dashboard_own_count
            total_own_count = table_own_count + dashboard_own_count

            table_follow_count = query_result.table_follow_count
            dashboard_follow_count = query_result.dashboard_follow_count
            total_follow_count = table_follow_count + dashboard_follow_count

            manager_email = user.manager.email if user.manager else ''
            user_result = dict(email=user.email,
                               first_name=user.first_name,
                               last_name=user.last_name,
                               full_name=user.full_name,
                               github_username=user.github_username,
                               team_name=user.team_name,
                               employee_type=user.employee_type,
                               manager_email=manager_email,
                               slack_id=user.slack_id,
                               role_name=user.role_name,
                               is_active=user.is_active,
                               total_read=total_read_count,
                               total_own=total_own_count,
                               total_follow=total_follow_count)

            user_results.append(user_result)

        offset += limit
        query_results = _user_search_query(session, user_filter, offset, limit)

    return user_results


class MySQLSearchDataExtractor(Extractor):
    """
    Extractor to fetch data required to support search from MySQL.
    """
    ENTITY_TYPE = 'entity_type'
    MODEL_CLASS = 'model_class'
    JOB_PUBLISH_TAG = 'job_publish_tag'
    SEARCH_FUNCTION = 'search_function'

    CONN_STRING = 'conn_string'
    ENGINE_ECHO = 'engine_echo'
    CONNECT_ARGS = 'connect_args'
    QUERY_LIMIT = 'query_limit'

    _DEFAULT_QUERY_LIMIT = 500
    _DEFAULT_SEARCH_BY_ENTITY: Dict[str, Callable] = {
        'table': _table_search,
        'user': _user_search,
        'dashboard': _dashboard_search
    }

    def init(self, conf: ConfigTree) -> None:
        self.conf = conf
        self.entity = conf.get_string(MySQLSearchDataExtractor.ENTITY_TYPE, default='table').lower()
        if MySQLSearchDataExtractor.SEARCH_FUNCTION in conf:
            self.search_function = conf.get(MySQLSearchDataExtractor.SEARCH_FUNCTION)
        else:
            self.search_function = MySQLSearchDataExtractor._DEFAULT_SEARCH_BY_ENTITY[self.entity]
        self.published_tag = conf.get_string(MySQLSearchDataExtractor.JOB_PUBLISH_TAG, '')
        self.query_limit = conf.get_int(MySQLSearchDataExtractor.QUERY_LIMIT, self._DEFAULT_QUERY_LIMIT)

        connect_args = {k: v for k, v in self.conf.get_config(MySQLSearchDataExtractor.CONNECT_ARGS,
                                                              default=ConfigTree()).items()}
        self._engine = create_engine(conf.get_string(MySQLSearchDataExtractor.CONN_STRING),
                                     echo=conf.get_bool(MySQLSearchDataExtractor.ENGINE_ECHO, False),
                                     connect_args=connect_args)
        self._session_factory = sessionmaker(bind=self._engine)

        model_class = conf.get(MySQLSearchDataExtractor.MODEL_CLASS, None)
        if model_class:
            module_name, class_name = model_class.rsplit(".", 1)
            mod = importlib.import_module(module_name)
            self.model_class = getattr(mod, class_name)

        self._extract_iter: Optional[Iterator] = None

    def close(self) -> None:
        """
        Close connection to mysql.
        """
        try:
            self._engine.dispose()
        except Exception as e:
            LOGGER.error(f'Exception encountered while closing engine: {e}')

    def extract(self) -> Optional[Any]:
        """
        Return an object or a raw query result.
        """
        if not self._extract_iter:
            self._extract_iter = self._get_extract_iter()

        try:
            return next(self._extract_iter)
        except StopIteration:
            return None

    def _get_extract_iter(self) -> Iterator[Any]:
        if not hasattr(self, 'results'):
            session = self._session_factory()
            try:
                self.results = self.search_function(session=session,
                                                    published_tag=self.published_tag,
                                                    limit=self.query_limit)
            except Exception as e:
                LOGGER.exception('Exception encountered while executing the search function.')
                raise e
            finally:
                session.close()

        for result in self.results:
            if hasattr(self, 'model_class'):
                obj = self.model_class(**result)
                yield obj
            else:
                yield result

    def get_scope(self) -> str:
        return 'extractor.mysql_search_data'
