# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0


from functools import lru_cache
from typing import (
    Any, Dict, Iterator, List, Union,
)

from sqlalchemy.engine.url import make_url

from databuilder.extractor.dashboard.apache_superset.apache_superset_extractor import ApacheSupersetBaseExtractor
from databuilder.models.dashboard.dashboard_table import DashboardTable
from databuilder.models.table_metadata import TableMetadata


class ApacheSupersetTableExtractor(ApacheSupersetBaseExtractor):
    def _get_extract_iter(self) -> Iterator[Union[DashboardTable, None]]:
        dashboards: Dict[str, set] = dict()

        ids = self._get_dataset_ids()

        data = [(self._get_dataset_details(i), self._get_dataset_related_objects(i)) for i in ids]

        for entry in data:
            dataset_details, dataset_objects = entry

            database_id = self.get_nested_field(dataset_details, 'result.database.id')

            if database_id:
                database_details = self._get_database_details(database_id)

                sql = self.get_nested_field(dataset_details, 'result.sql') or ''

                # if sql exists then table_name cannot be associated with physical table in db
                if not len(sql) > 0:
                    uri = self.get_nested_field(database_details, 'result.sqlalchemy_uri')
                    database_spec = make_url(uri)

                    db = self.driver_mapping.get(database_spec.drivername, database_spec.drivername)
                    schema = database_spec.database

                    cluster = self.cluster_mapping.get(database_id, self.cluster)
                    tbl = self.get_nested_field(dataset_details, 'result.table_name')

                    table_key = TableMetadata.TABLE_KEY_FORMAT.format(db=db,
                                                                      cluster=cluster,
                                                                      schema=schema,
                                                                      tbl=tbl)

                    for dashboard in dataset_objects.get('dashboards', dict()).get('result', []):
                        dashboard_id = str(dashboard.get('id'))

                        if not dashboards.get(dashboard_id):
                            dashboards[dashboard_id] = set()

                        dashboards[dashboard_id].add(table_key)
                else:
                    pass
            else:
                continue

        for dashboard_id, table_keys in dashboards.items():
            table_metadata: Dict[str, Any] = {'dashboard_id': dashboard_id, 'table_ids': table_keys}

            table_metadata.update(**self.common_params)

            result = DashboardTable(**table_metadata)

            yield result

    def _get_dataset_ids(self) -> List[str]:
        url = self.build_full_url('api/v1/dataset')

        data = self.execute_query(url)

        return data.get('ids', [])

    def _get_dataset_details(self, dataset_id: str) -> Dict[str, Any]:
        url = self.build_full_url(f'api/v1/dataset/{dataset_id}')

        data = self.execute_query(url)

        return data

    def _get_dataset_related_objects(self, dataset_id: str) -> Dict[str, Any]:
        url = self.build_full_url(f'api/v1/dataset/{dataset_id}/related_objects')

        data = self.execute_query(url)

        return data

    @lru_cache(maxsize=512)
    def _get_database_details(self, database_id: str) -> Dict[str, Any]:
        url = self.build_full_url(f'api/v1/database/{database_id}')

        data = self.execute_query(url)

        return data

    @property
    def driver_mapping(self) -> Dict[str, str]:
        return dict(self.conf.get(self.DRIVER_TO_DATABASE_MAPPING))

    @property
    def cluster_mapping(self) -> Dict[str, str]:
        return dict(self.conf.get(self.DATABASE_TO_CLUSTER_MAPPING))
