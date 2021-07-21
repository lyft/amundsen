# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0
import abc
import re
from typing import Any, Dict, Optional, Set


class AtlasStatus:
    ACTIVE = "ACTIVE"
    DELETED = "DELETED"


class AtlasCommonParams:
    qualified_name = 'qualifiedName'
    guid = 'guid'
    attributes = 'attributes'
    relationships = 'relationshipAttributes'
    uri = 'entityUri'
    type_name = 'typeName'
    unique_attributes = 'uniqueAttributes'
    created_timestamp = 'createdTimestamp'
    last_modified_timestamp = 'lastModifiedTimestamp'


class AtlasCommonTypes:
    bookmark = 'Bookmark'
    user = 'User'
    reader = 'Reader'
    cluster = 'Cluster'
    application = 'Application'
    tag = 'Tag'
    badge = 'Badge'
    data_set = 'DataSet'


class AtlasTableTypes:
    table = 'Table'
    column = 'Column'
    database = 'Database'
    schema = 'Schema'
    source = 'Source'
    watermark = 'TablePartition'
    process = 'LineageProcess'


class AtlasDashboardTypes:
    metadata = 'Dashboard'
    group = 'DashboardGroup'
    query = 'DashboardQuery'
    chart = 'DashboardChart'
    execution = 'DashboardExecution'


class AtlasKey(abc.ABC):
    """
    Class for unification of entity keys between Atlas and Amundsen ecosystems.

    Since Atlas can be populated both by tools from 'Atlas world' (like Apache Atlas Hive hook/bridge) and Amundsen
    Databuilder (and each of the approach has a different way to render unique identifiers) we need such class
    to serve as unification layer.
    """

    def __init__(self, raw_id: str, database: Optional[str] = None) -> None:
        self._raw_identifier = raw_id
        self._database = database

    @property
    def is_qualified_name(self) -> bool:
        """
        Property assessing whether raw_id is qualified name.

        :returns: -
        """
        if self.atlas_qualified_name_regex.match(self._raw_identifier):
            return True
        else:
            return False

    @property
    def is_amundsen_key(self) -> bool:
        """
        Property assessing whether raw_id is amundsen key.

        :returns: -
        """
        if self.amundsen_key_regex.match(self._raw_identifier):
            return True
        else:
            return False

    def get_details(self) -> Dict[str, str]:
        """
        Collect as many details from key (either qn or amundsen key)

        :returns: dictionary of entity properties derived from key
        """
        if self.is_qualified_name:
            return self._get_details_from_qualified_name()
        elif self.is_amundsen_key:
            return self._get_details_from_key()
        else:
            raise ValueError(f'Value is neither valid qualified name nor amundsen key: {self._raw_identifier}')

    def _get_details(self, pattern: Any) -> Dict[str, str]:
        """
        Helper function collecting data from regex match

        :returns: dictionary of matched regex groups with their values
        """
        try:
            result = pattern.match(self._raw_identifier).groupdict()

            return result
        except KeyError:
            raise KeyError

    def _get_details_from_qualified_name(self) -> Dict[str, str]:
        """
        Collect as many details from qualified name

        :returns: dictionary of entity properties derived from qualified name
        """
        try:
            return self._get_details(self.atlas_qualified_name_regex)
        except KeyError:
            raise ValueError(f'This is not valid qualified name: {self._raw_identifier}')

    def _get_details_from_key(self) -> Dict[str, str]:
        """
        Collect as many details from amundsen key

        :returns: dictionary of entity properties derived from amundsen key
        """
        try:
            return self._get_details(self.amundsen_key_regex)
        except KeyError:
            raise ValueError(f'This is not valid qualified name: {self._raw_identifier}')

    @property
    @abc.abstractmethod
    def atlas_qualified_name_regex(self) -> Any:
        """
        Regex for validating qualified name (and collecting details from qn parts)

        :returns: -
        """
        pass

    @property
    @abc.abstractmethod
    def amundsen_key_regex(self) -> Any:
        """
        Regex for validating amundsen key (and collecting details from key parts)

        :returns: -
        """
        pass

    @property
    @abc.abstractmethod
    def qualified_name(self) -> str:
        """
        Properly formatted qualified name

        :returns: -
        """
        pass

    @property
    @abc.abstractmethod
    def amundsen_key(self) -> str:
        """
        Properly formetted amundsen key

        :returns: -
        """
        pass

    @property
    def native_atlas_entity_types(self) -> Set[str]:
        """
        Atlas can be populated using two approaches:
        1. Using Atlas-provided bridge/hook tools to ingest data in push manner (like Atlas Hive Hook)
        2. Using Amundsen-provided databuilder framework in pull manner

        Since Atlas-provided tools follow different approach for rendering qualified name than databuilder does,
        to provide compatibility for both approaches we need to act differently depending whether the table entity
        was loaded by Atlas-provided or Amundsen-provided tools. We distinguish them by entity type - in Atlas the
        naming convention assumes '_table' suffix in entity name while Amundsen does not have such suffix.

        If the entity_type (database in Amundsen lingo) is one of the values from this property, we treat it like
        it was provided by Atlas and follow Atlas qualified name convention.

        If the opposite is true - we treat it like it was provided by Amundsen Databuilder, use generic entity types
        and follow Amundsen key name convention.
        """
        return {'hive_table'}

    @property
    def entity_type(self) -> str:
        if self.is_qualified_name:
            return self._database or ''
        else:
            return self.get_details()['database'] \
                if self.get_details()['database'] in self.native_atlas_entity_types else 'Table'


