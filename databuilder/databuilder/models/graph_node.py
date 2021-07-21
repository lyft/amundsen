# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from collections import namedtuple

GraphNode = namedtuple(
    'GraphNode',
    [
        'key',
        'label',
        'attributes'
    ]
)
