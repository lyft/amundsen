# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from collections import namedtuple

AtlasEntity = namedtuple(
    'AtlasEntity',
    [
        'operation',
        'typeName',
        'relationships',
        'attributes'
    ]
)
