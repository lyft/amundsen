# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from typing import (
    Any, Iterator, Optional, Union,
)

from amundsen_rds.models import RDSModel
from amundsen_rds.models.dashboard import DashboardOwner as RDSDashboardOwner

from databuilder.models.dashboard.dashboard_metadata import DashboardMetadata
from databuilder.models.graph_node import GraphNode
from databuilder.models.owner import Owner
from databuilder.models.user import User


class DashboardOwner(Owner):
    """
    A model that encapsulate Dashboard's owner.
    Note that it does not create new user as it has insufficient information about user but it builds relation
    between User and Dashboard
    """

    def __init__(self,
                 dashboard_group_id: str,
                 dashboard_id: str,
                 email: str,
                 product: Optional[str] = '',
                 cluster: str = 'gold',
                 **kwargs: Any
                 ) -> None:

        Owner.__init__(
            self,
            start_label=DashboardMetadata.DASHBOARD_NODE_LABEL,
            start_key=DashboardMetadata.DASHBOARD_KEY_FORMAT.format(
                product=product,
                cluster=cluster,
                dashboard_group=dashboard_group_id,
                dashboard_name=dashboard_id
            ),
            owner_emails=[email]
        )
        self._email = email
        self._record_iterator = self._create_record_iterator()

    # override this because we do not want to create new User nodes from this model
    def create_next_node(self) -> Union[GraphNode, None]:
        return None

    def create_next_record(self) -> Union[RDSModel, None]:
        try:
            return next(self._record_iterator)
        except StopIteration:
            return None

    # override this because we do not want to create new User rows from this model
    def _create_record_iterator(self) -> Iterator[RDSModel]:
        yield RDSDashboardOwner(
            user_rk=User.get_user_model_key(email=self._email),
            dashboard_rk=self.start_key,
        )
