# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from enum import Enum

NODE_LABEL = 'Timestamp'

TIMESTAMP_PROPERTY = 'timestamp'
TIMESTAMP_NAME_PROPERTY = 'name'
# This is deprecated property as it's not generic for the Timestamp
DEPRECATED_TIMESTAMP_PROPERTY = 'last_updated_timestamp'


LASTUPDATED_RELATION_TYPE = 'LAST_UPDATED_AT'
LASTUPDATED_REVERSE_RELATION_TYPE = 'LAST_UPDATED_TIME_OF'


class TimestampName(Enum):
    last_updated_timestamp = 1
