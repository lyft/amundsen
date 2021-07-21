# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import unittest

from pyhocon import ConfigFactory

from databuilder import Scoped
from databuilder.extractor.generic_extractor import GenericExtractor


class TestGenericExtractor(unittest.TestCase):

    def test_extraction_with_model_class(self) -> None:
        """
        Test Extraction using model class
        """
        config_dict = {
            'extractor.generic.extraction_items': [{'timestamp': 10000000}],
            'extractor.generic.model_class': 'databuilder.models.es_last_updated.ESLastUpdated',
        }
        conf = ConfigFactory.from_dict(config_dict)

        extractor = GenericExtractor()
        self.conf = ConfigFactory.from_dict(config_dict)
        extractor.init(Scoped.get_scoped_conf(conf=conf,
                                              scope=extractor.get_scope()))

        result = extractor.extract()
        self.assertEqual(result.timestamp, 10000000)

    def test_extraction_without_model_class(self) -> None:
        """
        Test Extraction using model class
        """
        config_dict = {
            'extractor.generic.extraction_items': [{'foo': 1}, {'bar': 2}],
        }
        conf = ConfigFactory.from_dict(config_dict)

        extractor = GenericExtractor()
        self.conf = ConfigFactory.from_dict(config_dict)
        extractor.init(Scoped.get_scoped_conf(conf=conf,
                                              scope=extractor.get_scope()))

        self.assertEqual(extractor.extract(), {'foo': 1})
        self.assertEqual(extractor.extract(), {'bar': 2})
