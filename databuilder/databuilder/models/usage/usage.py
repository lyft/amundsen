# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from typing import Iterator, Optional

from amundsen_rds.models import RDSModel
from amundsen_rds.models.dashboard import DashboardUsage as RDSDashboardUsage
from amundsen_rds.models.table import TableUsage as RDSTableUsage
from amundsen_rds.models.user import User as RDSUser

from databuilder.models.dashboard.dashboard_metadata import DashboardMetadata
from databuilder.models.graph_node import GraphNode
from databuilder.models.graph_relationship import GraphRelationship
from databuilder.models.graph_serializable import GraphSerializable
from databuilder.models.table_metadata import TableMetadata
from databuilder.models.table_serializable import TableSerializable
from databuilder.models.usage.usage_constants import (
    READ_RELATION_COUNT_PROPERTY, READ_RELATION_TYPE, READ_REVERSE_RELATION_TYPE,
)
from databuilder.models.user import User


class Usage(GraphSerializable, TableSerializable):
    LABELS_PERMITTED_TO_HAVE_USAGE = ['Table', 'Dashboard', 'Feature']

    def __init__(self,
                 start_label: str,
                 start_key: str,
                 user_email: str,
                 read_count: int = 1) -> None:

        if start_label not in Usage.LABELS_PERMITTED_TO_HAVE_USAGE:
            raise Exception(f'usage for {start_label} is not supported')

        self.start_label = start_label
        self.start_key = start_key
        self.user_email = user_email.strip().lower()
        self.read_count = int(read_count)

        self._node_iter = self._create_node_iterator()
        self._relation_iter = self._create_relation_iterator()
        self._record_iter = self._create_record_iterator()

    def __repr__(self) -> str:
        return f"Usage(start_label={self.start_label!r}, start_key={self.start_key!r}, " \
               f"user_email={self.user_email!r}, read_count={self.read_count!r})"

    def create_next_node(self) -> Optional[GraphNode]:
        try:
            return next(self._node_iter)
        except StopIteration:
            return None

    def create_next_relation(self) -> Optional[GraphRelationship]:
        try:
            return next(self._relation_iter)
        except StopIteration:
            return None

    def create_next_record(self) -> Optional[RDSModel]:
        try:
            return next(self._record_iter)
        except StopIteration:
            return None

    def _create_node_iterator(self) -> Iterator[GraphNode]:
        if self.user_email:
            yield GraphNode(
                key=User.get_user_model_key(email=self.user_email),
                label=User.USER_NODE_LABEL,
                attributes={
                    User.USER_NODE_EMAIL: self.user_email,
                }
            )

    def _create_relation_iterator(self) -> Iterator[GraphRelationship]:
        yield GraphRelationship(
            start_label=self.start_label,
            start_key=self.start_key,
            end_label=User.USER_NODE_LABEL,
            end_key=User.get_user_model_key(email=self.user_email),
            type=READ_REVERSE_RELATION_TYPE,
            reverse_type=READ_RELATION_TYPE,
            attributes={
                READ_RELATION_COUNT_PROPERTY: self.read_count,
            }
        )

    def _create_record_iterator(self) -> Iterator[RDSModel]:
        if self.user_email:
            yield RDSUser(
                rk=User.get_user_model_key(email=self.user_email),
                email=self.user_email
            )

        if self.start_label == TableMetadata.TABLE_NODE_LABEL:
            yield RDSTableUsage(user_rk=User.get_user_model_key(email=self.user_email),
                                table_rk=self.start_key,
                                read_count=self.read_count)
        elif self.start_label == DashboardMetadata.DASHBOARD_NODE_LABEL:
            yield RDSDashboardUsage(
                user_rk=User.get_user_model_key(email=self.user_email),
                dashboard_rk=self.start_key,
                read_count=self.read_count,
            )
        else:
            raise Exception(f'{self.start_label} usage is not table serializable')
