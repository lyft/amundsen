# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import unittest
from typing import Any

from mock import patch
from pyhocon import ConfigFactory

from databuilder import Scoped
from databuilder.extractor.es_last_updated_extractor import EsLastUpdatedExtractor


class TestEsLastUpdatedExtractor(unittest.TestCase):

    def setUp(self) -> None:
        config_dict = {
            'extractor.es_last_updated.model_class':
                'databuilder.models.es_last_updated.ESLastUpdated',
        }
        self.conf = ConfigFactory.from_dict(config_dict)

    @patch('time.time')
    def test_extraction_with_model_class(self, mock_time: Any) -> None:
        """
        Test Extraction using model class
        """
        mock_time.return_value = 10000000
        extractor = EsLastUpdatedExtractor()
        extractor.init(Scoped.get_scoped_conf(conf=self.conf,
                                              scope=extractor.get_scope()))

        result = extractor.extract()
        self.assertEqual(result.timestamp, 10000000)
