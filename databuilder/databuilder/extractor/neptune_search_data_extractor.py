# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import importlib
from typing import (
    Any, Dict, List, Optional,
)

from gremlin_python.process.graph_traversal import GraphTraversalSource, __
from gremlin_python.process.traversal import (
    Order, T, TextP,
)
from pyhocon import ConfigTree

from databuilder import Scoped
from databuilder.clients.neptune_client import NeptuneSessionClient
from databuilder.extractor.base_extractor import Extractor
from databuilder.models.cluster.cluster_constants import CLUSTER_REVERSE_RELATION_TYPE
from databuilder.models.dashboard.dashboard_chart import DashboardChart
from databuilder.models.dashboard.dashboard_metadata import DashboardMetadata
from databuilder.models.dashboard.dashboard_query import DashboardQuery
from databuilder.models.owner_constants import OWNER_OF_OBJECT_RELATION_TYPE
from databuilder.models.schema.schema_constant import SCHEMA_REVERSE_RELATION_TYPE
from databuilder.models.table_metadata import DescriptionMetadata, TableMetadata
from databuilder.models.timestamp.timestamp_constants import LASTUPDATED_RELATION_TYPE, TIMESTAMP_PROPERTY
from databuilder.models.usage.usage_constants import (
    READ_RELATION_COUNT_PROPERTY, READ_RELATION_TYPE, READ_REVERSE_RELATION_TYPE,
)
from databuilder.models.user import User
from databuilder.serializers.neptune_serializer import METADATA_KEY_PROPERTY_NAME


def _table_search_query(graph: GraphTraversalSource, tag_filter: str) -> List[Dict]:
    traversal = graph.V().hasLabel(TableMetadata.TABLE_NODE_LABEL)
    if tag_filter:
        traversal = traversal.has('published_tag', tag_filter)
    traversal = traversal.project(
        'database',
        'cluster',
        'schema',
        'schema_description',
        'name',
        'key',
        'description',
        'last_updated_timestamp',
        'column_names',
        'column_descriptions',
        'total_usage',
        'unique_usage',
        'tags',
        'badges',
        'programmatic_descriptions'
    )
    traversal = traversal.by(
        __.out(
            TableMetadata.TABLE_SCHEMA_RELATION_TYPE
        ).out(SCHEMA_REVERSE_RELATION_TYPE).out(CLUSTER_REVERSE_RELATION_TYPE).values('name')
    )  # database
    traversal = traversal.by(
        __.out(TableMetadata.TABLE_SCHEMA_RELATION_TYPE).out(SCHEMA_REVERSE_RELATION_TYPE).values('name')
    )  # cluster
    traversal = traversal.by(__.out(TableMetadata.TABLE_SCHEMA_RELATION_TYPE).values('name'))  # schema
    traversal = traversal.by(__.coalesce(
        __.out(TableMetadata.TABLE_SCHEMA_RELATION_TYPE).out(
            DescriptionMetadata.DESCRIPTION_RELATION_TYPE
        ).values('description'),
        __.constant('')
    ))  # schema_description
    traversal = traversal.by('name')  # name
    traversal = traversal.by(T.id)  # key
    traversal = traversal.by(__.coalesce(
        __.out(DescriptionMetadata.DESCRIPTION_RELATION_TYPE).values('description'),
        __.constant('')
    ))  # description
    traversal = traversal.by(
        __.coalesce(__.out(LASTUPDATED_RELATION_TYPE).values(TIMESTAMP_PROPERTY), __.constant(''))
    )  # last_updated_timestamp
    traversal = traversal.by(__.out(TableMetadata.TABLE_COL_RELATION_TYPE).values('name').fold())  # column_names
    traversal = traversal.by(
        __.out(TableMetadata.TABLE_COL_RELATION_TYPE).out(
            DescriptionMetadata.DESCRIPTION_RELATION_TYPE
        ).values('description').fold()
    )  # column_descriptions
    traversal = traversal.by(__.coalesce(
        __.outE(READ_REVERSE_RELATION_TYPE).values('read_count'),
        __.constant(0)).sum()
    )  # total_usage
    traversal = traversal.by(__.outE(READ_REVERSE_RELATION_TYPE).count())  # unique_usage
    traversal = traversal.by(
        __.inE(TableMetadata.TAG_TABLE_RELATION_TYPE).outV().values(METADATA_KEY_PROPERTY_NAME).fold()
    )  # tags
    traversal = traversal.by(
        __.out('HAS_BADGE').values('keys').dedup().fold()
    )  # badges
    traversal = traversal.by(
        __.out(DescriptionMetadata.PROGRAMMATIC_DESCRIPTION_NODE_LABEL).values('description').fold()
    )  # programmatic_descriptions
    traversal = traversal.order().by(__.select('name'), Order.asc)
    return traversal.toList()


