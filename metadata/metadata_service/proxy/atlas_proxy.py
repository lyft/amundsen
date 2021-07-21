# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import datetime
import logging
import re
from collections import defaultdict
from operator import attrgetter
from random import randint
from typing import (Any, Dict, Generator, List, Optional, Set, Tuple, Type,
                    Union)

from amundsen_common.entity.resource_type import ResourceType
from amundsen_common.models.dashboard import DashboardSummary
from amundsen_common.models.feature import Feature
from amundsen_common.models.generation_code import GenerationCode
from amundsen_common.models.lineage import Lineage, LineageItem
from amundsen_common.models.popular_table import PopularTable
from amundsen_common.models.table import (Application, Badge, Column,
                                          ProgrammaticDescription, Reader,
                                          ResourceReport, Stat, Table, Tag,
                                          User, Watermark)
from amundsen_common.models.user import User as UserEntity
from amundsen_common.utils.atlas import (AtlasColumnKey, AtlasCommonParams,
                                         AtlasCommonTypes, AtlasDashboardTypes,
                                         AtlasStatus, AtlasTableKey,
                                         AtlasTableTypes)
from apache_atlas.client.base_client import AtlasClient
from apache_atlas.model.glossary import (AtlasGlossary, AtlasGlossaryHeader,
                                         AtlasGlossaryTerm)
from apache_atlas.model.instance import (AtlasEntitiesWithExtInfo, AtlasEntity,
                                         AtlasEntityHeader,
                                         AtlasEntityWithExtInfo,
                                         AtlasRelatedObjectId)
from apache_atlas.model.relationship import AtlasRelationship
from apache_atlas.utils import type_coerce
from beaker.cache import CacheManager
from beaker.util import parse_cache_config_options
from flask import current_app as app
from werkzeug.exceptions import BadRequest

from metadata_service.entity.dashboard_detail import \
    DashboardDetail as DashboardDetailEntity
from metadata_service.entity.dashboard_query import DashboardQuery
from metadata_service.entity.description import Description
from metadata_service.entity.tag_detail import TagDetail
from metadata_service.exception import NotFoundException
from metadata_service.proxy import BaseProxy
from metadata_service.util import UserResourceRel

LOGGER = logging.getLogger(__name__)

# Expire cache every 11 hours + jitter
_ATLAS_PROXY_CACHE_EXPIRY_SEC = 11 * 60 * 60 + randint(0, 3600)


