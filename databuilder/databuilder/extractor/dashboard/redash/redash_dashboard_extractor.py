# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import importlib
from typing import (
    Any, Dict, Iterator, Optional,
)

from pyhocon import ConfigFactory, ConfigTree

from databuilder.extractor.base_extractor import Extractor
from databuilder.extractor.dashboard.redash.redash_dashboard_utils import (
    RedashPaginatedRestApiQuery, generate_dashboard_description, get_auth_headers, get_text_widgets,
    get_visualization_widgets, sort_widgets,
)
from databuilder.extractor.restapi.rest_api_extractor import REST_API_QUERY, RestAPIExtractor
from databuilder.models.dashboard.dashboard_chart import DashboardChart
from databuilder.models.dashboard.dashboard_last_modified import DashboardLastModifiedTimestamp
from databuilder.models.dashboard.dashboard_metadata import DashboardMetadata
from databuilder.models.dashboard.dashboard_owner import DashboardOwner
from databuilder.models.dashboard.dashboard_query import DashboardQuery
from databuilder.models.dashboard.dashboard_table import DashboardTable
from databuilder.models.table_metadata import TableMetadata
from databuilder.rest_api.base_rest_api_query import EmptyRestApiQuerySeed
from databuilder.rest_api.rest_api_query import RestApiQuery
from databuilder.transformer.base_transformer import ChainedTransformer
from databuilder.transformer.timestamp_string_to_epoch import FIELD_NAME as TS_FIELD_NAME, TimestampStringToEpoch


class TableRelationData:
    """
    This is sort of like a stripped down version of `TableMetadata`.
    It is used as the type returned by the (optional) table parser.
    """

    def __init__(self,
                 database: str,
                 cluster: str,
                 schema: str,
                 name: str) -> None:
        self._data = {'db': database, 'cluster': cluster, 'schema': schema, 'tbl': name}

    @property
    def key(self) -> str:
        return TableMetadata.TABLE_KEY_FORMAT.format(**self._data)


