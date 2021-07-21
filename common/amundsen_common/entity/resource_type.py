# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from enum import Enum, auto


class ResourceType(Enum):
    Table = auto()
    Dashboard = auto()
    User = auto()
    Column = auto()
    Feature = auto()


def to_resource_type(*, label: str) -> ResourceType:
    return ResourceType[label.title()]


def to_label(*, resource_type: ResourceType) -> str:
    return resource_type.name.lower()
