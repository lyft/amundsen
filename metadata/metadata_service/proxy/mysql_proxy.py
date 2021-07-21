# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import logging
import time
from random import randint
from typing import Any, Dict, List, Optional, Tuple, Type, Union

from amundsen_common.entity.resource_type import ResourceType
from amundsen_common.models.dashboard import DashboardSummary
from amundsen_common.models.feature import Feature
from amundsen_common.models.generation_code import GenerationCode
from amundsen_common.models.lineage import Lineage
from amundsen_common.models.popular_table import PopularTable
from amundsen_common.models.table import Application
from amundsen_common.models.table import Badge
from amundsen_common.models.table import Badge as TableBadge
from amundsen_common.models.table import (Column, ProgrammaticDescription,
                                          Reader, Source, Stat, Table, Tag,
                                          User, Watermark)
from amundsen_common.models.user import User as UserEntity
from amundsen_common.models.user import UserSchema
from amundsen_rds.models import RDSModel
from amundsen_rds.models.badge import Badge as RDSBadge
from amundsen_rds.models.base import Base
from amundsen_rds.models.cluster import Cluster as RDSCluster
from amundsen_rds.models.column import \
    ColumnDescription as RDSColumnDescription
from amundsen_rds.models.column import TableColumn as RDSColumn
from amundsen_rds.models.dashboard import Dashboard as RDSDashboard
from amundsen_rds.models.dashboard import DashboardChart as RDSDashboardChart
from amundsen_rds.models.dashboard import \
    DashboardCluster as RDSDashboardCluster
from amundsen_rds.models.dashboard import \
    DashboardDescription as RDSDashboardDescription
from amundsen_rds.models.dashboard import \
    DashboardExecution as RDSDashboardExecution
from amundsen_rds.models.dashboard import \
    DashboardFollower as RDSDashboardFollower
from amundsen_rds.models.dashboard import DashboardGroup as RDSDashboardGroup
from amundsen_rds.models.dashboard import \
    DashboardGroupDescription as RDSDashboardGroupDescription
from amundsen_rds.models.dashboard import DashboardOwner as RDSDashboardOwner
from amundsen_rds.models.dashboard import DashboardQuery as RDSDashboardQuery
from amundsen_rds.models.dashboard import DashboardTable as RDSDashboardTable
from amundsen_rds.models.dashboard import DashboardTag as RDSDashboardTag
from amundsen_rds.models.dashboard import DashboardUsage as RDSDashboardUsage
from amundsen_rds.models.database import Database as RDSDatabase
from amundsen_rds.models.schema import Schema as RDSSchema
from amundsen_rds.models.table import Table as RDSTable
from amundsen_rds.models.table import TableDescription as RDSTableDescription
from amundsen_rds.models.table import TableFollower as RDSTableFollower
from amundsen_rds.models.table import TableOwner as RDSTableOwner
from amundsen_rds.models.table import TableTag as RDSTableTag
from amundsen_rds.models.table import TableUsage as RDSTableUsage
from amundsen_rds.models.tag import Tag as RDSTag
from amundsen_rds.models.updated_timestamp import \
    UpdatedTimestamp as RDSUpdatedTimestamp
from amundsen_rds.models.user import User as RDSUser
from beaker.cache import CacheManager
from beaker.util import parse_cache_config_options
from flask import current_app as app
from sqlalchemy import func
from sqlalchemy.orm import Session, load_only, subqueryload

from metadata_service.client.rds_client import RDSClient
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
_GET_POPULAR_TABLE_CACHE_EXPIRY_SEC = 11 * 60 * 60 + randint(0, 3600)

resource_relation_model = {
    ResourceType.Table: {
        UserResourceRel.read: RDSTableUsage,
        UserResourceRel.own: RDSTableOwner,
        UserResourceRel.follow: RDSTableFollower
    },
    ResourceType.Dashboard: {
        UserResourceRel.read: RDSDashboardUsage,
        UserResourceRel.own: RDSDashboardOwner,
        UserResourceRel.follow: RDSDashboardFollower
    }
}

LOGGER = logging.getLogger(__name__)