class RedashDashboardExtractor(Extractor):
    """
    An extractor for retrieving dashboards and associated queries
    (and possibly tables) from Redash.

    There are five configuration values:

    - `redash_base_url`: (e.g., `https://redash.example.com`) Base URL for the user-facing
    Redash application
    - `api_base_url`: (e.g., `https://redash.example.com/api`) Base URL for the API
    - `api_key`: Redash API key
    - (optional) `cluster`: A cluster name for this Redash instance (defaults to `prod`)
    - (optional) `table_parser`: A function `(RedashVisualizationWidget) -> List[TableRelationData]`.
    Given a `RedashVisualizationWidget`, this should return a list of potentially related tables
    in Amundsen. Any table returned that exists in Amundsen will be linked to the dashboard.
    Any table that does not exist will be ignored.
    """

    REDASH_BASE_URL_KEY = 'redash_base_url'
    API_BASE_URL_KEY = 'api_base_url'
    API_KEY_KEY = 'api_key'
    CLUSTER_KEY = 'cluster'  # optional config
    TABLE_PARSER_KEY = 'table_parser'  # optional config
    REDASH_VERSION = 'redash_version'  # optional config

    DEFAULT_CLUSTER = 'prod'
    DEFAULT_VERSION = 9

    PRODUCT = 'redash'
    DASHBOARD_GROUP_ID = 'redash'
    DASHBOARD_GROUP_NAME = 'Redash'

    def init(self, conf: ConfigTree) -> None:

        # required configuration
        self._redash_base_url = conf.get_string(RedashDashboardExtractor.REDASH_BASE_URL_KEY)
        self._api_base_url = conf.get_string(RedashDashboardExtractor.API_BASE_URL_KEY)
        self._api_key = conf.get_string(RedashDashboardExtractor.API_KEY_KEY)

        # optional configuration
        self._cluster = conf.get_string(
            RedashDashboardExtractor.CLUSTER_KEY, RedashDashboardExtractor.DEFAULT_CLUSTER
        )
        self._redash_version = conf.get_int(
            RedashDashboardExtractor.REDASH_VERSION, RedashDashboardExtractor.DEFAULT_VERSION
        )

        self._parse_tables = None
        tbl_parser_path = conf.get_string(RedashDashboardExtractor.TABLE_PARSER_KEY)
        if tbl_parser_path:
            module_name, fn_name = tbl_parser_path.rsplit('.', 1)
            mod = importlib.import_module(module_name)
            self._parse_tables = getattr(mod, fn_name)

        self._extractor = self._build_extractor()
        self._transformer = self._build_transformer()
        self._extract_iter: Optional[Iterator[Any]] = None

    def _is_published_dashboard(self, record: Dict[str, Any]) -> bool:
        return not (record['is_archived'] or record['is_draft'])

    def _get_extract_iter(self) -> Iterator[Any]:

        while True:
            record = self._extractor.extract()
            if not record:
                break  # the end.

            record = next(self._transformer.transform(record=record), None)

            if not self._is_published_dashboard(record):
                continue  # filter this one out

            identity_data = {
                'cluster': self._cluster,
                'product': RedashDashboardExtractor.PRODUCT,
                'dashboard_group_id': str(RedashDashboardExtractor.DASHBOARD_GROUP_ID),
                'dashboard_id': str(record['dashboard_id']),
            }

            if self._redash_version >= 9:
                dashboard_url = f'{self._redash_base_url}/dashboards/{record["dashboard_id"]}'
            else:
                dashboard_url = f'{self._redash_base_url}/dashboard/{record["slug"]}'

            dash_data = {
                'dashboard_group':
                    RedashDashboardExtractor.DASHBOARD_GROUP_NAME,
                'dashboard_group_url':
                    self._redash_base_url,
                'dashboard_name':
                    record['dashboard_name'],
                'dashboard_url':
                    dashboard_url,
                'created_timestamp':
                    record['created_timestamp']
            }
            dash_data.update(identity_data)

            widgets = sort_widgets(record['widgets'])
            text_widgets = get_text_widgets(widgets)
            viz_widgets = get_visualization_widgets(widgets)

            # generate a description for this dashboard, since Redash does not have descriptions
            dash_data['description'] = generate_dashboard_description(text_widgets, viz_widgets)

            yield DashboardMetadata(**dash_data)

            last_mod_data = {'last_modified_timestamp': record['last_modified_timestamp']}
            last_mod_data.update(identity_data)

            yield DashboardLastModifiedTimestamp(**last_mod_data)

            owner_data = {'email': record['user']['email']}
            owner_data.update(identity_data)

            yield DashboardOwner(**owner_data)

            table_keys = set()

            for viz in viz_widgets:
                query_data = {
                    'query_id': str(viz.query_id),
                    'query_name': viz.query_name,
                    'url': self._redash_base_url + viz.query_relative_url,
                    'query_text': viz.raw_query
                }

                query_data.update(identity_data)
                yield DashboardQuery(**query_data)

                chart_data = {
                    'query_id': str(viz.query_id),
                    'chart_id': str(viz.visualization_id),
                    'chart_name': viz.visualization_name,
                    'chart_type': viz.visualization_type,
                }
                chart_data.update(identity_data)
                yield DashboardChart(**chart_data)

                # if a table parser is provided, retrieve tables from this viz
                if self._parse_tables:
                    for tbl in self._parse_tables(viz):
                        table_keys.add(tbl.key)

            if len(table_keys) > 0:
                yield DashboardTable(table_ids=list(table_keys), **identity_data)

    def extract(self) -> Any:

        if not self._extract_iter:
            self._extract_iter = self._get_extract_iter()
        try:
            return next(self._extract_iter)
        except StopIteration:
            return None

    def _build_restapi_query(self) -> RestApiQuery:

        dashes_query = RedashPaginatedRestApiQuery(
            query_to_join=EmptyRestApiQuerySeed(),
            url=f'{self._api_base_url}/dashboards',
            params=self._get_default_api_query_params(),
            json_path='results[*].[id,name,slug,created_at,updated_at,is_archived,is_draft,user]',
            field_names=[
                'dashboard_id', 'dashboard_name', 'slug', 'created_timestamp',
                'last_modified_timestamp', 'is_archived', 'is_draft', 'user'
            ],
            skip_no_result=True
        )

        if self._redash_version >= 9:
            dashboard_url = f'{self._api_base_url}/dashboards/{{dashboard_id}}'
        else:
            dashboard_url = f'{self._api_base_url}/dashboards/{{slug}}'

        return RestApiQuery(
            query_to_join=dashes_query,
            url=dashboard_url,
            params=self._get_default_api_query_params(),
            json_path='widgets',
            field_names=['widgets'],
            skip_no_result=True
        )

    def _get_default_api_query_params(self) -> Dict[str, Any]:

        return {'headers': get_auth_headers(self._api_key)}

    def _build_extractor(self) -> RestAPIExtractor:

        extractor = RestAPIExtractor()
        rest_api_extractor_conf = ConfigFactory.from_dict({
            REST_API_QUERY: self._build_restapi_query()
        })
        extractor.init(rest_api_extractor_conf)
        return extractor

    def _build_transformer(self) -> ChainedTransformer:

        transformers = []

        # transform timestamps from ISO to unix epoch
        ts_transformer_1 = TimestampStringToEpoch()
        ts_transformer_1.init(ConfigFactory.from_dict({
            TS_FIELD_NAME: 'created_timestamp',
        }))
        transformers.append(ts_transformer_1)

        ts_transformer_2 = TimestampStringToEpoch()
        ts_transformer_2.init(ConfigFactory.from_dict({
            TS_FIELD_NAME: 'last_modified_timestamp',
        }))
        transformers.append(ts_transformer_2)

        return ChainedTransformer(transformers=transformers)

    def get_scope(self) -> str:

        return 'extractor.redash_dashboard'
