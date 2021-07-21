# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import logging
from re import sub
from typing import (
    Any, Dict, List, Optional, Tuple,
)

from atlasclient.client import Atlas
from atlasclient.exceptions import BadRequest
from atlasclient.models import Entity, EntityCollection
# default search page size
from atlasclient.utils import parse_table_qualified_name

from search_service.models.dashboard import SearchDashboardResult
from search_service.models.feature import SearchFeatureResult
from search_service.models.table import SearchTableResult, Table
from search_service.models.tag import Tag
from search_service.models.user import SearchUserResult
from search_service.proxy import BaseProxy
from search_service.proxy.statsd_utilities import timer_with_counter

LOGGER = logging.getLogger(__name__)


class AtlasProxy(BaseProxy):
    """
    AtlasSearch connection handler
    """
    ATLAS_TABLE_ENTITY = 'Table'
    ATLAS_QN_ATTRIBUTE = 'qualifiedName'

    def __init__(self, *,
                 host: str = None,
                 user: str = '',
                 password: str = '',
                 client: Atlas = None,
                 page_size: int = 10) -> None:
        self.atlas = client or Atlas(host, username=user, password=password)
        self.page_size = page_size

    @staticmethod
    def _extract_entities(collections: EntityCollection) -> List[Entity]:
        """
        Helper method for flattening all collections from {collections}

        :return: list of all entities
        """
        entities: List[Entity] = []

        for collection in collections:
            entities.extend(collection.entities)
        return entities

    def _prepare_tables(self, response: EntityCollection, enhance_metadata: bool = False) -> List[Table]:
        """
        Based on an Atlas {response} with table entities, we render Table objects.

        :param response: Collection of Atlas Entities
        :param enhance_metadata: Should Atlas be queried to acquire complete entity definitions (search might not
        return all available attributes)
        :return: List of Table objects
        """

        result = list()

        # if condition is satisfied then we query Atlas again to collect all available information regarding each table
        # along with relationship information. This is helpful when using Atlas DSL as returned entities contain minimal
        # amount of attributes.
        if enhance_metadata:
            ids = list()

            for hit in response:
                ids.append(hit.guid)

            entities = self._extract_entities(self.atlas.entity_bulk(guid=ids, ignoreRelationships=False))
        else:
            entities = response

        for entity in entities:
            entity_attrs = entity.attributes

            qn = parse_table_qualified_name(qualified_name=entity_attrs.get(self.ATLAS_QN_ATTRIBUTE))

            entity_name = qn.get('table_name') or entity_attrs.get('name')
            db_name = qn.get('db_name', '')
            db_cluster = qn.get('cluster_name', '')

            tags: List[Tag] = []

            for classification in entity.classificationNames or list():
                tags.append(Tag(tag_name=classification))

            badges: List[Tag] = tags

            table = Table(id=f"{entity.typeName}://{db_cluster}.{db_name}/{entity_name}",
                          name=entity_name,
                          key=f"{entity.typeName}://{db_cluster}.{db_name}/{entity_name}",
                          description=entity_attrs.get('description'),
                          cluster=db_cluster,
                          database=entity.typeName,
                          schema=db_name,
                          tags=tags,
                          badges=badges,
                          column_names=[],
                          last_updated_timestamp=entity_attrs.get('updateTime'))

            result.append(table)

        return result

    def _atlas_basic_search(self, query_params: Dict) -> Tuple[List[Table], int]:
        """
        Conduct search using Atlas Basic Search API.

        :param query_params: A dictionary of query parameters needed to be pass to Basic Search Post method of Atlas
        :return: List of Table objects and approximate count of entities matching in Atlas
        """

        try:
            # Fetch the table entities based on query terms
            search_results = self.atlas.search_basic.create(data=query_params)
        except BadRequest as ex:
            LOGGER.error(f"Fetching Tables Failed : {str(ex)}")
            return [], 0

        if not len(search_results.entities):
            return [], 0

        # noinspection PyProtectedMember
        results_count = search_results._data.get("approximateCount")

        results = self._prepare_tables(search_results.entities, enhance_metadata=False)

        return results, results_count

    def _prepare_basic_search_query(self, limit: int, page_index: int, query_term: Optional[str] = None,
                                    filters: Optional[List[Tuple[str, str, str]]] = None,
                                    operator: Optional[str] = None,
                                    classification: Optional[str] = None,
                                    entity_type: str = None) -> Dict[str, Any]:
        """
        Render a query for Atlas Basic Search API.

        :param query_term: Search Query Term
        :param limit:
        :param page_index:
        :param fitlers: Optional list of tuples (field, condition, value) that will translate into entityFilters for
        narrowing down search results
        :param operator:
        :param entity_type: Which kind of entity this query will look for
        :return: Dictionary object prepared for Atlas client basic_search
        """
        if not entity_type:
            entity_type = self.ATLAS_TABLE_ENTITY

        query: Dict[str, Any] = {'typeName': entity_type,
                                 'excludeDeletedEntities': True,
                                 'includeSubTypes': True,
                                 'limit': limit,
                                 'offset': page_index * self.page_size,
                                 'sortBy': 'popularityScore',
                                 'sortOrder': 'DESCENDING'}

        if query_term:
            query_term = f'*{query_term}*'
            query_term = sub('\\*+', '*', query_term)

            query['query'] = query_term

        # filters and query_term shouldn't be mixed
        if filters and not query_term:
            condition = operator or 'AND'
            criterion: List[Dict[str, str]] = list()

            for _query_filter in filters:
                attribute_name, operator, attribute_value = _query_filter

                # filters perform much better when wildcard is dot, not star
                attribute_value = sub('\\*', '.', attribute_value)
                query_filter = {'attributeName': attribute_name,
                                'operator': operator.upper(),
                                'attributeValue': attribute_value}

                criterion.append(query_filter)

            if len(criterion) > 1:
                query['entityFilters'] = {'condition': condition, 'criterion': criterion}
            elif len(criterion) == 1:
                query['entityFilters'] = criterion[0]
        elif classification:
            query['classification'] = classification

        return query

    @timer_with_counter
    def fetch_table_search_results(self, *,
                                   query_term: str,
                                   page_index: int = 0,
                                   index: str = '') -> SearchTableResult:
        """
        Conduct a 'Basic Search' in Amundsen UI.

        Atlas Basic Search API is used for that operation. We search on `qualifiedName` field as
        (following Atlas documentation) any 'Referencable' entity 'can be searched for using a unique attribute called
        qualifiedName'. It provides best performance, simplicity and sorting by popularityScore.

        :param query_term: Search Query Term
        :param page_index: Index of search page user is currently on (for pagination)
        :param index: Search Index (different resource corresponding to different index)
        :return: SearchTableResult Object
        """
        if not query_term:
            # return empty result for blank query term
            return SearchTableResult(total_results=0, results=[])

        query_params = self._prepare_basic_search_query(self.page_size, page_index, query_term=query_term)

        tables, approx_count = self._atlas_basic_search(query_params)

        return SearchTableResult(total_results=approx_count, results=tables)

    def fetch_search_results_with_filter(self, *,
                                         query_term: str,
                                         search_request: dict,
                                         page_index: int = 0,
                                         index: str = '') -> SearchTableResult:
        """
        Conduct an 'Advanced Search' to narrow down search results with a use of filters.

        Using Atlas Basic Search with filters to retrieve precise results and sort them by popularity score.


        :param query_term: A Search Query Term
        :param search_request: Values from Filters
        :param page_index: Index of search page user is currently on (for pagination)
        :param index: Search Index (different resource corresponding to different index)
        :return: SearchTableResult Object
        """
        _filters = search_request.get('filters', dict())

        db_filter_value = _filters.get('database')
        table_filter_value = _filters.get('table')
        cluster_filter_value = _filters.get('cluster')
        tags_filter_value = _filters.get('tag')

        filters = list()

        # qualifiedName follows pattern ${db}.${table}@${cluster}
        if db_filter_value:
            filters.append((self.ATLAS_QN_ATTRIBUTE, 'STARTSWITH', db_filter_value[0] + '.'))

        if cluster_filter_value:
            filters.append((self.ATLAS_QN_ATTRIBUTE, 'ENDSWITH', '@' + cluster_filter_value[0]))

        if table_filter_value:
            filters.append(('name', 'CONTAINS', table_filter_value[0]))

        # Currently Atlas doesn't allow mixing search by filters and classifications
        if filters:
            query_params = self._prepare_basic_search_query(self.page_size, page_index,
                                                            filters=filters)
        elif tags_filter_value:
            query_params = self._prepare_basic_search_query(self.page_size, page_index,
                                                            classification=tags_filter_value[0])

        tables, approx_count = self._atlas_basic_search(query_params)

        return SearchTableResult(total_results=approx_count, results=tables)

    def fetch_user_search_results(self, *,
                                  query_term: str,
                                  page_index: int = 0,
                                  index: str = '') -> SearchUserResult:
        pass

    def fetch_dashboard_search_results(self, *,
                                       query_term: str,
                                       page_index: int = 0,
                                       index: str = '') -> SearchDashboardResult:
        pass

    def fetch_feature_search_results(self, *,
                                     query_term: str,
                                     page_index: int = 0,
                                     index: str = '') -> SearchFeatureResult:
        pass

    def update_document(self, *, data: List[Dict[str, Any]], index: str = '') -> str:
        raise NotImplementedError()

    def create_document(self, *, data: List[Dict[str, Any]], index: str = '') -> str:
        raise NotImplementedError()

    def delete_document(self, *, data: List[str], index: str = '') -> str:
        raise NotImplementedError()