class MySQLProxy(BaseProxy):
    """
    A proxy to MySQL using SQLAlchemy ORM and Amundsen RDS
    See https://docs.sqlalchemy.org/en/13/orm/
    See https://github.com/amundsen-io/amundsenrds
    """
    def __init__(self, *,
                 host: Optional[str] = None,
                 port: Optional[int] = None,
                 user: Optional[str] = None,
                 password: Optional[str] = None,
                 client_kwargs: Dict = dict(),
                 **kwargs: Dict
                 ) -> None:
        endpoint = app.config['SQLALCHEMY_DATABASE_URI']
        if not endpoint:
            database = app.config['PROXY_DATABASE']
            endpoint = f'mysql://{user}:{password}@{host}:{port}/{database}'

        self.client = RDSClient(sql_alchemy_url=endpoint, client_kwargs=client_kwargs)

        is_the_latest_schema = self.client.validate_schema_version()
        if not is_the_latest_schema:
            LOGGER.warning('Warning: DB Schema is not up to date and it may cause some features not supported. '
                           'Please run rds command to upgrade the schema.')

    def is_healthy(self) -> None:
        with self.client.create_session() as session:
            session.execute('SELECT 1 as is_alive')

    @timer_with_counter
    def get_user(self, *, id: str) -> Union[User, None]:
        """
        Retrieve user detail based on id(email).
        :param id: the email for the given user
        :return:
        """
        with self.client.create_session() as session:
            user_record = session.query(RDSUser).filter(RDSUser.rk == id).first()
            if not user_record:
                return user_record

            manager_record = user_record.manager

            manager_name = ''
            if manager_record and manager_record.full_name:
                manager_name = manager_record.full_name

        return self._build_user_from_record(user_record=user_record, manager_name=manager_name)

    @timer_with_counter
    def get_users(self) -> List[User]:
        """
        Retrieve all the user details.
        :return:
        """
        with self.client.create_session() as session:
            users = session.query(RDSUser).filter(RDSUser.is_active.is_(True)).all()

        return [self._build_user_from_record(user_record=user) for user in users]

    @staticmethod
    def _build_user_from_record(user_record: RDSUser, manager_name: str = '') -> UserEntity:
        return UserEntity(email=user_record.email,
                          first_name=user_record.first_name,
                          last_name=user_record.last_name,
                          full_name=user_record.full_name,
                          is_active=user_record.is_active if user_record.is_active else False,
                          github_username=user_record.github_username,
                          team_name=user_record.team_name,
                          slack_id=user_record.slack_id,
                          employee_type=user_record.employee_type,
                          role_name=user_record.role_name,
                          manager_fullname=manager_name)

    @timer_with_counter
    def create_update_user(self, *, user: User) -> Tuple[User, bool]:
        """
        Create a user if it does not exist, otherwise update the user.
        :param user:
        :return:
        """
        user_data = UserSchema().dump(user)
        user_record = RDSUser(rk=user.user_id,
                              manager_rk=user.manager_id,
                              published_tag='api_create_update_user',
                              publisher_last_updated_epoch_ms=int(time.time() * 1000))
        for attr, value in user_data.items():
            if hasattr(user_record, attr):
                user_record.__setattr__(attr, value)

        with self.client.create_session() as session:
            existed_user = session.query(RDSUser).filter(RDSUser.rk == user.user_id).first()
            is_new = False if existed_user else True

            session.merge(user_record)
            session.commit()

        user_result = self._build_user_from_record(user_record)

        return user_result, is_new

    @timer_with_counter
    def get_table(self, *, table_uri: str) -> Table:
        """
        Retrieve table detail.
        :param table_uri:
        :return:
        """
        with self.client.create_session() as session:
            # table
            table = self._get_table_metadata(session=session, table_uri=table_uri)
            if not table:
                raise NotFoundException(f'Table URI( {table_uri} ) does not exist')

            # columns
            cols = self._get_table_columns(session=session, table_uri=table_uri)

            # usage
            readers = self._get_table_readers(session=session, table_uri=table_uri)

        table_result = Table(database=table['database'].name,
                             cluster=table['cluster'].name,
                             schema=table['schema'].name,
                             name=table['table'].name,
                             tags=table['tags'],
                             badges=table['badges'],
                             description=table['description'].description if table['description'] else None,
                             columns=cols,
                             owners=table['owners'],
                             table_readers=readers,
                             watermarks=table['watermarks'],
                             table_writer=table['table_writer'],
                             last_updated_timestamp=table['last_updated_timestamp'],
                             source=table['source'],
                             is_view=table['table'].is_view,
                             programmatic_descriptions=table['programmatic_descriptions'])
        return table_result

    @timer_with_counter
    def _get_table_metadata(self, *, session: Session, table_uri: str) -> Optional[Dict[str, Any]]:
        table = session.query(RDSTable).filter(RDSTable.rk == table_uri).first()
        if not table:
            return None

        schema = table.schema
        cluster = schema.cluster
        database = cluster.database

        # watermark
        watermark_results = []
        for watermark in table.watermarks:
            watermark_type = watermark.rk.split('/')[-2]
            watermark_result = Watermark(watermark_type=watermark_type,
                                         partition_key=watermark.partition_key,
                                         partition_value=watermark.partition_value,
                                         create_time=watermark.create_time)
            watermark_results.append(watermark_result)

        # tags
        tag_results = []
        tags = [tag for tag in table.tags if tag.tag_type == 'default']
        for tag in tags:
            tag_result = Tag(tag_name=tag.rk, tag_type=tag.tag_type)
            tag_results.append(tag_result)

        # badges
        badge_results = []
        for badge in table.badges:
            badge_result = TableBadge(badge_name=badge.rk, category=badge.category)
            badge_results.append(badge_result)

        # application
        table_writer = None
        application = table.application
        if application is not None:
            application_id = '' if application.id is None else application.id
            table_writer = Application(application_url=application.application_url,
                                       description=application.description,
                                       name=application.name,
                                       id=application_id)
        # timestamp_value
        timestamp_value = table.timestamp.last_updated_timestamp if table.timestamp else None

        # owners
        owner_results = []
        for owner in table.owners:
            owner_results.append(User(email=owner.email))

        # source
        source_result = None
        source = table.source
        if source is not None:
            source_result = Source(source_type=source.source_type, source=source.source)

        # description
        description_result = table.description

        # programmatic descriptions
        prog_description_results = []
        for prog_desc in table.programmatic_descriptions:
            source = prog_desc.description_source
            if source is None:
                LOGGER.error("A programmatic description with no source was found... skipping.")
            else:
                prog_description_results.append(ProgrammaticDescription(source=source,
                                                                        text=prog_desc.description))
        prog_description_results.sort(key=lambda x: x.source)

        table_metadata_result = dict(database=database,
                                     cluster=cluster,
                                     schema=schema,
                                     table=table,
                                     tags=tag_results,
                                     badges=badge_results,
                                     description=description_result,
                                     owners=owner_results,
                                     watermarks=watermark_results,
                                     table_writer=table_writer,
                                     last_updated_timestamp=timestamp_value,
                                     source=source_result,
                                     programmatic_descriptions=prog_description_results)

        return table_metadata_result

    @timer_with_counter
    def _get_table_columns(self, *, session: Session, table_uri: str) -> List[Column]:
        # column
        query = session.query(RDSColumn).filter(RDSColumn.table_rk == table_uri)

        # description, stats, badges
        query = query.options(
            subqueryload(RDSColumn.description),
            subqueryload(RDSColumn.stats),
            subqueryload(RDSColumn.badges)
        )

        columns = query.all()

        col_results = []
        for column in columns:
            col_stat_results = []
            for stat in column.stats:
                col_stat_result = Stat(
                    stat_type=stat.stat_type,
                    stat_val=stat.stat_val,
                    start_epoch=int(float(stat.start_epoch)),
                    end_epoch=int(float(stat.end_epoch))
                )
                col_stat_results.append(col_stat_result)

            col_badge_results = []
            for badge in column.badges:
                col_badge_results.append(
                    TableBadge(badge_name=badge.rk, category=badge.category)
                )

            col_result = Column(name=column.name,
                                description=column.description.description
                                if column.description else None,
                                col_type=column.type,
                                sort_order=int(column.sort_order),
                                stats=col_stat_results,
                                badges=col_badge_results)
            col_results.append(col_result)

        return col_results

    @timer_with_counter
    def _get_table_readers(self, *, session: Session, table_uri: str) -> List[Reader]:
        readers = session.query(RDSTableUsage).filter(
            RDSTableUsage.table_rk == table_uri
        ).order_by(RDSTableUsage.read_count).limit(5).all()

        reader_results = []
        for reader in readers:
            reader_result = Reader(user=User(email=reader.user_rk),
                                   read_count=reader.read_count)
            reader_results.append(reader_result)

        return reader_results

    @timer_with_counter
    def delete_owner(self, *, table_uri: str, owner: str) -> None:
        """
        Delete relation between the given table and owner.
        :param table_uri:
        :param owner:
        :return:
        """
        try:
            with self.client.create_session() as session:
                session.query(RDSTableOwner).filter(
                    RDSTableOwner.table_rk == table_uri,
                    RDSTableOwner.user_rk == owner
                ).delete()
                session.commit()
        except Exception as e:
            LOGGER.exception(f'Failed to delete owner {owner} for table {table_uri}')
            raise e

    @timer_with_counter
    def add_owner(self, *, table_uri: str, owner: str) -> None:
        """
        Add the owner for the given table.
        :param table_uri:
        :param owner:
        :return:
        """
        user = RDSUser(rk=owner, email=owner)
        table_owner = RDSTableOwner(table_rk=table_uri, user_rk=owner)
        try:
            with self.client.create_session() as session:
                session.merge(user)
                session.merge(table_owner)
                session.commit()
        except Exception as e:
            LOGGER.exception(f'Failed to add owner {owner} for table {table_uri}')
            raise e

    @timer_with_counter
    def get_table_description(self, *, table_uri: str) -> Union[str, None]:
        """
        Get the table description based on table uri.
        :param table_uri:
        :return:
        """
        with self.client.create_session() as session:
            description = session.query(RDSTableDescription.description).filter(
                RDSTableDescription.table_rk == table_uri
            ).scalar()

        return description

    @timer_with_counter
    def put_table_description(self, *, table_uri: str, description: str) -> None:
        """
        Update table description with one from user
        :param table_uri:
        :param description:
        :return:
        """
        desc_key = table_uri + '/_description'
        description = RDSTableDescription(rk=desc_key, description=description, table_rk=table_uri)
        try:
            with self.client.create_session() as session:
                session.merge(description)
                session.commit()
        except Exception as e:
            LOGGER.exception(f'Failed to add description for table {table_uri}')
            raise e

    @timer_with_counter
    def add_tag(self, *,
                id: str,
                tag: str,
                tag_type: str = 'default',
                resource_type: ResourceType = ResourceType.Table) -> None:
        """
        Add a new tag if it does not exist and add the relation between the given resource and tag.
        :param id:
        :param tag:
        :param tag_type:
        :param resource_type:
        :return:
        """
        LOGGER.info(f'New tag {tag} for id {id} with type {tag_type} and resource type {resource_type.name}')

        resource_table = f'{resource_type.name.lower()}_tag'
        resource_model = self._get_model_from_table_name(resource_table)
        if not resource_model:
            raise NotImplementedError(f'The resource type {resource_type.name} is not defined!')

        resource_key = f'{resource_type.name.lower()}_rk'

        tag_record = RDSTag(rk=tag, tag_type=tag_type)
        resource_tag_record = resource_model(tag_rk=tag)
        resource_tag_record.__setattr__(resource_key, id)
        try:
            with self.client.create_session() as session:
                session.merge(tag_record)
                session.merge(resource_tag_record)
                session.commit()
        except Exception as e:
            LOGGER.exception(f'Failed to add tag {tag} for {id}')
            raise e

    @timer_with_counter
    def add_badge(self, *,
                  id: str,
                  badge_name: str,
                  category: str = '',
                  resource_type: ResourceType = ResourceType.Table) -> None:
        """
        Add a new badge if it does not exist and add the relation between the given resource and badge.
        :param id:
        :param badge_name:
        :param category:
        :param resource_type:
        :return:
        """
        LOGGER.info(f'New badge {badge_name} for id {id} with category {category} '
                    f'and resource type {resource_type.name}')

        resource_table = f'{resource_type.name.lower()}_badge'
        resource_model = self._get_model_from_table_name(resource_table)
        if not resource_model:
            raise NotImplementedError(f'The resource type {resource_type.name} is not defined!')

        resource_key = f'{resource_type.name.lower()}_rk'

        badge_record = RDSBadge(rk=badge_name, category=category)
        resource_badge_record = resource_model(badge_rk=badge_name)
        resource_badge_record.__setattr__(resource_key, id)
        try:
            with self.client.create_session() as session:
                session.merge(badge_record)
                session.merge(resource_badge_record)
                session.commit()
        except Exception as e:
            LOGGER.exception(f'Failed to add badge {badge_name} for {id}')
            raise e

    @timer_with_counter
    def delete_tag(self, *,
                   id: str,
                   tag: str,
                   tag_type: str = 'default',
                   resource_type: ResourceType = ResourceType.Table) -> None:
        """
        Delete the relation between the resource and the tag.
        :param id:
        :param tag:
        :param tag_type:
        :param resource_type:
        :return:
        """
        LOGGER.info(f'Delete tag {tag} for {id} with type {tag_type} and resource_type: {resource_type.name}')

        resource_table = f'{resource_type.name.lower()}_tag'
        resource_model = self._get_model_from_table_name(resource_table)
        if not resource_model:
            raise NotImplementedError(f'{resource_type.name} is not defined!')

        resource_key = f'{resource_type.name.lower()}_rk'
        resource_attr = getattr(resource_model, resource_key)
        tag_attr = getattr(resource_model, 'tag_rk')
        try:
            with self.client.create_session() as session:
                session.query(resource_model).filter(resource_attr == id, tag_attr == tag).delete()
                session.commit()
        except Exception as e:
            LOGGER.exception(f'Failed to delete tag {tag} for {id}')
            raise e

    @timer_with_counter
    def delete_badge(self, *,
                     id: str,
                     badge_name: str,
                     category: str,
                     resource_type: ResourceType = ResourceType.Table) -> None:
        """
        Delete the relation between the resource and the badge.
        :param id:
        :param badge_name:
        :param category:
        :param resource_type:
        :return:
        """
        LOGGER.info(f'Delete badge {badge_name} for {id} with {category}')

        resource_table = f'{resource_type.name.lower()}_badge'
        resource_model = self._get_model_from_table_name(resource_table)
        if not resource_model:
            raise NotImplementedError(f'{resource_type.name} is not defined!')

        resource_key = f'{resource_type.name.lower()}_rk'
        resource_attr = getattr(resource_model, resource_key)
        badge_attr = getattr(resource_model, 'badge_rk')
        try:
            with self.client.create_session() as session:
                session.query(resource_model).filter(resource_attr == id, badge_attr == badge_name).delete()
                session.commit()
        except Exception as e:
            LOGGER.exception(f'Failed to delete badge {badge_name} for {id}')
            raise e

    @staticmethod
    def _get_model_from_table_name(table_name: str) -> Optional[Type[RDSModel]]:
        """
        Get rds model for the given table name.
        :param table_name:
        :return:
        """
        table_model = None
        for model in Base._decl_class_registry.values():
            if hasattr(model, '__tablename__') and model.__tablename__ == table_name:
                table_model = model

        return table_model

    @timer_with_counter
    def put_column_description(self, *, table_uri: str, column_name: str, description: str) -> None:
        """
        Update column description with input from user.
        :param table_uri:
        :param column_name:
        :param description:
        :return:
        """
        column_uri = table_uri + '/' + column_name
        desc_key = column_uri + '/_description'
        description = RDSColumnDescription(rk=desc_key, description=description, column_rk=column_uri)
        try:
            with self.client.create_session() as session:
                session.merge(description)
                session.commit()
        except Exception as e:
            LOGGER.exception(f'Failed to update the table {table_uri} column {column_name} description')
            raise e

    @timer_with_counter
    def get_column_description(self, *, table_uri: str, column_name: str) -> Union[str, None]:
        """
        Get the column description based on table uri.
        :param table_uri:
        :param column_name:
        :return:
        """
        column_uri = table_uri + '/' + column_name
        desc_key = column_uri + '/_description'
        with self.client.create_session() as session:
            description = session.query(RDSColumnDescription.description).filter(
                RDSColumnDescription.rk == desc_key
            ).scalar()

        return description

    @timer_with_counter
    def get_popular_tables(self, *, num_entries: int, user_id: Optional[str] = None) -> List[PopularTable]:
        """
        Retrieve popular tables. As popular table computation requires full scan of table usage,
        it will utilize cached method _get_popular_tables_uris.
        :param num_entries:
        :param user_id:
        :return:
        """
        if user_id is None:
            table_uris = self._get_global_popular_tables_uris(num_entries=num_entries)
        else:
            table_uris = self._get_personal_popular_tables_uris(num_entries=num_entries, user_id=user_id)

        if not table_uris:
            return []

        with self.client.create_session() as session:
            # table
            query = session.query(RDSTable).filter(RDSTable.rk.in_(table_uris))

            # description
            query = query.options(
                subqueryload(RDSTable.description).options(
                    load_only(RDSTableDescription.description)
                )
            )

            # schema, cluster, database
            query = query.options(
                subqueryload(RDSTable.schema).options(
                    load_only(RDSSchema.name, RDSSchema.cluster_rk),
                    subqueryload(RDSSchema.cluster).options(
                        load_only(RDSCluster.name, RDSCluster.database_rk),
                        subqueryload(RDSCluster.database).options(
                            load_only(RDSDatabase.name)
                        )
                    )
                )
            )

            tables = query.all()

        popular_tables = []
        for table in tables:
            schema = table.schema
            cluster = schema.cluster
            database = cluster.database
            description = table.description
            popular_table = PopularTable(database=database.name,
                                         cluster=cluster.name,
                                         schema=schema.name,
                                         name=table.name,
                                         description=description.description if description else None)
            popular_tables.append(popular_table)

        return popular_tables

    @_CACHE.cache('_get_global_popular_tables_uris', _GET_POPULAR_TABLE_CACHE_EXPIRY_SEC)
    def _get_global_popular_tables_uris(self, num_entries: int) -> List[str]:
        """
        Retrieve popular table uris. Will provide tables with top x popularity score.
        Popularity score = number of distinct readers * log(total number of reads)
        The result of this method will be cached based on the key (num_entries),
        and the cache will be expired based on _GET_POPULAR_TABLE_CACHE_EXPIRY_SEC
        :param num_entries:
        :return:
        """
        LOGGER.info('Querying global popular tables URIs')

        num_readers = app.config['POPULAR_RESOURCES_MINIMUM_READER_COUNT']
        with self.client.create_session() as session:
            readers = func.count(RDSTableUsage.user_rk).label('readers')

            usage_subquery = session.query(
                RDSTableUsage.table_rk,
                readers,
                func.sum(RDSTableUsage.read_count).label('total_reads')
            ).group_by(RDSTableUsage.table_rk).having(readers >= num_readers).subquery()

            popular_usage = session.query(usage_subquery.c.table_rk).order_by(
                (usage_subquery.c.readers * func.log(usage_subquery.c.total_reads)).desc()
            ).limit(num_entries).all()

        return [usage.table_rk for usage in popular_usage]

    @timer_with_counter
    @_CACHE.cache('_get_personal_popular_tables_uris', _GET_POPULAR_TABLE_CACHE_EXPIRY_SEC)
    def _get_personal_popular_tables_uris(self, num_entries: int, user_id: str) -> List[str]:
        """
        Retrieve personalized popular table uris. Will provide tables with top
        popularity score that have been read by a peer of the user_id provided.
        The popularity score is defined in the same way as `_get_global_popular_tables_uris`
        The result of this method will be cached based on the key (num_entries, user_id),
        and the cache will be expired based on _GET_POPULAR_TABLE_CACHE_EXPIRY_SEC
        :param num_entries:
        :param user_id:
        :return:
        """
        LOGGER.info('Querying personal popular tables URIs')

        num_readers = app.config['POPULAR_RESOURCES_MINIMUM_READER_COUNT']
        with self.client.create_session() as session:
            readers = func.count(RDSTableUsage.user_rk).label('readers')

            usage_subquery = session.query(
                RDSTableUsage.table_rk,
                readers,
                func.sum(RDSTableUsage.read_count).label('total_reads')
            ).filter(
                RDSTableUsage.user_rk == user_id
            ).group_by(RDSTableUsage.table_rk).having(readers >= num_readers).subquery()

            popular_usage = session.query(usage_subquery.c.table_rk).order_by(
                (usage_subquery.c.readers * func.log(usage_subquery.c.total_reads)).desc()
            ).limit(num_entries).all()

        return [usage.table_rk for usage in popular_usage]

    @timer_with_counter
    def get_latest_updated_ts(self) -> Optional[int]:
        """
        Fetch last updated / index timestamp for mysql.
        :return:
        """
        with self.client.create_session() as session:
            latest_updated_ts_value = session.query(RDSUpdatedTimestamp.latest_timestamp).scalar()

        return latest_updated_ts_value

    @timer_with_counter
    def get_tags(self) -> List:
        """
        Get all existing tags.
        :return:
        """
        LOGGER.info('Get all the tags')

        with self.client.create_session() as session:
            tag_count = (func.count(RDSTableTag.table_rk)
                         + func.count(RDSDashboardTag.dashboard_rk)).label('tag_count')

            records = session.query(
                RDSTag.rk.label('tag_name'),
                tag_count
            )\
                .outerjoin(RDSTableTag)\
                .outerjoin(RDSDashboardTag)\
                .filter(RDSTag.tag_type == 'default')\
                .group_by(RDSTag.rk)\
                .having(tag_count > 0)\
                .all()

        results = []
        for record in records:
            results.append(TagDetail(tag_name=record.tag_name,
                                     tag_count=record.tag_count))

        return results

    @timer_with_counter
    def get_badges(self) -> List:
        """
        Get all existing badges.
        :return:
        """
        LOGGER.info('Get all badges')

        with self.client.create_session() as session:
            badges = session.query(RDSBadge).all()

        results = []
        for badge in badges:
            results.append(Badge(badge_name=badge.rk,
                                 category=badge.category))

        return results

    @timer_with_counter
    def get_dashboard_by_user_relation(self, *, user_email: str, relation_type: UserResourceRel) -> \
            Dict[str, List[DashboardSummary]]:
        """
        Retrieve all dashboards based on the given user and relation.
        :param user_email:
        :param relation_type:
        :return:
        """
        if relation_type not in resource_relation_model[ResourceType.Dashboard]:
            raise NotImplementedError(f'The relation type {relation_type} is not defined!')

        relation_model = resource_relation_model[ResourceType.Dashboard][relation_type]
        dashboard_attr = getattr(relation_model, 'dashboard_rk')
        user_attr = getattr(relation_model, 'user_rk')
        with self.client.create_session() as session:
            dashboard_subquery = session.query(dashboard_attr).filter(user_attr == user_email).subquery()

            query = session.query(RDSDashboard).filter(RDSDashboard.rk.in_(dashboard_subquery)).options(
                subqueryload(RDSDashboard.group).options(
                    subqueryload(RDSDashboardGroup.description).options(
                        load_only(RDSDashboardGroupDescription.description)
                    ),
                    subqueryload(RDSDashboardGroup.cluster).options(
                        load_only(RDSDashboardCluster.name)
                    )
                ),
                subqueryload(RDSDashboard.description).options(
                    load_only(RDSDashboardDescription.description)
                ),
                subqueryload(RDSDashboard.execution).options(
                    load_only(RDSDashboardExecution.rk, RDSDashboardExecution.timestamp)
                )
            )

            dashboards = query.all()

        results = []
        for dashboard in dashboards:
            product = dashboard.rk.split('_')[0]
            description = dashboard.description
            group = dashboard.group
            last_exec = next((execution for execution in dashboard.execution
                              if execution.rk.endswith('_last_successful_execution')), None)
            results.append(DashboardSummary(uri=dashboard.rk,
                                            cluster=group.cluster.name,
                                            group_name=group.name,
                                            group_url=group.dashboard_group_url,
                                            product=product,
                                            name=dashboard.name,
                                            url=dashboard.dashboard_url,
                                            description=description.description if description else None,
                                            last_successful_run_timestamp=last_exec.timestamp
                                            if last_exec else None))

        return {ResourceType.Dashboard.name.lower(): results}

    @timer_with_counter
    def get_table_by_user_relation(self, *, user_email: str, relation_type: UserResourceRel) -> Dict[str, Any]:
        """
        Retrieve all the tables based on the given user and relation.
        :param user_email:
        :param relation_type:
        :return:
        """
        if relation_type not in resource_relation_model[ResourceType.Table]:
            raise NotImplementedError(f'The relation type {relation_type} is not defined!')

        relation_model = resource_relation_model[ResourceType.Table][relation_type]
        table_attr = getattr(relation_model, 'table_rk')
        user_attr = getattr(relation_model, 'user_rk')
        with self.client.create_session() as session:
            table_subquery = session.query(table_attr).filter(user_attr == user_email).subquery()

            query = session.query(RDSTable).filter(RDSTable.rk.in_(table_subquery)).options(
                load_only(RDSTable.rk, RDSTable.name, RDSTable.schema_rk),
                subqueryload(RDSTable.description).options(
                    load_only(RDSTableDescription.description)
                ),
                subqueryload(RDSTable.schema).options(
                    load_only(RDSSchema.name, RDSSchema.cluster_rk),
                    subqueryload(RDSSchema.cluster).options(
                        load_only(RDSCluster.name, RDSCluster.database_rk),
                        subqueryload(RDSCluster.database).options(
                            load_only(RDSDatabase.name)
                        )
                    )
                )
            )

            tables = query.all()

        results = []
        for table in tables:
            description = table.description
            schema = table.schema
            cluster = schema.cluster
            database = cluster.database

            results.append(PopularTable(database=database.name,
                                        cluster=cluster.name,
                                        schema=schema.name,
                                        name=table.name,
                                        description=description.description if description else None))

        return {ResourceType.Table.name.lower(): results}

    @timer_with_counter
    def get_frequently_used_tables(self, *, user_email: str) -> Dict[str, Any]:
        """
        Retrieve all the tables from usage records.
        :param user_email:
        :return:
        """
        with self.client.create_session() as session:
            # usage
            frequently_used_tables_uris = self._get_frequently_used_tables_uris(session=session,
                                                                                user_email=user_email)

            # table
            query = session.query(RDSTable).filter(RDSTable.rk.in_(frequently_used_tables_uris)).options(
                load_only(RDSTable.rk, RDSTable.name, RDSTable.schema_rk)
            )

            # description, schema, cluster, database
            query = query.options(
                subqueryload(RDSTable.description).options(
                    load_only(RDSTableDescription.description)
                ),
                subqueryload(RDSTable.schema).options(
                    load_only(RDSSchema.name, RDSSchema.cluster_rk),
                    subqueryload(RDSSchema.cluster).options(
                        load_only(RDSCluster.name, RDSCluster.database_rk),
                        subqueryload(RDSCluster.database).options(
                            load_only(RDSDatabase.name)
                        )
                    )
                )
            )

            tables = query.all()

        results = []
        for table in tables:
            description = table.description
            schema = table.schema
            cluster = schema.cluster
            database = cluster.database

            results.append(PopularTable(database=database.name,
                                        cluster=cluster.name,
                                        schema=schema.name,
                                        name=table.name,
                                        description=description.description if description else None))
        return {'table': results}

    @timer_with_counter
    def _get_frequently_used_tables_uris(self, *, session: Session, user_email: str) -> List[str]:
        records = session.query(RDSTableUsage.table_rk).filter(
            RDSTableUsage.user_rk == user_email,
            RDSTableUsage.published_tag.isnot(None)
        ).order_by(
            RDSTableUsage.published_tag.desc(),
            RDSTableUsage.read_count.desc()
        ).limit(50).all()

        table_uris = []
        for record in records:
            table_uris.append(record.table_rk)

        return table_uris

    @timer_with_counter
    def add_resource_relation_by_user(self, *, id: str,
                                      user_id: str,
                                      relation_type: UserResourceRel,
                                      resource_type: ResourceType) -> None:
        """
        Add a new user if it does not exist and add the relation between the given resource and user.
        :param id:
        :param user_id:
        :param relation_type:
        :param resource_type:
        :return:
        """
        if resource_type not in resource_relation_model:
            raise NotImplementedError(f'The resource_type {resource_type.name} is not defined!')

        if relation_type not in resource_relation_model[resource_type]:
            raise NotImplementedError(f'the relation type {relation_type} is not defined!')

        res_rel_model = resource_relation_model[resource_type][relation_type]
        res_key = f'{resource_type.name.lower()}_rk'

        user_record = RDSUser(rk=user_id, email=user_id)
        res_rel_record = res_rel_model(user_rk=user_id)
        res_rel_record.__setattr__(res_key, id)
        try:
            with self.client.create_session() as session:
                session.merge(user_record)
                session.merge(res_rel_record)
                session.commit()
        except Exception as e:
            LOGGER.exception(f'Failed to create relation between user {user_id} and resource {id}')
            raise e

    @timer_with_counter
    def delete_resource_relation_by_user(self, *,
                                         id: str,
                                         user_id: str,
                                         relation_type: UserResourceRel,
                                         resource_type: ResourceType) -> None:
        """
        Delete the relation between the given user and resource.
        :param id:
        :param user_id:
        :param relation_type:
        :param resource_type:
        :return:
        """
        if resource_type not in resource_relation_model:
            raise NotImplementedError(f'The resource_type {resource_type.name} is not define!')

        if relation_type not in resource_relation_model[resource_type]:
            raise NotImplementedError(f'the relation type {relation_type} is not defined!')

        res_rel_model = resource_relation_model[resource_type][relation_type]
        res_key = f'{resource_type.name.lower()}_rk'
        user_attr = getattr(res_rel_model, 'user_rk')
        res_attr = getattr(res_rel_model, res_key)
        try:
            with self.client.create_session() as session:
                session.query(res_rel_model).filter(user_attr == user_id, res_attr == id).delete()
                session.commit()
        except Exception as e:
            LOGGER.exception(f'Failed to delete relation between user {user_id} and resource {id}')
            raise e

    @timer_with_counter
    def get_dashboard(self, id: str) -> DashboardDetailEntity:
        """
        Retrieve dashboard detail.
        :param id:
        :return:
        """
        with self.client.create_session() as session:
            dashboard_result = self._get_dashboard_metadata(session=session, id=id)
            if not dashboard_result:
                raise NotFoundException(f'No dashboard exist with URI: {id}')

            dashboard_query_result = self._get_dashboard_queries(session=session, id=id)
            dashboard_table_result = self._get_dashboard_tables(session=session, id=id)

        return DashboardDetailEntity(uri=dashboard_result['uri'],
                                     cluster=dashboard_result['cluster'],
                                     url=dashboard_result['url'],
                                     name=dashboard_result['name'],
                                     product=dashboard_result['product'],
                                     created_timestamp=dashboard_result['created_timestamp'],
                                     description=dashboard_result['description'],
                                     group_name=dashboard_result['group_name'],
                                     group_url=dashboard_result['group_url'],
                                     last_successful_run_timestamp=dashboard_result['last_successful_run_timestamp'],
                                     last_run_timestamp=dashboard_result['last_run_timestamp'],
                                     last_run_state=dashboard_result['last_run_state'],
                                     updated_timestamp=dashboard_result['updated_timestamp'],
                                     owners=dashboard_result['owners'],
                                     tags=dashboard_result['tags'],
                                     badges=dashboard_result['badges'],
                                     recent_view_count=dashboard_result['recent_view_count'],
                                     chart_names=dashboard_query_result['chart_names'],
                                     query_names=dashboard_query_result['query_names'],
                                     queries=dashboard_query_result['queries'],
                                     tables=dashboard_table_result)

    @timer_with_counter
    def _get_dashboard_metadata(self, session: Session, id: str) -> Optional[Dict[str, Any]]:
        dashboard = session.query(RDSDashboard).filter(RDSDashboard.rk == id).first()
        if not dashboard:
            return None

        product = dashboard.rk.split('_')[0]
        execution = dashboard.execution
        last_suc_exec = next((execution for execution in execution
                              if execution.rk.endswith('_last_successful_execution')), None)

        last_exec = next((execution for execution in execution
                          if execution.rk.endswith('_last_execution')), None)

        updated_timestamp = dashboard.timestamp
        description = dashboard.description
        group = dashboard.group
        cluster = group.cluster
        owners = [self._build_user_from_record(owner) for owner in dashboard.owners]

        tags = [Tag(tag_type=tag.tag_type, tag_name=tag.rk) for tag in dashboard.tags if tag.tag_type == 'default']
        badges = [TableBadge(badge_name=badge.rk, category=badge.category) for badge in dashboard.badges]
        recent_view_count = sum(usage.read_count for usage in dashboard.usage) if dashboard.usage else 0

        return dict(uri=dashboard.rk,
                    cluster=cluster.name,
                    url=dashboard.dashboard_url,
                    name=dashboard.name,
                    product=product,
                    created_timestamp=dashboard.created_timestamp,
                    description=description.description if description else None,
                    group_name=group.name,
                    group_url=group.dashboard_group_url,
                    last_successful_run_timestamp=int(last_suc_exec.timestamp) if last_suc_exec else None,
                    last_run_timestamp=int(last_exec.timestamp) if last_exec else None,
                    last_run_state=last_exec.state if last_exec else None,
                    updated_timestamp=int(updated_timestamp.timestamp) if updated_timestamp else None,
                    owners=owners,
                    tags=tags,
                    badges=badges,
                    recent_view_count=recent_view_count)

    @timer_with_counter
    def _get_dashboard_queries(self, session: Session, id: str) -> Dict[str, Any]:
        dashboard_queries = session.query(RDSDashboardQuery).filter(RDSDashboardQuery.dashboard_rk == id).options(
            subqueryload(RDSDashboardQuery.charts).options(
                load_only(RDSDashboardChart.name)
            )
        ).all()

        chart_names = [chart.name for query in dashboard_queries for chart in query.charts]
        query_names = [query.name for query in dashboard_queries if query.name]
        queries = [DashboardQueryEntity(name=query.name, url=query.url, query_text=query.query_text)
                   for query in dashboard_queries if query.name or query.url or query.query_text]

        return dict(chart_names=chart_names, query_names=query_names, queries=queries)

    @timer_with_counter
    def _get_dashboard_tables(self, session: Session, id: str) -> List[PopularTable]:
        table_subquery = session.query(RDSDashboardTable.table_rk).filter(
            RDSDashboardTable.dashboard_rk == id
        ).subquery()

        tables_query = session.query(RDSTable).filter(RDSTable.rk.in_(table_subquery)).options(
            load_only(RDSTable.rk, RDSTable.name, RDSTable.schema_rk),
            subqueryload(RDSTable.description).options(
                load_only(RDSTableDescription.description)
            ),
            subqueryload(RDSTable.schema).options(
                load_only(RDSSchema.name, RDSSchema.cluster_rk),
                subqueryload(RDSSchema.cluster).options(
                    load_only(RDSCluster.name, RDSCluster.database_rk),
                    subqueryload(RDSCluster.database).options(
                        load_only(RDSDatabase.name)
                    )
                )
            )
        )

        tables = tables_query.all()

        table_results = []
        for table in tables:
            table_description = table.description
            table_schema = table.schema
            table_cluster = table_schema.cluster
            table_database = table_cluster.database
            table_results.append(
                PopularTable(
                    database=table_database.name,
                    cluster=table_cluster.name,
                    schema=table_schema.name,
                    name=table.name,
                    description=table_description.description if table_description else None
                )
            )

        return table_results

    @timer_with_counter
    def get_dashboard_description(self, *, id: str) -> Description:
        """
        Get the dashboard description based on dashboard uri.
        :param id:
        :return:
        """
        with self.client.create_session() as session:
            description = session.query(RDSDashboardDescription.description).filter(
                RDSDashboardDescription.dashboard_rk == id
            ).scalar()

        return Description(description=description)

    @timer_with_counter
    def put_dashboard_description(self, *, id: str, description: str) -> None:
        """
        Update dashboard description.
        :param id:
        :param description:
        :return:
        """
        desc_key = id + '/_description'
        description = RDSDashboardDescription(rk=desc_key, description=description, dashboard_rk=id)
        try:
            with self.client.create_session() as session:
                session.merge(description)
                session.commit()
        except Exception as e:
            LOGGER.exception(f'Failed to add description for dashboard {id}')
            raise e

    @timer_with_counter
    def get_resources_using_table(self, *, id: str, resource_type: ResourceType) -> Dict[str, List[DashboardSummary]]:
        """
        Fetch resources related to the given table
        :param id:
        :param resource_type:
        :return:
        """
        if resource_type != ResourceType.Dashboard:
            raise NotImplementedError(f'{resource_type.name} is not supported')

        with self.client.create_session() as session:
            dashboard_subquery = session.query(RDSDashboardTable.dashboard_rk).filter(
                RDSDashboardTable.table_rk == id
            ).subquery()

            usage_subquery = session.query(
                RDSDashboardUsage.dashboard_rk,
                func.sum(RDSDashboardUsage.read_count).label('recent_view_count')
            ).group_by(RDSDashboardUsage.dashboard_rk).filter(
                RDSDashboardUsage.dashboard_rk.in_(dashboard_subquery)
            ).subquery()

            query = session.query(RDSDashboard).join(usage_subquery).filter(
                RDSDashboard.rk == usage_subquery.c.dashboard_rk
            ).order_by(usage_subquery.c.recent_view_count.desc())

            query = query.options(
                subqueryload(RDSDashboard.group).options(
                    subqueryload(RDSDashboardGroup.description).options(
                        load_only(RDSDashboardGroupDescription.description)
                    ),
                    subqueryload(RDSDashboardGroup.cluster).options(
                        load_only(RDSDashboardCluster.name)
                    )
                ),
                subqueryload(RDSDashboard.description).options(
                    load_only(RDSDashboardDescription.description)
                ),
                subqueryload(RDSDashboard.execution).options(
                    load_only(RDSDashboardExecution.rk, RDSDashboardExecution.timestamp)
                )
            )

            dashboards = query.all()

        results = []
        for dashboard in dashboards:
            product = dashboard.rk.split('_')[0]
            description = dashboard.description
            group = dashboard.group
            last_exec = next((execution for execution in dashboard.execution
                              if execution.rk.endswith('_last_successful_execution')), None)
            results.append(DashboardSummary(uri=dashboard.rk,
                                            cluster=group.cluster.name,
                                            group_name=group.name,
                                            group_url=group.dashboard_group_url,
                                            product=product,
                                            name=dashboard.name,
                                            url=dashboard.dashboard_url,
                                            description=description.description if description else None,
                                            last_successful_run_timestamp=int(last_exec.timestamp)
                                            if last_exec else None))
        return {'dashboards': results}

    def get_statistics(self) -> Dict[str, Any]:
        pass

    def get_lineage(self, *, id: str, resource_type: ResourceType, direction: str, depth: int) -> Lineage:
        pass

    def get_feature(self, *, feature_uri: str) -> Feature:
        pass

    def get_resource_description(self, *, resource_type: ResourceType, uri: str) -> Description:
        pass

    def put_resource_description(self, *, resource_type: ResourceType, uri: str, description: str) -> None:
        pass

    def add_resource_owner(self, *, uri: str, resource_type: ResourceType, owner: str) -> None:
        pass

    def delete_resource_owner(self, *, uri: str, resource_type: ResourceType, owner: str) -> None:
        pass

    def get_resource_generation_code(self, *, uri: str, resource_type: ResourceType) -> GenerationCode:
        pass

    def get_popular_resources(self, *,
                              num_entries: int,
                              resource_types: List[str],
                              user_id: Optional[str] = None) -> Dict[str, List]:
        raise NotImplementedError
