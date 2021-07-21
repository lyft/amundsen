# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import logging
import unittest

from mock import MagicMock, patch
from pyhocon import ConfigFactory

from databuilder import Scoped
from databuilder.extractor.kafka_source_extractor import KafkaSourceExtractor


class TestKafkaSourceExtractor(unittest.TestCase):
    def setUp(self) -> None:
        logging.basicConfig(level=logging.INFO)
        config_dict = {
            'extractor.kafka_source.consumer_config': {'"group.id"': 'consumer-group', '"enable.auto.commit"': False},
            f'extractor.kafka_source.{KafkaSourceExtractor.RAW_VALUE_TRANSFORMER}':
                'databuilder.transformer.base_transformer.NoopTransformer',
            f'extractor.kafka_source.{KafkaSourceExtractor.TOPIC_NAME_LIST}': ['test-topic'],
            f'extractor.kafka_source.{KafkaSourceExtractor.CONSUMER_TOTAL_TIMEOUT_SEC}': 1,
        }
        self.conf = ConfigFactory.from_dict(config_dict)

    def test_consume_success(self) -> None:
        kafka_extractor = KafkaSourceExtractor()
        kafka_extractor.init(Scoped.get_scoped_conf(conf=self.conf,
                                                    scope=kafka_extractor.get_scope()))

        with patch.object(kafka_extractor, 'consumer') as mock_consumer:
            mock_poll = MagicMock()
            mock_poll.error.return_value = False
            # only return once
            mock_poll.value.side_effect = ['msg']
            mock_consumer.poll.return_value = mock_poll

            records = kafka_extractor.consume()
            self.assertEqual(len(records), 1)

    def test_consume_fail(self) -> None:
        kafka_extractor = KafkaSourceExtractor()
        kafka_extractor.init(Scoped.get_scoped_conf(conf=self.conf,
                                                    scope=kafka_extractor.get_scope()))

        with patch.object(kafka_extractor, 'consumer') as mock_consumer:
            mock_poll = MagicMock()
            mock_poll.error.return_value = True
            mock_consumer.poll.return_value = mock_poll

            records = kafka_extractor.consume()
            self.assertEqual(len(records), 0)
