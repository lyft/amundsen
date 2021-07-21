# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import logging
from datetime import datetime
from typing import Any, Dict

from pyhocon import ConfigFactory, ConfigTree

from databuilder.transformer.base_transformer import Transformer

TIMESTAMP_FORMAT = 'timestamp_format'
FIELD_NAME = 'field_name'

LOGGER = logging.getLogger(__name__)

DEFAULT_CONFIG = ConfigFactory.from_dict({TIMESTAMP_FORMAT: '%Y-%m-%dT%H:%M:%S.%fZ'})


class TimestampStringToEpoch(Transformer):
    """
    Transforms string timestamp into epoch
    """

    def init(self, conf: ConfigTree) -> None:
        self._conf = conf.with_fallback(DEFAULT_CONFIG)
        self._timestamp_format = self._conf.get_string(TIMESTAMP_FORMAT)
        self._field_name = self._conf.get_string(FIELD_NAME)

    def transform(self, record: Dict[str, Any]) -> Dict[str, Any]:
        timestamp_str = record.get(self._field_name, '')

        if not timestamp_str:
            return record

        try:
            utc_dt = datetime.strptime(timestamp_str, self._timestamp_format)
        except ValueError:
            # if the timestamp_str doesn't match format, no conversion, return initial result
            record[self._field_name] = 0
            return record

        record[self._field_name] = int((utc_dt - datetime(1970, 1, 1)).total_seconds())
        return record

    def get_scope(self) -> str:
        return 'transformer.timestamp_str_to_epoch'
