# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0


from typing import (
    Any, Dict, Iterator, List, Tuple, Union,
)

from databuilder.extractor.dashboard.apache_superset.apache_superset_extractor import (
    ApacheSupersetBaseExtractor, type_fields_mapping,
)
from databuilder.models.dashboard.dashboard_chart import DashboardChart
from databuilder.models.dashboard.dashboard_query import DashboardQuery


class ApacheSupersetChartExtractor(ApacheSupersetBaseExtractor):
    def chart_field_mappings(self) -> type_fields_mapping:
        result = [
            ('chart_id', 'id', lambda x: str(x), ''),
            ('chart_name', 'slice_name', None, ''),
            ('chart_type', 'viz_type', None, ''),
            ('chart_url', 'url', None, ''),  # currently not available in superset chart api
        ]

        return result

    def _get_extract_iter(self) -> Iterator[Union[DashboardQuery, DashboardChart, None]]:
        ids = self._get_dashboard_ids()

        data = [self._get_dashboard_details(i) for i in ids]

        for entry in data:
            dashboard_id, dashboard_data = entry

            # Since Apache Superset doesn't support dashboard <> query <> chart relation we create a dummy 'bridge'
            # query node so we can connect charts to a dashboard
            dashboard_query_data = dict(dashboard_id=dashboard_id,
                                        query_name='default',
                                        query_id=self.dummy_query_id,
                                        url='',
                                        query_text='')
            dashboard_query_data.update(**self.common_params)

            yield DashboardQuery(**dashboard_query_data)

            charts = [s.get('__Slice__') for s in dashboard_data.get('slices', [])]

            for chart in charts:
                if chart:
                    dashboard_chart_data = self.map_fields(chart, self.chart_field_mappings())
                    dashboard_chart_data.update(**{**dict(dashboard_id=dashboard_id, query_id=self.dummy_query_id),
                                                   **self.common_params})

                    yield DashboardChart(**dashboard_chart_data)

    def _get_dashboard_ids(self) -> List[str]:
        url = self.build_full_url('api/v1/dashboard')

        data = self.execute_query(url)

        return data.get('ids', [])

    def _get_dashboard_details(self, dashboard_id: str) -> Tuple[str, Dict[str, Any]]:
        url = self.build_full_url(f'api/v1/dashboard/export?q=[{dashboard_id}]')

        _data = self.execute_query(url)

        dashboard_data = _data.get('dashboards', [])[0].get('__Dashboard__', dict())

        data = dashboard_id, dashboard_data

        return data

    @property
    def dummy_query_id(self) -> str:
        return '-1'
