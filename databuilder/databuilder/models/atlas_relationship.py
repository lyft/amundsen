# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0
from collections import namedtuple

AtlasRelationship = namedtuple(
    'AtlasRelationship',
    [
        'relationshipType',
        'entityType1',
        'entityQualifiedName1',
        'entityType2',
        'entityQualifiedName2',
        'attributes',
    ],
)
