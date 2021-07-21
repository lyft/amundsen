# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import importlib
import logging
import multiprocessing.pool
from copy import deepcopy
from functools import reduce
from typing import (
    Any, Dict, Generator, Iterator, List, Optional, Tuple,
)

from amundsen_common.utils.atlas import AtlasTableKey
from atlasclient.client import Atlas
from pyhocon import ConfigFactory, ConfigTree

from databuilder.extractor.base_extractor import Extractor

LOGGER = logging.getLogger(__name__)

# custom types
type_fields_mapping_spec = Dict[str, List[Tuple[str, Any, Any, Any]]]
type_fields_mapping = List[Tuple[str, Any, Any, Any]]

# @todo document classes/methods
# @todo write tests

__all__ = ['AtlasSearchDataExtractor']


class AtlasSearchDataExtractorHelpers:
    @staticmethod
    def _filter_none(input_list: List) -> List:
        return list(filter(None, input_list))

    @staticmethod
    def get_entity_names(entity_list: Optional[List]) -> List:
        entity_list = entity_list or []
        return AtlasSearchDataExtractorHelpers._filter_none(
            [e.get('attributes').get('name') for e in entity_list if e.get('status').lower() == 'active'])

    @staticmethod
    def get_entity_uri(qualified_name: str, type_name: str) -> str:
        key = AtlasTableKey(qualified_name, database=type_name)
        return key.amundsen_key

    @staticmethod
    def get_entity_descriptions(entity_list: Optional[List]) -> List:
        entity_list = entity_list or []
        return AtlasSearchDataExtractorHelpers._filter_none(
            [e.get('attributes', dict()).get('description') for e in entity_list
             if e.get('status').lower() == 'active'])

    @staticmethod
    def get_badges_from_classifications(classifications: Optional[List]) -> List:
        classifications = classifications or []
        return AtlasSearchDataExtractorHelpers._filter_none(
            [c.get('typeName') for c in classifications if c.get('entityStatus', '').lower() == 'active'])

    @staticmethod
    def get_display_text(meanings: Optional[List]) -> List:
        meanings = meanings or []
        return AtlasSearchDataExtractorHelpers._filter_none(
            [c.get('displayText') for c in meanings if c.get('entityStatus', '').lower() == 'active'])

    @staticmethod
    def get_last_successful_execution_timestamp(executions: Optional[List]) -> int:
        executions = executions or []
        successful_executions = AtlasSearchDataExtractorHelpers._filter_none(
            [e.get('attributes').get('timestamp') for e in executions
             if e.get('status', '').lower() == 'active' and e.get('attributes', dict()).get('state') == 'succeeded'])

        try:
            return max(successful_executions)
        except ValueError:
            return 0

    @staticmethod
    def get_chart_names(queries: Optional[List]) -> List[str]:
        queries = queries or []
        charts = []

        for query in queries:
            _charts = query.get('relationshipAttributes', dict()).get('charts', [])
            charts += _charts

        return AtlasSearchDataExtractorHelpers.get_display_text(charts)


