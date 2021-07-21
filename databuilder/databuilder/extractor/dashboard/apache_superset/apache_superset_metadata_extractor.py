# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0


from typing import (
    Any, Dict, Iterator, List, Union,
)

from databuilder.extractor.dashboard.apache_superset.apache_superset_extractor import (
    ApacheSupersetBaseExtractor, type_fields_mapping,
)
from databuilder.models.dashboard.dashboard_last_modified import DashboardLastModifiedTimestamp
from databuilder.models.dashboard.dashboard_metadata import DashboardMetadata


class ApacheSupersetMetadataExtractor(ApacheSupersetBaseExtractor):
    def last_modified_field_mappings(self) -> type_fields_mapping:
        result = [
            ('dashboard_id', 'result.id', lambda x: str(x), ''),
            ('dashboard_name', 'result.dashboard_title', None, ''),
            ('last_modified_timestamp', 'result.changed_on',
             lambda _date: self.parse_date(_date), 0)
        ]

        return result

    def dashboard_metadata_field_mappings(self) -> type_fields_mapping:
        result = [
            ('dashboard_id', 'result.id', lambda x: str(x), ''),
            ('dashboard_name', 'result.dashboard_title', None, ''),
            ('dashboard_url', 'result.url', lambda x: self.base_url + x, ''),
            ('created_timestamp', 'result.created_on', None, 0),  # currently not available in superset dashboard api
            ('tags', '', lambda x: [x] if x else [], []),  # not available
            ('description', 'result.description', None, '')  # currently not available in superset dashboard api
        ]

        return result

    def _get_extract_iter(self) -> Iterator[Union[DashboardMetadata, DashboardLastModifiedTimestamp, None]]:
        ids = self._get_dashboard_ids()

        data = [self._get_dashboard_details(i) for i in ids]

        if self.extract_published_only:
            data = [d for d in data if self.get_nested_field(d, 'result.published')]

        for entry in data:
            dashboard_metadata = self.map_fields(entry, self.dashboard_metadata_field_mappings())
            dashboard_metadata.update(**self.common_params)

            yield DashboardMetadata(**dashboard_metadata)

            dashboard_last_modified = self.map_fields(entry, self.last_modified_field_mappings())
            dashboard_last_modified.update(**self.common_params)

            yield DashboardLastModifiedTimestamp(**dashboard_last_modified)

    def _get_dashboard_ids(self) -> List[str]:
        url = self.build_full_url('api/v1/dashboard')

        data = self.execute_query(url)

        return data.get('ids', [])

    def _get_dashboard_details(self, dashboard_id: str) -> Dict[str, Any]:
        url = self.build_full_url(f'api/v1/dashboard/{dashboard_id}')

        data = self.execute_query(url)

        return data
