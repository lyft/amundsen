# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0
import unittest
from typing import Any

from mock import MagicMock, Mock
from pyhocon import ConfigFactory

from databuilder import Scoped
from databuilder.extractor.dashboard.apache_superset.apache_superset_table_extractor import ApacheSupersetTableExtractor
from databuilder.models.dashboard.dashboard_table import DashboardTable

dataset_data_response_1 = {
    'result': {
        'sql': None,
        'table_name': 'table_name',
        'database': {
            'id': 1
        }
    }
}

dataset_objects_data_response_1 = {
    'dashboards': {
        'result': [
            {
                'id': 2
            }
        ]
    }
}

database_data_response_1 = {
    'result': {
        'sqlalchemy_uri': 'postgresql://localhost:5432/db_name'
    }
}

dataset_data_response_2 = {
    'result': {
        'sql': None,
        'table_name': 'table_name_2',
        'database': {
            'id': 3
        }
    }
}

dataset_objects_data_response_2 = {
    'dashboards': {
        'result': [
            {
                'id': 2
            }
        ]
    }
}

database_data_response_2 = {
    'result': {
        'sqlalchemy_uri': 'postgresql://localhost:5432/db_name_2'
    }
}


class TestApacheSupersetTableExtractor(unittest.TestCase):
    def setUp(self) -> None:
        config = ConfigFactory.from_dict({
            'extractor.apache_superset.dashboard_group_id': '1',
            'extractor.apache_superset.dashboard_group_name': 'dashboard group',
            'extractor.apache_superset.dashboard_group_description': 'dashboard group description',
            'extractor.apache_superset.cluster': 'gold',
            'extractor.apache_superset.apache_superset_security_settings_dict': dict(username='admin',
                                                                                     password='admin',
                                                                                     provider='db')
        })

        self.config = config

    def _get_extractor(self) -> Any:
        extractor = self._extractor_class()
        extractor.authenticate = MagicMock()
        extractor.init(Scoped.get_scoped_conf(conf=self.config, scope=extractor.get_scope()))

        return extractor

    @property
    def _extractor_class(self) -> Any:
        return ApacheSupersetTableExtractor

    def test_extractor(self) -> None:
        extractor = self._get_extractor()

        extractor.execute_query = Mock(side_effect=[{'ids': [2, 3]},
                                                    dataset_data_response_1, dataset_objects_data_response_1,
                                                    dataset_data_response_2, dataset_objects_data_response_2,
                                                    database_data_response_1, database_data_response_2])

        record = extractor.extract()

        self.assertIsInstance(record, DashboardTable)
        self.assertEquals(record._dashboard_id, '2')
        self.assertSetEqual(record._table_ids,
                            {'postgres://gold.db_name/table_name', 'postgres://gold.db_name_2/table_name_2'})