# noinspection PyMethodMayBeStatic
class AtlasProxy(BaseProxy):
    """
    Atlas Proxy client for the amundsen metadata
    {ATLAS_API_DOCS} = https://atlas.apache.org/api/v2/
    """
    DB_ATTRIBUTE = 'db'
    STATISTICS_FORMAT_SPEC = app.config['STATISTICS_FORMAT_SPEC']
    # Qualified Name of the Glossary, that holds the user defined terms.
    # For Amundsen, we are using Glossary Terms as the Tags.
    AMUNDSEN_USER_TAGS = 'amundsen_user_tags'
    _CACHE = CacheManager(**parse_cache_config_options({'cache.regions': 'atlas_proxy',
                                                        'cache.atlas_proxy.type': 'memory',
                                                        'cache.atlas_proxy.expire': _ATLAS_PROXY_CACHE_EXPIRY_SEC}))

    def __init__(self, *,
                 host: str,
                 port: int,
                 user: str = 'admin',
                 password: str = '',
                 encrypted: bool = False,
                 validate_ssl: bool = False,
                 client_kwargs: dict = dict()) -> None:
        """
        Initiate the Apache Atlas client with the provided credentials
        """
        protocol = 'https' if encrypted else 'http'
        self.client = AtlasClient(f'{protocol}://{host}:{port}', (user, password))
        self.client.session.verify = validate_ssl

    def _parse_dashboard_bookmark_qn(self, bookmark_qn: str) -> Dict:
        """
        Parse bookmark qualifiedName and extract the info
        :param bookmark_qn: Qualified Name of Bookmark entity
        :return: Dictionary object containing following information:
        product: dashboard product
        cluster: cluster information
        dashboard_group: Dashboard group name
        dashboard_id: Dashboard identifier
        user_id: User id
        """
        pattern = re.compile(r"""
        ^(?P<product>[^.]*)_dashboard
        ://
        (?P<cluster>[^.]*)
        \.
        (?P<dashboard_group>[^.]*)
        /
        (?P<dashboard_id>[^.]*)
        /
        (?P<type>[^.]*)
        /
        bookmark
        /
        (?P<user_id>[^.]*)
        $
        """, re.X)
        result = pattern.match(bookmark_qn)
        return result.groupdict() if result else dict()

    def _parse_table_bookmark_qn(self, bookmark_qn: str) -> Dict:
        """
        Parse bookmark qualifiedName and extract the info
        :param bookmark_qn: Qualified Name of Bookmark entity
        :return: Dictionary object containing following information:
        cluster: cluster information
        db: Database name
        name: Table name
        """
        pattern = re.compile(r"""
        ^(?P<db>[^.]*)
        \.
        (?P<table>[^.]*)
        \.
        (?P<entity_type>[^.]*)
        \.
        (?P<user_id>[^.]*)\.bookmark
        \@
        (?P<cluster>.*)
        $
        """, re.X)
        result = pattern.match(bookmark_qn)
        return result.groupdict() if result else dict()

    @classmethod
    def _filter_active(cls, entities: List[dict]) -> List[dict]:
        """
        Filter out active entities based on entity end relationship status.
        """
        result = [e for e in entities
                  if e.get('relationshipStatus') == AtlasStatus.ACTIVE
                  and e.get('entityStatus') == AtlasStatus.ACTIVE]

        return result

    def _get_table_entity(self, *, table_uri: str) -> AtlasEntityWithExtInfo:
        """
        Fetch information from table_uri and then find the appropriate entity
        :param table_uri: The table URI coming from Amundsen Frontend
        :return: A table entity matching the Qualified Name derived from table_uri
        """
        key = AtlasTableKey(table_uri)

        try:
            return self.client.entity.get_entity_by_attribute(type_name=key.entity_type,
                                                              uniq_attributes=[
                                                                  (AtlasCommonParams.qualified_name,
                                                                   key.qualified_name)])
        except Exception as ex:
            LOGGER.exception(f'Table not found. {str(ex)}')
            raise NotFoundException(f'Table URI( {table_uri} ) does not exist')

    def _get_user_entity(self, user_id: str) -> AtlasEntityWithExtInfo:
        """
        Fetches an user entity from an id
        :param user_id: User ID
        :return: A User entity matching the user_id
        """
        try:
            return self.client.entity.get_entity_by_attribute(type_name=AtlasCommonTypes.user,
                                                              uniq_attributes=[
                                                                  (AtlasCommonParams.qualified_name, user_id)])
        except Exception:
            raise NotFoundException(f'(User {user_id}) does not exist')

    def _create_bookmark(self, entity: AtlasEntityWithExtInfo, user_guid: str, bookmark_qn: str,
                         entity_uri: str) -> None:
        """
        Creates a bookmark entity for a specific user and entity uri.
        :param entity: bookmarked entity
        :param user_guid: User's guid
        :param bookmark_qn: Bookmark qualifiedName
        :param entity_uri: uri of bookmarked entity
        :return:
        """

        bookmark_entity = {
            'entity': {
                'typeName': AtlasCommonTypes.bookmark,
                AtlasCommonParams.attributes: {
                    AtlasCommonParams.qualified_name: bookmark_qn,
                    AtlasStatus.ACTIVE.lower(): True,
                    'entityUri': entity_uri,
                    'entityName': entity.entity[AtlasCommonParams.attributes]['name'],
                    'user': {AtlasCommonParams.guid: user_guid},
                    'entity': {AtlasCommonParams.guid: entity.entity[AtlasCommonParams.guid]}}
            }
        }

        bookmark_entity = type_coerce(bookmark_entity, AtlasEntityWithExtInfo)
        self.client.entity.create_entity(bookmark_entity)

    def _get_bookmark_entity(self, entity_uri: str, user_id: str,
                             resource_type: ResourceType) -> AtlasEntityWithExtInfo:
        """
        Fetch a Bookmark entity from parsing entity uri and user id.
        If Bookmark is not present, create one for the user.
        :param entity_uri:
        :param user_id: Qualified Name of a user
        :return:
        """
        if resource_type == ResourceType.Table:
            entity_info = AtlasTableKey(entity_uri).get_details()

            schema = entity_info.get('schema')
            table = entity_info.get('table')
            database = entity_info.get('database', 'hive_table')
            cluster = entity_info.get('cluster')

            bookmark_qn = f'{schema}.{table}.{database}.{user_id}.bookmark@{cluster}'

        else:
            bookmark_qn = f'{entity_uri}/{resource_type.name.lower()}/bookmark/{user_id}'

        try:
            bookmark_entity = self.client.entity.get_entity_by_attribute(type_name=AtlasCommonTypes.bookmark,
                                                                         uniq_attributes=[
                                                                             (AtlasCommonParams.qualified_name,
                                                                              bookmark_qn)])
        except Exception as ex:
            LOGGER.exception(f'Bookmark not found. {str(ex)}')

            if resource_type == ResourceType.Table:
                bookmarked_entity = self._get_table_entity(table_uri=entity_uri)
            elif resource_type == ResourceType.Dashboard:
                bookmarked_entity = self._get_dashboard(qualified_name=entity_uri)
            else:
                raise NotImplementedError(f'Bookmarks for Resource Type ({resource_type}) are not yet implemented')

            # Fetch user entity from user_id for relation
            user_entity = self._get_user_entity(user_id)
            # Create bookmark entity with the user relation.

            self._create_bookmark(bookmarked_entity,
                                  user_entity.entity[AtlasCommonParams.guid],
                                  bookmark_qn,
                                  entity_uri)
            # Fetch bookmark entity after creating it.
            bookmark_entity = self.client.entity.get_entity_by_attribute(type_name=AtlasCommonTypes.bookmark,
                                                                         uniq_attributes=[
                                                                             (AtlasCommonParams.qualified_name,
                                                                              bookmark_qn)])

        return bookmark_entity

    def _get_column(self, *, table_uri: str, column_name: str) -> Dict:
        """
        Fetch the column information from referredEntities of the table entity
        :param table_uri:
        :param column_name:
        :return: A dictionary containing the column details
        """
        try:
            table_entity = self._get_table_entity(table_uri=table_uri)
            columns = table_entity.entity[AtlasCommonParams.relationships].get('columns')
            for column in columns or list():
                col_details = table_entity.referredEntities[column[AtlasCommonParams.guid]]
                if column_name == col_details[AtlasCommonParams.attributes]['name']:
                    return col_details

            raise NotFoundException(f'Column not found: {column_name}')

        except KeyError as ex:
            LOGGER.exception(f'Column not found: {str(ex)}')
            raise NotFoundException(f'Column not found: {column_name}')

    def _serialize_columns(self, *, entity: AtlasEntityWithExtInfo) -> \
            Union[List[Column], List]:
        """
        Helper function to fetch the columns from entity and serialize them
        using Column and Stat model.
        :param entity: AtlasEntityWithExtInfo object,
        along with relationshipAttributes
        :return: A list of Column objects, if there are any columns available,
        else an empty list.
        """
        columns = list()
        for column in entity.entity[AtlasCommonParams.relationships].get('columns') or list():
            column_status = column.get('entityStatus', 'inactive').lower()

            if column_status != 'active':
                continue

            col_entity = entity.referredEntities[column[AtlasCommonParams.guid]]
            col_attrs = col_entity[AtlasCommonParams.attributes]
            statistics = list()

            badges = list()
            for column_classification in col_entity.get('classifications') or list():
                if column_classification.get('entityStatus') == AtlasStatus.ACTIVE:
                    name = column_classification.get('typeName')

                    badges.append(Badge(badge_name=name, category='default'))

            for stats in col_attrs.get('statistics') or list():
                stats_attrs = stats[AtlasCommonParams.attributes]

                stat_type = stats_attrs.get('stat_name')

                stat_format = self.STATISTICS_FORMAT_SPEC.get(stat_type, dict())

                if not stat_format.get('drop', False):
                    stat_type = stat_format.get('new_name', stat_type)

                    stat_val = stats_attrs.get('stat_val')

                    format_val = stat_format.get('format')

                    if format_val:
                        stat_val = format_val.format(stat_val)
                    else:
                        stat_val = str(stat_val)

                    start_epoch = stats_attrs.get('start_epoch')
                    end_epoch = stats_attrs.get('end_epoch')

                    statistics.append(
                        Stat(
                            stat_type=stat_type,
                            stat_val=stat_val,
                            start_epoch=start_epoch,
                            end_epoch=end_epoch,
                        )
                    )

            columns.append(
                Column(
                    name=col_attrs.get('name'),
                    description=col_attrs.get('description') or col_attrs.get('comment'),
                    col_type=col_attrs.get('type') or col_attrs.get('dataType') or col_attrs.get('data_type'),
                    sort_order=col_attrs.get('position') or 9999,
                    stats=statistics,
                    badges=badges
                )
            )
        return sorted(columns, key=lambda item: item.sort_order)

    def _get_reports(self, guids: List[str]) -> List[ResourceReport]:
        reports = []
        if guids:
            report_entities = self.client.entity.get_entities_by_guids(guids=guids)
            for report_entity in report_entities.entities:
                try:
                    if report_entity.status == AtlasStatus.ACTIVE:
                        report_attrs = report_entity.attributes
                        reports.append(
                            ResourceReport(
                                name=report_attrs['name'],
                                url=report_attrs['url']
                            )
                        )
                except (KeyError, AttributeError):
                    LOGGER.exception(f'Error while accessing table report: {str(report_entity)}', exc_info=True)

        parsed_reports = app.config['RESOURCE_REPORT_CLIENT'](reports) \
            if app.config['RESOURCE_REPORT_CLIENT'] else reports

        return sorted(parsed_reports)

    def _get_owners(self, data_owners: list, fallback_owner: str = None) -> List[User]:
        owners_detail = list()
        active_owners_list = list()

        for owner in self._filter_active(data_owners):
            owner_qn = owner['displayText']
            owner_data = self._get_user_details(owner_qn)
            owners_detail.append(User(**owner_data))
            active_owners_list.append(owner_qn)

        # To avoid the duplication,
        # we are checking if the fallback is not in data_owners
        if fallback_owner and (fallback_owner not in active_owners_list):
            owners_detail.append(User(**self._get_user_details(fallback_owner)))

        return owners_detail

    def get_user(self, *, id: str) -> Union[UserEntity, None]:
        pass

    def create_update_user(self, *, user: User) -> Tuple[User, bool]:
        pass

    def get_users(self) -> List[UserEntity]:
        pass

    def _serialize_badges(self, entity: AtlasEntityWithExtInfo) -> List[Badge]:
        """
        Return list of Badges for entity. Badges in Amundsen <> Atlas integration are based on Atlas Classification.

        :param entity: entity for which badges should be collected
        :return : List of Amundsen Badge objects.
        """
        result = []

        classifications = entity.get('classifications')

        for classification in classifications or list():
            result.append(Badge(badge_name=classification.get('typeName'), category='default'))

        return result

    def _serialize_tags(self, entity: AtlasEntityWithExtInfo) -> List[Tag]:
        """
        Return list of Tags for entity. Tags in Amundsen <> Atlas integration are based on Atlas Glossary.

        :param entity: entity for which tags should be collected
        :return : List of Amundsen Tag objects.
        """
        result = []

        meanings = self._filter_active(entity.get(AtlasCommonParams.relationships, dict()).get('meanings', []))

        for term in meanings or list():
            result.append(Tag(tag_name=term.get('displayText', ''), tag_type='default'))

        return result

    def get_table(self, *, table_uri: str) -> Table:
        """
        Gathers all the information needed for the Table Detail Page.
        :param table_uri:
        :return: A Table object with all the information available
        or gathered from different entities.
        """
        entity = self._get_table_entity(table_uri=table_uri)
        table_details = entity.entity

        try:
            attrs = table_details[AtlasCommonParams.attributes]

            programmatic_descriptions = self._get_programmatic_descriptions(attrs.get('parameters', dict()) or dict())

            table_info = AtlasTableKey(attrs.get(AtlasCommonParams.qualified_name)).get_details()

            badges = self._serialize_badges(table_details)
            tags = self._serialize_tags(table_details)

            columns = self._serialize_columns(entity=entity)

            reports_guids = [report.get("guid") for report in attrs.get("reports") or list()]

            table_type = attrs.get('tableType') or 'table'
            is_view = 'view' in table_type.lower()

            readers = self._get_readers(table_details, Reader)
            application = self._get_application(table_details)

            table = Table(
                table_writer=application,
                database=AtlasTableKey(table_uri).get_details()['database'],
                cluster=table_info.get('cluster', ''),
                schema=table_info.get('schema', ''),
                name=attrs.get('name') or table_info.get('table', ''),
                badges=badges,
                tags=tags,
                description=attrs.get('description') or attrs.get('comment'),
                owners=self._get_owners(
                    table_details[AtlasCommonParams.relationships].get('ownedBy', []), attrs.get('owner')),
                resource_reports=self._get_reports(guids=reports_guids),
                columns=columns,
                is_view=is_view,
                table_readers=readers,
                last_updated_timestamp=self._parse_date(table_details.get('updateTime')),
                programmatic_descriptions=programmatic_descriptions,
                watermarks=self._get_table_watermarks(table_details))

            return table
        except KeyError:
            LOGGER.exception('Error while accessing table information. {}', exc_info=True)
            raise BadRequest(f'Some of the required attributes are missing in: {table_uri}')

    @staticmethod
    def _validate_date(text_date: str, date_format: str) -> Tuple[Optional[datetime.datetime], Optional[str]]:
        try:
            return datetime.datetime.strptime(text_date, date_format), date_format
        except (ValueError, TypeError):
            return None, None

    @staticmethod
    def _select_watermark_format(partition_names: Optional[List[Any]]) -> Optional[str]:
        result = None

        if partition_names:
            for partition_name in partition_names:
                # Assume that all partitions for given table have the same date format. Only thing that needs to be done
                # is establishing which format out of the supported ones it is and then we validate every partition
                # against it.
                for df in app.config['WATERMARK_DATE_FORMATS']:
                    _, result = AtlasProxy._validate_date(partition_name, df)

                    if result:
                        LOGGER.debug('Established date format', extra=dict(date_format=result))
                        return result

        return result

    @staticmethod
    def _render_partition_key_name(entity: AtlasEntityWithExtInfo) -> Optional[str]:
        _partition_keys = []

        for partition_key in entity.get(AtlasCommonParams.attributes, dict()).get('partitionKeys', []):
            partition_key_column_name = partition_key.get('displayName')

            if partition_key_column_name:
                _partition_keys.append(partition_key_column_name)

        partition_key = ' '.join(_partition_keys).strip()

        return partition_key

    def _get_table_watermarks(self, entity: AtlasEntityWithExtInfo) -> List[Watermark]:
        partition_value_format = '%Y-%m-%d %H:%M:%S'

        _partitions = entity.get(AtlasCommonParams.relationships, dict()).get('partitions', list())

        names = [_partition.get('displayText') for _partition in self._filter_active(_partitions)]

        if not names:
            return []

        partition_key = self._render_partition_key_name(entity)
        watermark_date_format = self._select_watermark_format(names)

        partitions = {}

        for _partition in _partitions:
            partition_name = _partition.get('displayText')
            if partition_name and watermark_date_format:
                partition_date, _ = self._validate_date(partition_name, watermark_date_format)

                if partition_date:
                    common_values = {'partition_value': datetime.datetime.strftime(partition_date,
                                                                                   partition_value_format),
                                     'create_time': 0,
                                     'partition_key': partition_key}

                    partitions[partition_date] = common_values

        if partitions:
            low_watermark_date = min(partitions.keys())
            high_watermark_date = max(partitions.keys())

            low_watermark = Watermark(watermark_type='low_watermark', **partitions.get(low_watermark_date))
            high_watermark = Watermark(watermark_type='high_watermark', **partitions.get(high_watermark_date))

            return [low_watermark, high_watermark]
        else:
            return []

    def delete_owner(self, *, table_uri: str, owner: str) -> None:
        """
        :param table_uri:
        :param owner:
        :return:
        """
        table = self._get_table_entity(table_uri=table_uri)
        table_entity = table.entity

        if table_entity[AtlasCommonParams.relationships].get("ownedBy"):
            try:
                active_owner = next(filter(lambda item:
                                           item['relationshipStatus'] == AtlasStatus.ACTIVE
                                           and item['displayText'] == owner,
                                           table_entity[AtlasCommonParams.relationships]['ownedBy']), None)

                if active_owner:
                    self.client.relationship.delete_relationship_by_guid(
                        guid=active_owner.get('relationshipGuid')
                    )
                else:
                    raise BadRequest('You can not delete this owner.')
            except Exception:
                LOGGER.exception('Error while removing table data owner.', exc_info=True)

    def add_owner(self, *, table_uri: str, owner: str) -> None:
        """
        Query on Atlas User entity to find if the entity exist for the
        owner string in parameter, if not create one. And then use that User
        entity's GUID and add a relationship between Table and User, on ownedBy field.
        :param table_uri:
        :param owner: Email address of the owner
        :return: None, as it simply adds the owner.
        """
        owner_info = self._get_user_details(owner)

        if not owner_info:
            raise NotFoundException(f'User "{owner}" does not exist.')

        user_dict = type_coerce({
            "entity": {
                "typeName": "User",
                "attributes": {"qualifiedName": owner},
            }
        }, AtlasEntityWithExtInfo)

        # Get or Create a User
        user_entity = self.client.entity.create_entity(user_dict)
        user_guid = next(iter(user_entity.guidAssignments.values()))

        table = self._get_table_entity(table_uri=table_uri)

        entity_def = {
            "typeName": "DataSet_Users_Owner",
            "end1": {
                "guid": table.entity.get("guid"), "typeName": "Table",
            },
            "end2": {
                "guid": user_guid, "typeName": "User",
            },
        }
        try:
            relationship = type_coerce(entity_def, AtlasRelationship)
            self.client.relationship.create_relationship(relationship=relationship)

        except Exception:
            LOGGER.exception('Error while adding the owner information. {}', exc_info=True)
            raise BadRequest(f'User {owner} is already added as a data owner for table {table_uri}.')

    def get_table_description(self, *,
                              table_uri: str) -> Union[str, None]:
        """
        :param table_uri:
        :return: The description of the table as a string
        """
        entity = self._get_table_entity(table_uri=table_uri)
        return entity.entity[AtlasCommonParams.attributes].get('description')

    def put_table_description(self, *,
                              table_uri: str,
                              description: str) -> None:
        """
        Update the description of the given table.
        :param table_uri:
        :param description: Description string
        :return: None
        """
        table = self._get_table_entity(table_uri=table_uri)

        self.client.entity.partial_update_entity_by_guid(
            entity_guid=table.entity.get("guid"), attr_value=description, attr_name='description'
        )

    @_CACHE.cache('_get_user_defined_glossary_guid')
    def _get_user_defined_glossary_guid(self) -> str:
        """
        This function look for a user defined glossary i.e., self.ATLAS_USER_DEFINED_TERMS
        If there is not one available, this will create a new glossary.
        The main reason to put this functionality into a separate function is to avoid
        the lookup each time someone assigns a tag to a data source.
        :return: Glossary object, that holds the user defined terms.
        """
        # Check if the user glossary already exists
        glossaries = self.client.glossary.get_all_glossaries()
        for glossary in glossaries:
            if glossary.get(AtlasCommonParams.qualified_name) == self.AMUNDSEN_USER_TAGS:
                return glossary[AtlasCommonParams.guid]

        # If not already exists, create one
        glossary_def = AtlasGlossary({"name": self.AMUNDSEN_USER_TAGS,
                                      "shortDescription": "Amundsen User Defined Terms"})
        glossary = self.client.glossary.create_glossary(glossary_def)
        return glossary.guid

    @_CACHE.cache('_get_create_glossary_term')
    def _get_create_glossary_term(self, term_name: str) -> Union[AtlasGlossaryTerm, AtlasEntityHeader]:
        """
        Since Atlas does not provide any API to find a term directly by a qualified name,
        we need to look for AtlasGlossaryTerm via basic search, if found then return, else
        create a new glossary term under the user defined glossary.
        :param term_name: Name of the term. NOTE: this is different from qualified name.
        :return: Term Object.
        """
        params = {
            'typeName': "AtlasGlossaryTerm",
            'excludeDeletedEntities': True,
            'includeSubTypes': True,
            AtlasCommonParams.attributes: ["assignedEntities", ],
            'entityFilters': {'condition': "AND",
                              'criterion': [{'attributeName': "name", 'operator': "=", 'attributeValue': term_name}]
                              }
        }
        result = self.client.discovery.faceted_search(search_parameters=params)
        if result.approximateCount:
            term = result.entities[0]
        else:
            glossary_guid = self._get_user_defined_glossary_guid()
            glossary_def = AtlasGlossaryHeader({'glossaryGuid': glossary_guid})
            term_def = AtlasGlossaryTerm({'name': term_name, 'anchor': glossary_def})
            term = self.client.glossary.create_glossary_term(term_def)

        return term

    def add_tag(self, *, id: str, tag: str, tag_type: str = "default",
                resource_type: ResourceType = ResourceType.Table) -> None:
        """
        Assign the Glossary Term to the give table. If the term is not there, it will
        create a new term under the Glossary self.ATLAS_USER_DEFINED_TERMS
        :param id: Table URI / Dashboard ID etc.
        :param tag: Tag Name
        :param tag_type
        :return: None
        """
        entity = self._get_table_entity(table_uri=id)

        term = self._get_create_glossary_term(tag)
        related_entity = AtlasRelatedObjectId({AtlasCommonParams.guid: entity.entity[AtlasCommonParams.guid],
                                               "typeName": resource_type.name})
        self.client.glossary.assign_term_to_entities(term.guid, [related_entity])

    def add_badge(self, *, id: str, badge_name: str, category: str = '',
                  resource_type: ResourceType) -> None:
        # Not implemented
        raise NotImplementedError

    def delete_tag(self, *, id: str, tag: str, tag_type: str,
                   resource_type: ResourceType = ResourceType.Table) -> None:
        """
        Removes the Glossary Term assignment from the provided source.
        :param id: Table URI / Dashboard ID etc.
        :param tag: Tag Name
        :return:None
        """
        entity = self._get_table_entity(table_uri=id)
        term = self._get_create_glossary_term(tag)

        if not term:
            return

        assigned_entities = self.client.glossary.get_entities_assigned_with_term(term.guid, "ASC", -1, 0)

        for item in assigned_entities or list():
            if item.get(AtlasCommonParams.guid) == entity.entity[AtlasCommonParams.guid]:
                related_entity = AtlasRelatedObjectId(item)
                return self.client.glossary.disassociate_term_from_entities(term.guid, [related_entity])

    def delete_badge(self, *, id: str, badge_name: str, category: str,
                     resource_type: ResourceType) -> None:
        # Not implemented
        raise NotImplementedError

    def put_column_description(self, *,
                               table_uri: str,
                               column_name: str,
                               description: str) -> None:
        """
        :param table_uri:
        :param column_name: Name of the column to update the description
        :param description: The description string
        :return: None, as it simply updates the description of a column
        """
        column_detail = self._get_column(
            table_uri=table_uri,
            column_name=column_name)
        col_guid = column_detail[AtlasCommonParams.guid]

        self.client.entity.partial_update_entity_by_guid(
            entity_guid=col_guid, attr_value=description, attr_name='description'
        )

    def get_column_description(self, *,
                               table_uri: str,
                               column_name: str) -> Union[str, None]:
        """
        :param table_uri:
        :param column_name:
        :return: The column description using the referredEntities
        information of a table entity
        """
        column_detail = self._get_column(
            table_uri=table_uri,
            column_name=column_name)
        return column_detail[AtlasCommonParams.attributes].get('description')

    def _serialize_popular_tables(self, entities: AtlasEntitiesWithExtInfo) -> List[PopularTable]:
        """
        Gets a list of entities and serialize the popular tables.
        :param entities: List of entities from atlas client
        :return: a list of PopularTable objects
        """
        popular_tables = list()

        for table in entities.entities:
            table_attrs = table.attributes

            table_info = AtlasTableKey(table_attrs.get(AtlasCommonParams.qualified_name)).get_details()

            table_name = table_info.get('table') or table_attrs.get('name')
            schema_name = table_info.get('schema', '')
            db_cluster = table_info.get('cluster', '')

            popular_table = PopularTable(
                database=table_info.get('database') or table.typeName,
                cluster=db_cluster,
                schema=schema_name,
                name=table_name,
                description=table_attrs.get('description') or table_attrs.get('comment'))
            popular_tables.append(popular_table)

        return popular_tables

    def get_popular_tables(self, *,
                           num_entries: int,
                           user_id: Optional[str] = None) -> List[PopularTable]:
        """
        Generates a list of Popular tables to be shown on the home page of Amundsen.
        :param num_entries: Number of popular tables to fetch
        :return: A List of popular tables instances
        """
        popular_query_params = {'typeName': AtlasTableTypes.table,
                                'sortBy': 'popularityScore',
                                'sortOrder': 'DESCENDING',
                                'excludeDeletedEntities': True,
                                'limit': num_entries}
        search_results = self.client.discovery.faceted_search(search_parameters=popular_query_params)

        return self._serialize_popular_tables(search_results)

    def get_latest_updated_ts(self) -> int:
        date = None

        metrics = self.client.admin.get_metrics()
        try:
            date = self._parse_date(metrics.general.get('stats', {}).get('Notification:lastMessageProcessedTime'))
        except AttributeError:
            pass

        return date or 0

    def get_statistics(self) -> Dict[str, Any]:
        # Not implemented
        pass

    def get_tags(self) -> List:
        """
        Fetch all the glossary terms from atlas, along with their assigned entities as this
        will be used to generate the autocomplete on the table detail page
        :return: A list of TagDetail Objects
        """
        tags = []
        params = {
            'typeName': "AtlasGlossaryTerm",
            'limit': 1000,
            'offset': 0,
            'excludeDeletedEntities': True,
            'includeSubTypes': True,
            AtlasCommonParams.attributes: ["assignedEntities", ]
        }
        glossary_terms = self.client.discovery.faceted_search(search_parameters=params)
        for item in glossary_terms.entities or list():
            tags.append(
                TagDetail(
                    tag_name=item.attributes.get("name"),
                    tag_count=len(item.attributes.get("assignedEntities"))
                )
            )
        return tags

    def get_badges(self) -> List:
        badges = list()

        metrics = self.client.admin.get_metrics()
        try:
            system_badges = metrics["tag"].get("tagEntities").keys()

            for item in system_badges:
                badges.append(
                    Badge(badge_name=item, category="default")
                )
        except AttributeError:
            LOGGER.info("No badges/classifications available in the system.")

        return badges

    def _get_resources_followed_by_user(self, user_id: str, resource_type: str) \
            -> List[Union[PopularTable, DashboardSummary]]:
        """
        Helper function to get the resource, table, dashboard etc followed by a user.
        :param user_id: User ID of a user
        :param resource_type: Type of a resource that returns, could be table, dashboard etc.
        :return: A list of PopularTable, DashboardSummary or any other resource.
        """

        if resource_type == ResourceType.Table.name:
            bookmark_qn_search_pattern = f'_{resource_type.lower()}.{user_id}.bookmark'
        else:
            bookmark_qn_search_pattern = f'/{resource_type.lower()}/bookmark/{user_id}'

        params = {
            'typeName': AtlasCommonTypes.bookmark,
            'offset': '0',
            'limit': '1000',
            'excludeDeletedEntities': True,
            'entityFilters': {
                'condition': 'AND',
                'criterion': [
                    {
                        'attributeName': AtlasCommonParams.qualified_name,
                        'operator': 'contains',
                        'attributeValue': bookmark_qn_search_pattern
                    },
                    {
                        'attributeName': AtlasStatus.ACTIVE.lower(),
                        'operator': 'eq',
                        'attributeValue': 'true'
                    }
                ]
            },
            AtlasCommonParams.attributes: ['count', AtlasCommonParams.qualified_name,
                                           AtlasCommonParams.uri, 'entityName']
        }
        # Fetches the bookmark entities based on filters
        search_results = self.client.discovery.faceted_search(search_parameters=params)

        resources: List[Union[PopularTable, DashboardSummary]] = []
        for record in search_results.entities or []:
            if resource_type == ResourceType.Table.name:
                table_info = AtlasTableKey(record.attributes[AtlasCommonParams.uri]).get_details()
                res = self._parse_table_bookmark_qn(record.attributes[AtlasCommonParams.qualified_name])
                resources.append(PopularTable(
                    database=table_info['database'],
                    cluster=res['cluster'],
                    schema=res['db'],
                    name=res['table']))
            elif resource_type == ResourceType.Dashboard.name:
                dashboard_info = self._parse_dashboard_bookmark_qn(record.attributes[AtlasCommonParams.qualified_name])
                resources.append(DashboardSummary(
                    uri=record.attributes[AtlasCommonParams.uri],
                    cluster=dashboard_info['cluster'],
                    name=record.attributes['entityName'],
                    group_name=dashboard_info['dashboard_group'],
                    group_url='',
                    product=dashboard_info['product'],
                    url=''
                ))
            else:
                raise NotImplementedError(f'resource type {resource_type} is not supported')
        return resources

    def _get_resources_owned_by_user(self, user_id: str, resource_type: str) \
            -> List[Union[PopularTable, DashboardSummary, Any]]:
        """
        Helper function to get the resource, table, dashboard etc owned by a user.

        :param user_id: User ID of a user
        :param resource_type: Type of a resource that returns, could be table, dashboard etc.
        :return: A list of PopularTable, DashboardSummary or any other resource.
        """
        resources: List[Union[PopularTable, DashboardSummary, Any]] = list()

        if resource_type == ResourceType.Table.name:
            type_regex = "(.*)_table$"
            entity_type = AtlasTableTypes.table
            serialize_function = self._serialize_popular_tables
        elif resource_type == ResourceType.Dashboard.name:
            type_regex = 'Dashboard'
            entity_type = AtlasDashboardTypes.metadata
            serialize_function = self._serialize_dashboard_summaries
        else:
            raise NotImplementedError(f'Resource Type ({resource_type}) is not yet implemented')

        user_entity = self.client.entity.get_entity_by_attribute(type_name=AtlasCommonTypes.user,
                                                                 uniq_attributes=[
                                                                     (
                                                                         AtlasCommonParams.qualified_name,
                                                                         user_id)]).entity

        if not user_entity:
            raise NotFoundException(f'User {user_id} not found.')

        resource_guids = set()
        for item in self._filter_active(user_entity[AtlasCommonParams.relationships].get('owns')) or list():
            if re.compile(type_regex).match(item['typeName']):
                resource_guids.add(item[AtlasCommonParams.guid])

        owned_resources_query = f'{entity_type} where owner like "{user_id.lower()}*" and __state = "ACTIVE"'
        entities = self.client.discovery.dsl_search(owned_resources_query)

        for entity in entities.entities or list():
            resource_guids.add(entity.guid)

        if resource_guids:
            resource_guids_chunks = AtlasProxy.split_list_to_chunks(list(resource_guids), 100)

            for chunk in resource_guids_chunks:
                entities = self.client.entity.get_entities_by_guids(guids=list(chunk), ignore_relationships=True)

                resources += serialize_function(entities)
        else:
            LOGGER.info(f'User ({user_id}) does not own any "{resource_type}"')

        return resources

    @staticmethod
    def split_list_to_chunks(input_list: List[Any], n: int) -> Generator:
        """Yield successive n-sized chunks from lst."""
        for i in range(0, len(input_list), n):
            yield input_list[i:i + n]

    def _get_resource_by_user_relation(self, user_email: str, relation_type: UserResourceRel,
                                       resource_type: ResourceType) -> Dict[str, Any]:
        resources: List[Union[PopularTable, DashboardSummary]] = list()

        if resource_type.name == ResourceType.Table.name:
            resource = ResourceType.Table.name.lower()
        elif resource_type.name == ResourceType.Dashboard.name:
            resource = ResourceType.Dashboard.name.lower()
        else:
            raise NotImplementedError(f'Resource type {resource_type.name} not supported.')

        if relation_type == UserResourceRel.follow:
            resources = self._get_resources_followed_by_user(user_id=user_email,
                                                             resource_type=resource_type.name)
        elif relation_type == UserResourceRel.own:
            resources = self._get_resources_owned_by_user(user_id=user_email,
                                                          resource_type=resource_type.name)

        return {resource: resources}

    def get_dashboard_by_user_relation(self, *, user_email: str, relation_type: UserResourceRel) -> Dict[str, Any]:
        return self._get_resource_by_user_relation(user_email, relation_type, ResourceType.Dashboard)

    def get_table_by_user_relation(self, *, user_email: str, relation_type: UserResourceRel) -> Dict[str, Any]:
        return self._get_resource_by_user_relation(user_email, relation_type, ResourceType.Table)

    def get_frequently_used_tables(self, *, user_email: str) -> Dict[str, List[PopularTable]]:
        user = self.client.entity.get_entity_by_attribute(type_name=AtlasCommonTypes.user,
                                                          uniq_attributes=[
                                                              (AtlasCommonParams.qualified_name, user_email)]).entity

        readers_guids = []
        for user_reads in self._filter_active(user[AtlasCommonParams.relationships].get('entityReads')):
            readers_guids.append(user_reads.get(AtlasCommonParams.guid))

        readers = self.client.entity.get_entities_by_guids(guids=list(readers_guids), ignore_relationships=True)

        _results = {}
        for reader in readers.entities or list():
            entity_uri = reader.attributes.get(AtlasCommonParams.uri)
            count = reader.attributes.get('count')

            if count:
                table_info = AtlasTableKey(entity_uri).get_details()

                _results[count] = dict(cluster=table_info.get('cluster'),
                                       name=table_info.get('table'),
                                       schema=table_info.get('schema'),
                                       database=table_info.get('database'))

        sorted_counts = sorted(_results.keys())

        results = []
        for count in sorted_counts:
            data: dict = _results.get(count, dict())
            table = PopularTable(**data)

            results.append(table)

        return {'table': results}

    def add_resource_relation_by_user(self, *,
                                      id: str,
                                      user_id: str,
                                      relation_type: UserResourceRel,
                                      resource_type: ResourceType) -> None:

        if resource_type not in [ResourceType.Table, ResourceType.Dashboard]:
            raise NotImplementedError(f'resource type {resource_type} is not supported')

        entity = self._get_bookmark_entity(entity_uri=id, user_id=user_id, resource_type=resource_type)  # type: ignore
        entity.entity[AtlasCommonParams.attributes][AtlasStatus.ACTIVE.lower()] = True
        self.client.entity.update_entity(entity)

    def delete_resource_relation_by_user(self, *,
                                         id: str,
                                         user_id: str,
                                         relation_type: UserResourceRel,
                                         resource_type: ResourceType) -> None:
        if resource_type not in [ResourceType.Table, ResourceType.Dashboard]:
            raise NotImplementedError(f'resource type {resource_type} is not supported')

        entity = self._get_bookmark_entity(entity_uri=id, user_id=user_id, resource_type=resource_type)  # type: ignore
        entity.entity[AtlasCommonParams.attributes][AtlasStatus.ACTIVE.lower()] = False
        self.client.entity.update_entity(entity)

    def _parse_date(self, date: int) -> Optional[int]:
        try:
            date_str = str(date)
            date_trimmed = date_str[:10]

            assert len(date_trimmed) == 10

            return int(date_trimmed)
        except Exception:
            return None

    def _get_readers(self, entity: AtlasEntityWithExtInfo, model: Any = Reader, top: Optional[int] = 15) \
            -> List[Union[Reader, User]]:
        _readers = entity.get(AtlasCommonParams.relationships, dict()).get('readers', list())

        guids = [_reader.get(AtlasCommonParams.guid) for _reader in self._filter_active(_readers)]

        if not guids:
            return []

        readers = self.client.entity.get_entities_by_guids(guids=list(guids), ignore_relationships=False)

        _result = []

        for _reader in readers.entities or list():
            read_count = _reader.attributes['count']

            if read_count >= int(app.config['POPULAR_RESOURCES_MINIMUM_READER_COUNT']):
                reader_qn = _reader.relationshipAttributes['user']['displayText']
                reader_details = self._get_user_details(reader_qn)

                if model == Reader:
                    reader = Reader(user=User(**reader_details), read_count=read_count)
                elif model == User:
                    reader = User(**reader_details)
                else:
                    return []

                _result.append(reader)

        if model == Reader:
            result = sorted(_result, key=attrgetter('read_count'), reverse=True)[:top]
        else:
            result = _result

        result = result[:top]

        return result

    def _get_application(self, entity: AtlasEntityWithExtInfo) -> Optional[Application]:
        _applications = entity.get(AtlasCommonParams.relationships, dict()).get('applications', list())

        guids = [a.get(AtlasCommonParams.guid) for a in self._filter_active(_applications)]

        if not guids:
            return None

        applications = self.client.entity.get_entities_by_guids(guids=list(guids), ignore_relationships=False)

        for _app in applications.entities or list():
            url = _app.attributes.get('application_url', '')
            description = _app.attributes.get('description', '')
            id = _app.attributes.get('id', '')
            name = _app.attributes.get('name', '')

            app = Application(application_url=url, description=description, id=id, name=name)

            # only single app per table is supported
            break

        return app

    def _get_programmatic_descriptions(self, parameters: dict) -> List[ProgrammaticDescription]:
        programmatic_descriptions: Dict[str, ProgrammaticDescription] = {}

        for source, text in parameters.items():
            use_parameter = True

            for regex_filter in app.config['PROGRAMMATIC_DESCRIPTIONS_EXCLUDE_FILTERS']:
                pattern = re.compile(regex_filter)

                if pattern.match(source):
                    use_parameter = False
                    break

            if use_parameter:
                source = re.sub("([a-z])([A-Z])", "\g<1> \g<2>", source).lower()
                programmatic_descriptions[source] = ProgrammaticDescription(source=source, text=text)

        result = dict(sorted(programmatic_descriptions.items()))

        return list(result.values())

    def _serialize_dashboard_queries(self, queries: List[Dict]) -> List[DashboardQuery]:
        """
        Renders DashboardQuery from attributes

        :param queries: list of dicts with query attributes
        :returns List of DashboardQuery objects.
        """
        result = []

        for query in queries:
            name = query.get('name', '')
            query_text = query.get('queryText', '')
            url = query.get('url', '')

            dashboard_query = DashboardQuery(name=name, query_text=query_text, url=url)

            result.append(dashboard_query)

        return result

    def _get_dashboard_group(self, group_guid: str) -> AtlasEntityWithExtInfo:
        """
        Return raw DashboardGroup entity.

        :param group_guid: guid of dashboard group entity.
        :return : Atlas DashboardGroup entity.
        """
        entity = self.client.entity.get_entities_by_guids(guids=[group_guid]).entities[0]

        return entity

    def _get_dashboard_summary(self, entity: AtlasEntityWithExtInfo, executions: List[AtlasEntity]) -> Dict:
        attributes = entity.entity[AtlasCommonParams.attributes]
        relationships = entity.entity[AtlasCommonParams.relationships]

        group = self._get_dashboard_group(relationships.get('group').get(AtlasCommonParams.guid))[
            AtlasCommonParams.attributes]

        successful_executions = [e for e in executions if e.get('state') == 'succeeded']

        try:
            last_successful_execution = successful_executions[0]
        except IndexError:
            last_successful_execution = dict(timestamp=0)

        chart_names = [e[AtlasCommonParams.attributes]['name'] for _, e in entity['referredEntities'].items()
                       if e['typeName'] == AtlasDashboardTypes.chart]

        result = dict(
            uri=attributes.get(AtlasCommonParams.qualified_name, ''),
            cluster=attributes.get('cluster', ''),
            group_name=relationships.get('group', dict()).get('displayText', ''),
            group_url=group.get('url', ''),
            product=attributes.get('product', ''),
            name=attributes.get('name', ''),
            url=attributes.get('url', ''),
            last_successful_run_timestamp=last_successful_execution.get('timestamp', 0),
            description=attributes.get('description', ''),
            chart_names=chart_names)

        return result

    def _get_dashboard_details(self, entity: AtlasEntityWithExtInfo) -> Dict:
        try:
            attributes = entity.entity[AtlasCommonParams.attributes]
            relationships = entity.entity[AtlasCommonParams.relationships]

            referred_entities = entity['referredEntities']

            badges = self._serialize_badges(entity)
            tags = self._serialize_tags(entity)

            _executions = []
            _queries = []

            for k, v in referred_entities.items():
                entity_type = v.get('typeName')

                _attributes = v[AtlasCommonParams.attributes]

                if entity_type == AtlasDashboardTypes.execution:
                    _executions.append(_attributes)
                elif entity_type == AtlasDashboardTypes.query:
                    _queries.append(_attributes)

            queries = self._serialize_dashboard_queries(_queries)
            query_names = [q.name for q in queries]

            table_guids = [t.get(AtlasCommonParams.guid) for t in self._filter_active(relationships.get('tables', []))]

            if table_guids:
                _tables = self.client.entity.get_entities_by_guids(guids=table_guids)
                tables = self._serialize_popular_tables(_tables)
            else:
                tables = []

            executions_attributes = sorted(_executions, key=lambda x: x.get('timestamp', 0), reverse=True)

            try:
                last_execution = executions_attributes[0]
            except IndexError:
                last_execution = dict(timestamp=0, state='Unknown')

            owners = self._get_owners(relationships.get('ownedBy', []))
            readers = self._get_readers(entity.entity, User)

            result = self._get_dashboard_summary(entity, executions_attributes)

            extra_spec = dict(
                created_timestamp=attributes.get('createdTimestamp', 0),
                updated_timestamp=attributes.get('lastModifiedTimestamp', 0),
                owners=owners,
                last_run_timestamp=last_execution.get('timestamp', 0),
                last_run_state=last_execution.get('state', 'Unknown'),
                query_names=query_names,
                queries=queries,
                tables=tables,
                tags=tags,
                badges=badges,
                recent_view_count=attributes.get('popularityScore', 0),
                frequent_users=readers)

            result.update(extra_spec)

            return result
        except Exception as e:
            raise e

    def _get_dashboard(self, qualified_name: str) -> AtlasEntityWithExtInfo:
        """
        Return raw Dasboard entity.

        :param qualified_name: qualified name of the dashboard
        :return : Atlas Dashboard entity.
        """
        entity = self.client.entity.get_entity_by_attribute(type_name=AtlasDashboardTypes.metadata,
                                                            uniq_attributes=[
                                                                (AtlasCommonParams.qualified_name, qualified_name)])

        return entity

    def get_dashboard(self, id: str) -> DashboardDetailEntity:
        entity = self._get_dashboard(id)

        attributes = self._get_dashboard_details(entity)

        return DashboardDetailEntity(**attributes)

    def get_dashboard_description(self, *, id: str) -> Description:
        """
        Return dashboard description.

        :param id:
        :return: The description of the dashboard as a string
        """
        entity = self.client.entity.get_entity_by_attribute(type_name=AtlasDashboardTypes.metadata,
                                                            uniq_attributes=[(AtlasCommonParams.qualified_name, id)])

        return entity.entity[AtlasCommonParams.attributes].get('description')

    def put_dashboard_description(self, *,
                                  id: str,
                                  description: str) -> None:
        """
        Update the description of the given dashboard.

        :param id: dashboard id (uri)
        :param description: Description string
        :return: None
        """
        entity = self.client.entity.get_entity_by_attribute(type_name=AtlasDashboardTypes.metadata,
                                                            uniq_attributes=[(AtlasCommonParams.qualified_name, id)])

        self.client.entity.partial_update_entity_by_guid(
            entity_guid=entity.entity.get(AtlasCommonParams.guid), attr_value=description, attr_name='description'
        )

    def _serialize_dashboard_summaries(self, entities: AtlasEntitiesWithExtInfo) -> List[DashboardSummary]:
        """
        Returns dashboards summary for dashboards using specific table.

        """
        result = []

        for _dashboard in entities.entities:
            try:
                if _dashboard.status == AtlasStatus.ACTIVE:
                    executions = [
                        entities['referredEntities'].get(e.get(AtlasCommonParams.guid))[AtlasCommonParams.attributes]
                        for e in
                        self._filter_active(
                            _dashboard[AtlasCommonParams.relationships].get('executions', []))]

                    dashboard = AtlasEntityWithExtInfo(attrs=dict(entity=_dashboard, referredEntities={}))

                    summary = DashboardSummary(**self._get_dashboard_summary(dashboard, executions))

                    result.append(summary)
            except (KeyError, AttributeError):
                LOGGER.exception(f'Error while accessing table report: {str(dashboard)}.', exc_info=True)

        return result

    def get_resources_using_table(self, *,
                                  id: str,
                                  resource_type: ResourceType) -> Dict[str, List[DashboardSummary]]:
        if resource_type == ResourceType.Dashboard:
            resource = 'dashboards'
            serialize_function = self._serialize_dashboard_summaries
        else:
            raise NotImplementedError(f'{resource_type} is not supported')

        table = self._get_table_entity(table_uri=id)

        guids = [d.get(AtlasCommonParams.guid) for d in
                 self._filter_active(table.entity[AtlasCommonParams.relationships].get(resource, []))]

        if guids:
            entities = self.client.entity.get_entities_by_guids(guids=guids)
            result = serialize_function(entities)
        else:
            result = []

        return {resource: result}

    @classmethod
    def _generate_edges(cls, graph: Dict[str, List[str]]) -> List[Tuple[str, str]]:
        """
        Generates list of edge pairs from the graph.

        :param graph: Graph of nodes
        :return: List of tuples with graph edges
        """
        edges = []

        # for each node in graph
        for node in graph:
            # for each neighbour node of a single node
            for neighbour in graph[node]:
                # if edge exists then append
                edges.append((node, neighbour))
        return edges

    @classmethod
    def _find_shortest_path(cls, graph: Dict[str, List[str]], start: str, end: str, path: List[Any] = []) -> List[str]:
        """
        Find shortest path between graph nodes. Used to calculate 'level' parameter

        __source__='https://www.python.org/doc/essays/graphs/'
        __author__='Guido van Rossum'

        :param graph: Dictionary of str (node key) and List[str] (connected nodes)
        :param start: Starting node for finding the path
        :param end: Ending node for finding the path
        :param path: Accumulator for recursive calls
        :return: Shortest path between start and end nodes
        """
        path = path + [start]

        if start == end:
            return path
        if not graph.get(start):
            return []
        shortest: List[str] = []
        for node in graph[start]:
            if node not in path:
                newpath = AtlasProxy._find_shortest_path(graph, node, end, path)
                if newpath:
                    if not shortest or len(newpath) < len(shortest):
                        shortest = newpath

        return shortest

    @staticmethod
    def _find_parent_nodes(graph: Dict) -> Dict[str, Set[str]]:
        """
        Rewrite graph dict to the form that makes it possible to easily

        :param graph: Dictionary of str (node key) and List[str]
        :return: Dict with keys (node) and values (parents of a node)
        """
        relations: Dict[str, Set[str]] = {}

        for parent, ancestors in graph.items():
            for ancestor in ancestors:
                if not relations.get(ancestor):
                    relations[ancestor] = set()

                relations[ancestor].add(parent)

        return relations

    def _get_lineage_graph(self, lineage: Dict, entity_type: str, key_class: Any) -> Dict[str, List[str]]:
        """
        Since Atlas bases lineage on additional entity (Process(input=A, output=B)) for capturing lineage
        we need to create graph that has direct A > B relationships and removes Process entities.

        :param lineage: Raw linage captured from Atlas
        :param entity_type: Type of entity for which lineage is captured
        :param key_class: Helper class used for Amundsen key <> Atlas qualified name serialization/deserialization
        :return: Graph of nodes with relations.
        """
        processes: Dict[str, Dict[str, Any]] = dict()

        entity_type = entity_type.lower()
        entities = lineage.get('guidEntityMap', dict())
        relations = lineage.get('relations', [])

        for relation in relations:
            input_guid = relation['fromEntityId']
            input_type = entities.get(input_guid)['typeName'].lower()

            output_guid = relation['toEntityId']
            output_type = entities.get(output_guid)['typeName'].lower()

            if input_type.endswith('process') and output_type.endswith(entity_type):
                output_qn = entities.get(output_guid)[AtlasCommonParams.attributes][AtlasCommonParams.qualified_name]
                output_key = key_class(output_qn, output_type).amundsen_key  # type: ignore

                if not processes.get(input_guid):
                    processes[input_guid] = dict(inputs=set(), outputs=set())

                processes[input_guid]['outputs'].add(output_key)

            elif output_type.endswith('process') and input_type.endswith(entity_type):
                input_qn = entities.get(input_guid)[AtlasCommonParams.attributes][AtlasCommonParams.qualified_name]
                input_key = key_class(input_qn, input_type).amundsen_key  # type: ignore

                if not processes.get(output_guid):
                    processes[output_guid] = dict(inputs=set(), outputs=set())

                processes[output_guid]['inputs'].add(input_key)

        graph: Dict[str, List[str]] = defaultdict(list)

        for _, spec in processes.items():
            for input_key in spec['inputs']:
                for output_key in spec['outputs']:
                    graph[input_key].append(output_key)

        return dict(graph)

    def _serialize_lineage_item(self, edge: Tuple[str, str], direction: str, key_class: Any,
                                graph: Dict, root_node: str, parent_nodes: Dict[str, Set[str]]) -> List[LineageItem]:
        """
        Serializes LineageItem object.

        :param edge: tuple containing two node keys that are connected with each other.
        :param direction: Lineage direction upstream/downstream
        :param key_class: Helper class used for managing Atlas <> Amundsen key formats.
        :param: graph: Graph from which the edge was derived from. Used to find distance between edge node and entity
        for which lineage is retrieved.
        :param parent_nodes: Dict of keys (nodes) with set of keys (parents).
        :return: Serialized LineageItem list.
        """
        result: List[LineageItem] = []

        if direction == 'upstream':
            key, _ = edge
            level = len(AtlasProxy._find_shortest_path(graph, key, root_node)) - 1
        elif direction == 'downstream':
            _, key = edge
            level = len(AtlasProxy._find_shortest_path(graph, root_node, key)) - 1
        else:
            raise ValueError(f'Direction {direction} not supported!')

        parents = parent_nodes.get(key, [''])

        while True:
            try:
                parent = parents.pop()
            except Exception:
                break

            badges: List[str] = []
            usage = 0
            source = key_class(key).get_details()['database']

            spec = dict(key=key,
                        parent=parent,
                        source=source,
                        badges=badges,
                        usage=usage,
                        level=level)

            result.append(LineageItem(**spec))

        return result

    def _serialize_lineage(self, lineage: dict, entity_type: str, root_node: str, direction: str,
                           key_class: Union[Type[AtlasTableKey], Type[AtlasColumnKey]]) -> List[LineageItem]:
        """
        Serializes lineage to Amundsen format based on Atlas lineage output.

        The assumption for Atlas <> Amundsen lineage is that every Process entity in Atlas lineage contains at least
        one entity of entity_type both in inputs and outputs.

        If your lineage is A > B > C where:
            A - is table
            B - is file
            C - is table
        It won't render A > C table lineage in Amundsen.

        The implementation follows simplified set of expectations and might be subject of change if such requirement
        arises.

        :param lineage: Raw lineage from Atlas
        :param entity_type: Type of the entity for which lineage is being retrieved
        :param root_node: key of entity for which lineage will be rendered. Required to calculate 'level' dynamically
        based on nodes distance.
        :param direction: upstream/downstream
        :param key_class: Class for serializing entities keys
        :return: The Lineage object with upstream & downstream lineage items
        """
        result: List[LineageItem] = []

        graph = self._get_lineage_graph(lineage, entity_type, key_class)
        edges = AtlasProxy._generate_edges(graph)
        parent_nodes = self._find_parent_nodes(graph)

        for edge in edges:
            lineage_items = self._serialize_lineage_item(edge, direction, key_class, graph, root_node, parent_nodes)

            result += lineage_items

        return result

    def get_lineage(self, *, id: str, resource_type: ResourceType, direction: str, depth: int) -> Lineage:
        """
        Retrieves the lineage information for the specified resource type.

        :param id: Key of entity for which lineage will be collected
        :param resource_type: Type of the entity for which lineage is being retrieved
        :param direction: Whether to get the upstream/downstream or both directions
        :param depth: Depth or level of lineage information. 0=only parent, 1=immediate nodes, 2=...
        :return: The Lineage object with upstream & downstream lineage items
        """
        lineage_spec: Dict[str, Any] = dict(key=id,
                                            direction=direction,
                                            depth=depth,
                                            upstream_entities=[],
                                            downstream_entities=[])

        # Atlas returns complete lineage when depth=0. In Amundsen depth=0 means only parent.
        if depth > 0:
            key_class: Union[Type[AtlasTableKey], Type[AtlasColumnKey]]

            if resource_type == ResourceType.Column:
                key_class = AtlasColumnKey
            elif resource_type == ResourceType.Table:
                key_class = AtlasTableKey
            else:
                raise NotImplementedError(f'Resource {resource_type.name} not supported!')

            key = key_class(id)  # type: ignore

            entity = self.client.entity.get_entity_by_attribute(type_name=resource_type.name,
                                                                uniq_attributes=[(AtlasCommonParams.qualified_name,
                                                                                  key.qualified_name)])

            entity_guid = entity.entity.guid

            _upstream: Dict[str, Any] = {}
            _downstream: Dict[str, Any] = {}

            if not direction == 'downstream':
                _upstream = self.client.lineage.get_lineage_info(entity_guid, 'INPUT', depth)

            if not direction == 'upstream':
                _downstream = self.client.lineage.get_lineage_info(entity_guid, 'OUTPUT', depth)

            upstream = self._serialize_lineage(_upstream, resource_type.name, id, 'upstream', key_class)
            downstream = self._serialize_lineage(_downstream, resource_type.name, id, 'downstream', key_class)

            lineage_spec['upstream_entities'] = upstream
            lineage_spec['downstream_entities'] = downstream

        lineage = Lineage(**lineage_spec)

        return lineage

    def get_feature(self, *, feature_uri: str) -> Feature:
        pass

    def get_resource_description(self, *,
                                 resource_type: ResourceType,
                                 uri: str) -> Description:
        pass

    def put_resource_description(self, *,
                                 resource_type: ResourceType,
                                 uri: str,
                                 description: str) -> None:
        pass

    def add_resource_owner(self, *,
                           uri: str,
                           resource_type: ResourceType,
                           owner: str) -> None:
        pass

    def delete_resource_owner(self, *,
                              uri: str,
                              resource_type: ResourceType,
                              owner: str) -> None:
        pass

    def get_resource_generation_code(self, *,
                                     uri: str,
                                     resource_type: ResourceType) -> GenerationCode:
        pass

    def get_popular_resources(self, *,
                              num_entries: int,
                              resource_types: List[str],
                              user_id: Optional[str] = None) -> Dict[str, List]:
        raise NotImplementedError