def _user_search_query(graph: GraphTraversalSource, tag_filter: str) -> List[Dict]:
    traversal = graph.V().hasLabel(User.USER_NODE_LABEL)
    traversal = traversal.has(User.USER_NODE_FULL_NAME)
    if tag_filter:
        traversal = traversal.where('published_tag', tag_filter)
    traversal = traversal.project(
        'email',
        'first_name',
        'last_name',
        'full_name',
        'github_username',
        'team_name',
        'employee_type',
        'manager_email',
        'slack_id',
        'is_active',
        'role_name',
        'total_read',
        'total_own',
        'total_follow'
    )
    traversal = traversal.by('email')  # email
    traversal = traversal.by('first_name')  # first_name
    traversal = traversal.by('last_name')  # last_name
    traversal = traversal.by('full_name')  # full_name
    traversal = traversal.by('github_username')  # github_username
    traversal = traversal.by('team_name')  # team_name
    traversal = traversal.by('employee_type')  # employee_type
    traversal = traversal.by(__.coalesce(
        __.out(User.USER_MANAGER_RELATION_TYPE).values('email'),
        __.constant(''))
    )  # manager_email
    traversal = traversal.by('slack_id')  # slack_id
    traversal = traversal.by('is_active')  # is_active
    traversal = traversal.by('role_name')  # role_name
    traversal = traversal.by(__.coalesce(
        __.outE(READ_RELATION_TYPE).values('read_count'),
        __.constant(0)
    ).sum())  # total_read
    traversal = traversal.by(__.outE(OWNER_OF_OBJECT_RELATION_TYPE).fold().count())  # total_own
    traversal = traversal.by(__.outE('FOLLOWED_BY').fold().count())  # total_follow
    traversal = traversal.order().by(__.select('email'), Order.asc)
    return traversal.toList()


def _dashboard_search_query(graph: GraphTraversalSource, tag_filter: str) -> List[Dict]:
    traversal = graph.V().hasLabel(DashboardMetadata.DASHBOARD_NODE_LABEL)
    traversal = traversal.has('name')
    if tag_filter:
        traversal = traversal.where('published_tag', tag_filter)

    traversal = traversal.project(
        'group_name',
        'name',
        'cluster',
        'description',
        'group_description',
        'group_url',
        'url',
        'uri',
        'last_successful_run_timestamp',
        'query_names',
        'chart_names',
        'total_usage',
        'tags',
        'badges'
    )
    traversal = traversal.by(
        __.out(DashboardMetadata.DASHBOARD_DASHBOARD_GROUP_RELATION_TYPE).values('name')
    )  # group_name
    traversal = traversal.by('name')  # name
    traversal = traversal.by(
        __.out(
            DashboardMetadata.DASHBOARD_DASHBOARD_GROUP_RELATION_TYPE
        ).out(
            DashboardMetadata.DASHBOARD_GROUP_CLUSTER_RELATION_TYPE
        ).values('name')
    )  # cluster
    traversal = traversal.by(__.coalesce(
        __.out(DashboardMetadata.DASHBOARD_DESCRIPTION_RELATION_TYPE).values('description'),
        __.constant('')
    ))  # description
    traversal = traversal.by(__.coalesce(
        __.out(DashboardMetadata.DASHBOARD_DASHBOARD_GROUP_RELATION_TYPE).out(
            DashboardMetadata.DASHBOARD_DESCRIPTION_RELATION_TYPE
        ).values('description'),
        __.constant('')
    ))  # group_description
    traversal = traversal.by(
        __.out(DashboardMetadata.DASHBOARD_DASHBOARD_GROUP_RELATION_TYPE).values('dashboard_group_url')
    )  # group_url
    traversal = traversal.by('dashboard_url')  # dashboard_url
    traversal = traversal.by('key')  # uri

    traversal = traversal.by(
        __.coalesce(
            __.out('EXECUTED').has('key', TextP.endingWith('_last_successful_execution')).values('timestamp'),
            __.constant('')
        )
    )  # last_successful_run_timestamp
    traversal = traversal.by(
        __.out(DashboardQuery.DASHBOARD_QUERY_RELATION_TYPE).values('name').dedup().fold()
    )  # query_names
    traversal = traversal.by(
        __.out(
            DashboardQuery.DASHBOARD_QUERY_RELATION_TYPE
        ).out(DashboardChart.CHART_RELATION_TYPE).values('name').dedup().fold()
    )  # chart_names
    traversal = traversal.by(__.coalesce(
        __.outE(READ_REVERSE_RELATION_TYPE).values(READ_RELATION_COUNT_PROPERTY),
        __.constant(0)
    ).sum())  # total_usage
    traversal = traversal.by(
        __.out('TAGGED_BY').has('tag_type', 'default').values('keys').dedup().fold()
    )  # tags
    traversal = traversal.by(
        __.out('HAS_BADGE').values('keys').dedup().fold()
    )  # badges

    traversal = traversal.order().by(__.select('name'), Order.asc)

    dashboards = traversal.toList()
    for dashboard in dashboards:
        dashboard['product'] = dashboard['uri'].split('_')[0]

    return dashboards


