# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import unittest

from pyhocon import ConfigFactory

from databuilder.extractor.restapi.rest_api_extractor import (
    MODEL_CLASS, REST_API_QUERY, STATIC_RECORD_DICT, RestAPIExtractor,
)
from databuilder.models.dashboard.dashboard_metadata import DashboardMetadata
from databuilder.rest_api.base_rest_api_query import RestApiQuerySeed


class TestRestAPIExtractor(unittest.TestCase):

    def test_static_data(self) -> None:

        conf = ConfigFactory.from_dict(
            {
                REST_API_QUERY: RestApiQuerySeed(seed_record=[{'foo': 'bar'}]),
                STATIC_RECORD_DICT: {'john': 'doe'}
            }
        )
        extractor = RestAPIExtractor()
        extractor.init(conf=conf)

        record = extractor.extract()
        expected = {'foo': 'bar', 'john': 'doe'}

        self.assertDictEqual(expected, record)

    def test_model_construction(self) -> None:
        conf = ConfigFactory.from_dict(
            {
                REST_API_QUERY: RestApiQuerySeed(
                    seed_record=[{'dashboard_group': 'foo',
                                  'dashboard_name': 'bar',
                                  'description': 'john',
                                  'dashboard_group_description': 'doe'}]),
                MODEL_CLASS: 'databuilder.models.dashboard.dashboard_metadata.DashboardMetadata',
            }
        )
        extractor = RestAPIExtractor()
        extractor.init(conf=conf)

        record = extractor.extract()
        expected = DashboardMetadata(dashboard_group='foo', dashboard_name='bar', description='john',
                                     dashboard_group_description='doe')

        self.assertEqual(expected.__repr__(), record.__repr__())
