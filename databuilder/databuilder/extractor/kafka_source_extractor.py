# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import importlib
import logging
from datetime import datetime, timedelta
from typing import Any

from confluent_kafka import (
    Consumer, KafkaError, KafkaException,
)
from pyhocon import ConfigTree

from databuilder import Scoped
from databuilder.callback.call_back import Callback
from databuilder.extractor.base_extractor import Extractor
from databuilder.transformer.base_transformer import Transformer

LOGGER = logging.getLogger(__name__)


class KafkaSourceExtractor(Extractor, Callback):
    """
    Kafka source extractor. The extractor itself is single consumer(single-threaded)
    which could consume all the partitions given a topic or a subset of partitions.

    It uses the "micro-batch" concept to ingest data from a given Kafka topic and
    persist into downstream sink.
    Once the publisher commit successfully, it will trigger the extractor's callback to commit the
    consumer offset.
    """
    # The dict of Kafka consumer config
    CONSUMER_CONFIG = 'consumer_config'
    # The consumer group id. Ideally each Kafka extractor should only associate with one consumer group.
    CONSUMER_GROUP_ID = 'group.id'
    # We don't deserde the key of the message.
    # CONSUMER_VALUE_DESERDE = 'value.deserializer'
    # Each Kafka extractor should only consume one single topic. We could extend to consume more topic if needed.
    TOPIC_NAME_LIST = 'topic_name_list'

    # Time out config. It will abort from reading the Kafka topic after timeout is reached. Unit is seconds
    CONSUMER_TOTAL_TIMEOUT_SEC = 'consumer_total_timeout_sec'

    # The timeout for consumer polling messages. Default to 1 sec
    CONSUMER_POLL_TIMEOUT_SEC = 'consumer_poll_timeout_sec'

    # Config on whether we throw exception if transformation fails
    TRANSFORMER_THROWN_EXCEPTION = 'transformer_thrown_exception'

    # The value transformer to deserde the Kafka message
    RAW_VALUE_TRANSFORMER = 'raw_value_transformer'

    def init(self, conf: ConfigTree) -> None:
        self.conf = conf
        self.consumer_config = conf.get_config(KafkaSourceExtractor.CONSUMER_CONFIG).\
            as_plain_ordered_dict()

        self.topic_names: list = conf.get_list(KafkaSourceExtractor.TOPIC_NAME_LIST)

        if not self.topic_names:
            raise Exception('Kafka topic needs to be provided by the user.')

        self.consumer_total_timeout = conf.get_int(KafkaSourceExtractor.CONSUMER_TOTAL_TIMEOUT_SEC,
                                                   default=10)

        self.consumer_poll_timeout = conf.get_int(KafkaSourceExtractor.CONSUMER_POLL_TIMEOUT_SEC,
                                                  default=1)

        self.transformer_thrown_exception = conf.get_bool(KafkaSourceExtractor.TRANSFORMER_THROWN_EXCEPTION,
                                                          default=False)

        # Transform the protoBuf message with a transformer
        val_transformer = conf.get(KafkaSourceExtractor.RAW_VALUE_TRANSFORMER)
        if val_transformer is None:
            raise Exception('A message transformer should be provided.')
        else:
            try:
                module_name, class_name = val_transformer.rsplit(".", 1)
                mod = importlib.import_module(module_name)
                self.transformer = getattr(mod, class_name)()
            except Exception:
                raise RuntimeError('The Kafka message value deserde class cant instantiated!')

            if not isinstance(self.transformer, Transformer):
                raise Exception('The transformer needs to be subclass of the base transformer')
            self.transformer.init(Scoped.get_scoped_conf(conf, self.transformer.get_scope()))

        # Consumer init
        try:
            # Disable enable.auto.commit
            self.consumer_config['enable.auto.commit'] = False

            self.consumer = Consumer(self.consumer_config)
            # TODO: to support only consume a subset of partitions.
            self.consumer.subscribe(self.topic_names)
        except Exception:
            raise RuntimeError('Consumer could not start correctly!')

    def extract(self) -> Any:
        """
        :return: Provides a record or None if no more to extract
        """
        records = self.consume()
        for record in records:
            try:
                transform_record = self.transformer.transform(record=record)
                yield transform_record
            except Exception as e:
                # Has issues tranform / deserde the record. drop the record in default
                LOGGER.exception(e)
                if self.transformer_thrown_exception:
                    # if config enabled, it will throw exception.
                    # Users need to figure out how to rewind the consumer offset
                    raise Exception('Encounter exception when transform the record')

    def on_success(self) -> None:
        """
        Commit the offset
        once:
            1. get the success callback from publisher in
            https://github.com/amundsen-io/amundsendatabuilder/blob/
            master/databuilder/publisher/base_publisher.py#L50
            2. close the consumer.

        :return:
        """
        # set enable.auto.commit to False to avoid auto commit offset
        if self.consumer:
            self.consumer.commit(asynchronous=False)
            self.consumer.close()

    def on_failure(self) -> None:
        if self.consumer:
            self.consumer.close()

    def consume(self) -> Any:
        """
        Consume messages from a give list of topic

        :return:
        """
        records = []
        start = datetime.now()
        try:
            while True:
                msg = self.consumer.poll(timeout=self.consumer_poll_timeout)
                end = datetime.now()

                # The consumer exceeds consume timeout
                if (end - start) > timedelta(seconds=self.consumer_total_timeout):
                    # Exceed the consume timeout
                    break

                if msg is None:
                    continue

                if msg.error():
                    # Hit the EOF of partition
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    else:
                        raise KafkaException(msg.error())
                else:
                    records.append(msg.value())

        except Exception as e:
            LOGGER.exception(e)
        finally:
            return records

    def get_scope(self) -> str:
        return 'extractor.kafka_source'
