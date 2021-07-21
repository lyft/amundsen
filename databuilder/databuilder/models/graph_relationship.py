# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from collections import namedtuple

GraphRelationship = namedtuple(
    'GraphRelationship',
    [
        'start_label',
        'end_label',
        'start_key',
        'end_key',
        'type',
        'reverse_type',
        'attributes'
    ]
)