class NeptuneSearchDataExtractor(Extractor):
    """
    Extractor to fetch data required to support search from Neptune's graph database
    """
    QUERY_FUNCTION_CONFIG_KEY = 'query_function'
    QUERY_FUNCTION_KWARGS_CONFIG_KEY = 'query_function_kwargs'
    ENTITY_TYPE_CONFIG_KEY = 'entity_type'
    JOB_PUBLISH_TAG_CONFIG_KEY = 'job_publish_tag'
    MODEL_CLASS_CONFIG_KEY = 'model_class'

    DEFAULT_QUERY_BY_ENTITY = {
        'table': _table_search_query,
        'user': _user_search_query,
        'dashboard': _dashboard_search_query
    }

    def init(self, conf: ConfigTree) -> None:
        self.conf = conf
        self.entity = conf.get_string(NeptuneSearchDataExtractor.ENTITY_TYPE_CONFIG_KEY, default='table').lower()

        if NeptuneSearchDataExtractor.QUERY_FUNCTION_CONFIG_KEY in conf:
            self.query_function = conf.get(NeptuneSearchDataExtractor.QUERY_FUNCTION_CONFIG_KEY)
        else:
            self.query_function = NeptuneSearchDataExtractor.DEFAULT_QUERY_BY_ENTITY[self.entity]

        self.job_publish_tag = conf.get_string(NeptuneSearchDataExtractor.JOB_PUBLISH_TAG_CONFIG_KEY, '')
        self.neptune_client = NeptuneSessionClient()

        neptune_client_conf = Scoped.get_scoped_conf(conf, self.neptune_client.get_scope())
        self.neptune_client.init(neptune_client_conf)

        model_class = conf.get(NeptuneSearchDataExtractor.MODEL_CLASS_CONFIG_KEY, None)
        if model_class:
            module_name, class_name = model_class.rsplit(".", 1)
            mod = importlib.import_module(module_name)
            self.model_class = getattr(mod, class_name)

        self._extract_iter: Optional[Any] = None

    def close(self) -> None:
        self.neptune_client.close()

    def extract(self) -> Optional[Any]:
        if not self._extract_iter:
            self._extract_iter = self._get_extract_iter()

        try:
            return next(self._extract_iter)
        except StopIteration:
            return None

    def _get_extract_iter(self) -> Any:
        if not hasattr(self, 'results'):
            self.results = self.query_function(self.neptune_client.get_graph(), tag_filter=self.job_publish_tag)

        for result in self.results:
            if hasattr(self, 'model_class'):
                obj = self.model_class(**result)
                yield obj
            else:
                yield result

    def get_scope(self) -> str:
        return 'extractor.neptune_search_data'