class AtlasTableKey(AtlasKey):
    @property
    def atlas_qualified_name_regex(self) -> Any:
        return re.compile(r'^(?P<schema>.*?)\.(?P<table>.*)@(?P<cluster>.*?)$', re.X)

    @property
    def amundsen_key_regex(self) -> Any:
        return re.compile(r'^(?P<database>.*?)://(?P<cluster>.*)\.(?P<schema>.*?)\/(?P<table>.*?)$', re.X)

    @property
    def qualified_name(self) -> str:
        if not self.is_qualified_name and self.get_details()['database'] in self.native_atlas_entity_types:
            spec = self._get_details_from_key()

            schema = spec['schema']
            table = spec['table']
            cluster = spec['cluster']

            return f'{schema}.{table}@{cluster}'
        else:
            return self._raw_identifier

    @property
    def amundsen_key(self) -> str:
        if self.is_qualified_name:
            spec = self._get_details_from_qualified_name()

            schema = spec['schema']
            table = spec['table']
            cluster = spec['cluster']

            return f'{self._database}://{cluster}.{schema}/{table}'
        elif self.is_amundsen_key:
            return self._raw_identifier
        else:
            raise ValueError(f'Value is neither qualified name nor amundsen key: {self._raw_identifier}')


class AtlasColumnKey(AtlasKey):
    @property
    def atlas_qualified_name_regex(self) -> Any:
        return re.compile(r'^(?P<schema>.*?)\.(?P<table>.*?)\.(?P<column>.*?)@(?P<cluster>.*?)$', re.X)

    @property
    def amundsen_key_regex(self) -> Any:
        return re.compile(r'^(?P<database>.*?)://(?P<cluster>.*)\.(?P<schema>.*?)\/(?P<table>.*?)\/(?P<column>.*)$',
                          re.X)

    @property
    def qualified_name(self) -> str:
        if self.is_amundsen_key:
            spec = self._get_details_from_key()

            schema = spec['schema']
            table = spec['table']
            cluster = spec['cluster']
            column = spec['column']

            return f'{schema}.{table}.{column}@{cluster}'
        elif self.is_qualified_name:
            return self._raw_identifier
        else:
            raise ValueError(f'Value is neither qualified name nor amundsen key: {self._raw_identifier}')

    @property
    def amundsen_key(self) -> str:
        if self.is_qualified_name:
            spec = self._get_details_from_qualified_name()

            schema = spec['schema']
            table = spec['table']
            cluster = spec['cluster']
            column = spec['column']

            source = self._database.replace('column', 'table') if self._database else ''

            return f'{source}://{cluster}.{schema}/{table}/{column}'
        elif self.is_amundsen_key:
            return self._raw_identifier
        else:
            raise ValueError(f'Value is neither qualified name nor amundsen key: {self._raw_identifier}')