class AtlasSearchDataExtractor(Extractor):
    ATLAS_URL_CONFIG_KEY = 'atlas_url'
    ATLAS_PORT_CONFIG_KEY = 'atlas_port'
    ATLAS_PROTOCOL_CONFIG_KEY = 'atlas_protocol'
    ATLAS_VALIDATE_SSL_CONFIG_KEY = 'atlas_validate_ssl'
    ATLAS_USERNAME_CONFIG_KEY = 'atlas_auth_user'
    ATLAS_PASSWORD_CONFIG_KEY = 'atlas_auth_pw'
    ATLAS_SEARCH_CHUNK_SIZE_KEY = 'atlas_search_chunk_size'
    ATLAS_DETAILS_CHUNK_SIZE_KEY = 'atlas_details_chunk_size'
    ATLAS_TIMEOUT_SECONDS_KEY = 'atlas_timeout_seconds'
    ATLAS_MAX_RETRIES_KEY = 'atlas_max_retries'

    PROCESS_POOL_SIZE_KEY = 'process_pool_size'

    ENTITY_TYPE_KEY = 'entity_type'

    DEFAULT_CONFIG = ConfigFactory.from_dict({ATLAS_URL_CONFIG_KEY: "localhost",
                                              ATLAS_PORT_CONFIG_KEY: 21000,
                                              ATLAS_PROTOCOL_CONFIG_KEY: 'http',
                                              ATLAS_VALIDATE_SSL_CONFIG_KEY: False,
                                              ATLAS_SEARCH_CHUNK_SIZE_KEY: 250,
                                              ATLAS_DETAILS_CHUNK_SIZE_KEY: 25,
                                              ATLAS_TIMEOUT_SECONDS_KEY: 120,
                                              ATLAS_MAX_RETRIES_KEY: 2,
                                              PROCESS_POOL_SIZE_KEY: 10})

    # es_document field, atlas field path, modification function, default_value
    FIELDS_MAPPING_SPEC: type_fields_mapping_spec = {
        'Table': [
            ('database', 'typeName', None, None),
            ('cluster', 'attributes.qualifiedName', lambda x: x.split('@')[-1], None),
            ('schema', 'relationshipAttributes.db.displayText', None, None),
            ('name', 'attributes.name', None, None),
            ('key', ['attributes.qualifiedName', 'typeName'],
             lambda x, y: AtlasSearchDataExtractorHelpers.get_entity_uri(x, y), None),
            ('description', 'attributes.description', None, None),
            ('last_updated_timestamp', 'updateTime', lambda x: int(x) / 1000, 0),
            ('total_usage', 'attributes.popularityScore', lambda x: int(x), 0),
            ('unique_usage', 'attributes.uniqueUsage', lambda x: int(x), 1),
            ('column_names', 'relationshipAttributes.columns',
             lambda x: AtlasSearchDataExtractorHelpers.get_entity_names(x), []),
            ('column_descriptions', 'relationshipAttributes.columns',
             lambda x: AtlasSearchDataExtractorHelpers.get_entity_descriptions(x), []),
            ('tags', 'relationshipAttributes.meanings',
             lambda x: AtlasSearchDataExtractorHelpers.get_display_text(x), []),
            ('badges', 'classifications',
             lambda x: AtlasSearchDataExtractorHelpers.get_badges_from_classifications(x), []),
            ('display_name', 'attributes.qualifiedName', lambda x: x.split('@')[0], None),
            ('schema_description', 'attributes.parameters.sourceDescription', None, None),
            ('programmatic_descriptions', 'attributes.parameters', lambda x: [str(s) for s in list(x.values())], {})
        ],
        'Dashboard': [
            ('group_name', 'relationshipAttributes.group.attributes.name', None, None),
            ('name', 'attributes.name', None, None),
            ('description', 'attributes.description', None, None),
            ('total_usage', 'attributes.popularityScore', lambda x: int(x), 0),
            ('product', 'attributes.product', None, None),
            ('cluster', 'attributes.cluster', None, None),
            ('group_description', 'relationshipAttributes.group.attributes.description', None, None),
            ('query_names', 'relationshipAttributes.queries',
             lambda x: AtlasSearchDataExtractorHelpers.get_entity_names(x), []),
            ('chart_names', 'relationshipAttributes.queries',
             lambda x: AtlasSearchDataExtractorHelpers.get_chart_names(x), []),
            ('group_url', 'relationshipAttributes.group.attributes.url', None, None),
            ('url', 'attributes.url', None, None),
            ('uri', 'attributes.qualifiedName', None, None),
            ('last_successful_run_timestamp', 'relationshipAttributes.executions',
             lambda x: AtlasSearchDataExtractorHelpers.get_last_successful_execution_timestamp(x), None),
            ('tags', 'relationshipAttributes.meanings',
             lambda x: AtlasSearchDataExtractorHelpers.get_display_text(x), []),
            ('badges', 'classifications',
             lambda x: AtlasSearchDataExtractorHelpers.get_badges_from_classifications(x), [])
        ]
    }

    ENTITY_MODEL_BY_TYPE = {
        'Table': 'databuilder.models.table_elasticsearch_document.TableESDocument',
        'Dashboard': 'databuilder.models.dashboard_elasticsearch_document.DashboardESDocument'
    }

    REQUIRED_RELATIONSHIPS_BY_TYPE = {
        'Table': ['columns'],
        'Dashboard': ['group', 'charts', 'executions', 'queries']
    }

    def init(self, conf: ConfigTree) -> None:
        self.conf = conf.with_fallback(AtlasSearchDataExtractor.DEFAULT_CONFIG)
        self.driver = self._get_driver()

        self._extract_iter: Optional[Iterator[Any]] = None

    @property
    def entity_type(self) -> str:
        return self.conf.get(AtlasSearchDataExtractor.ENTITY_TYPE_KEY)

    @property
    def dsl_search_query(self) -> Dict:
        query = {
            'query': f'{self.entity_type} where __state = "ACTIVE"'
        }

        LOGGER.debug(f'DSL Search Query: {query}')

        return query

    @property
    def model_class(self) -> Any:
        model_class = AtlasSearchDataExtractor.ENTITY_MODEL_BY_TYPE.get(self.entity_type)

        if model_class:
            module_name, class_name = model_class.rsplit(".", 1)
            mod = importlib.import_module(module_name)

            return getattr(mod, class_name)

    @property
    def field_mappings(self) -> type_fields_mapping:
        return AtlasSearchDataExtractor.FIELDS_MAPPING_SPEC.get(self.entity_type) or []

    @property
    def search_chunk_size(self) -> int:
        return self.conf.get_int(AtlasSearchDataExtractor.ATLAS_SEARCH_CHUNK_SIZE_KEY)

    @property
    def relationships(self) -> Optional[List[str]]:
        return AtlasSearchDataExtractor.REQUIRED_RELATIONSHIPS_BY_TYPE.get(self.entity_type)

    def extract(self) -> Any:
        if not self._extract_iter:
            self._extract_iter = self._get_extract_iter()

        try:
            return next(self._extract_iter)
        except StopIteration:
            return None

    def get_scope(self) -> str:
        return 'extractor.atlas_search_data'

    def _get_driver(self) -> Any:
        return Atlas(host=self.conf.get_string(AtlasSearchDataExtractor.ATLAS_URL_CONFIG_KEY),
                     port=self.conf.get_string(AtlasSearchDataExtractor.ATLAS_PORT_CONFIG_KEY),
                     username=self.conf.get_string(AtlasSearchDataExtractor.ATLAS_USERNAME_CONFIG_KEY),
                     password=self.conf.get_string(AtlasSearchDataExtractor.ATLAS_PASSWORD_CONFIG_KEY),
                     protocol=self.conf.get_string(AtlasSearchDataExtractor.ATLAS_PROTOCOL_CONFIG_KEY),
                     validate_ssl=self.conf.get_bool(AtlasSearchDataExtractor.ATLAS_VALIDATE_SSL_CONFIG_KEY),
                     timeout=self.conf.get_int(AtlasSearchDataExtractor.ATLAS_TIMEOUT_SECONDS_KEY),
                     max_retries=self.conf.get_int(AtlasSearchDataExtractor.ATLAS_MAX_RETRIES_KEY))

    def _get_latest_entity_metrics(self) -> Optional[dict]:
        admin_metrics = list(self.driver.admin_metrics)

        try:
            return admin_metrics[-1].entity
        except Exception:
            return None

    def _get_count_of_active_entities(self) -> int:
        entity_metrics = self._get_latest_entity_metrics()

        if entity_metrics:
            count = entity_metrics.get('entityActive-typeAndSubTypes', dict()).get(self.entity_type, 0)

            return int(count)
        else:
            return 0

    def _get_entity_guids(self, start_offset: int) -> List[str]:
        result = []

        batch_start = start_offset
        batch_end = start_offset + self.search_chunk_size

        LOGGER.info(f'Collecting guids for batch: {batch_start}-{batch_end}')

        _params = {'offset': str(batch_start), 'limit': str(self.search_chunk_size)}

        full_params = deepcopy(self.dsl_search_query)
        full_params.update(**_params)

        try:
            results = self.driver.search_dsl(**full_params)

            for hit in results:
                for entity in hit.entities:
                    result.append(entity.guid)

            return result
        except Exception:
            LOGGER.warning(f'Error processing batch: {batch_start}-{batch_end}', exc_info=True)

            return []

    def _get_entity_details(self, guid_list: List[str]) -> List:
        result = []

        LOGGER.info(f'Processing guids chunk of size: {len(guid_list)}')

        try:
            bulk_collection = self.driver.entity_bulk(guid=guid_list)

            for collection in bulk_collection:
                search_chunk = list(collection.entities_with_relationships(attributes=self.relationships))

                result += search_chunk

            return result
        except Exception:
            LOGGER.warning(f'Error processing guids. {len(guid_list)}', exc_info=True)

            return []

    @staticmethod
    def split_list_to_chunks(input_list: List[Any], n: int) -> Generator:
        """Yield successive n-sized chunks from lst."""
        for i in range(0, len(input_list), n):
            yield input_list[i:i + n]

    def _execute_query(self) -> Any:
        details_chunk_size = self.conf.get_int(AtlasSearchDataExtractor.ATLAS_DETAILS_CHUNK_SIZE_KEY)
        process_pool_size = self.conf.get_int(AtlasSearchDataExtractor.PROCESS_POOL_SIZE_KEY)

        guids = []

        entity_count = self._get_count_of_active_entities()

        LOGGER.info(f'Received count: {entity_count}')

        if entity_count > 0:
            offsets = [i * self.search_chunk_size for i in range(int(entity_count / self.search_chunk_size) + 1)]
        else:
            offsets = []

        with multiprocessing.pool.ThreadPool(processes=process_pool_size) as pool:
            guid_list = pool.map(self._get_entity_guids, offsets, chunksize=1)

        for sub_list in guid_list:
            guids += sub_list

        LOGGER.info(f'Received guids: {len(guids)}')

        if guids:
            guids_chunks = AtlasSearchDataExtractor.split_list_to_chunks(guids, details_chunk_size)

            with multiprocessing.pool.ThreadPool(processes=process_pool_size) as pool:
                return_list = pool.map(self._get_entity_details, guids_chunks)

            for sub_list in return_list:
                for entry in sub_list:
                    yield entry

    def _get_extract_iter(self) -> Iterator[Any]:
        for atlas_entity in self._execute_query():
            model_dict = dict()

            try:
                data = atlas_entity.__dict__['_data']

                for spec in self.field_mappings:
                    model_field, atlas_fields_paths, _transform_spec, default_value = spec

                    if not isinstance(atlas_fields_paths, list):
                        atlas_fields_paths = [atlas_fields_paths]

                    atlas_values = []
                    for atlas_field_path in atlas_fields_paths:

                        atlas_value = reduce(lambda x, y: x.get(y, dict()), atlas_field_path.split('.'),
                                             data) or default_value
                        atlas_values.append(atlas_value)

                    transform_spec = _transform_spec or (lambda x: x)

                    es_entity_value = transform_spec(*atlas_values)
                    model_dict[model_field] = es_entity_value

                yield self.model_class(**model_dict)
            except Exception:
                LOGGER.warning('Error building model object.', exc_info=True)
