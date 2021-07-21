# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from typing import (
    Any, Optional, Union,
)

from amundsen_rds.models import RDSModel
from amundsen_rds.models.user import User as RDSUser

from databuilder.models.dashboard.dashboard_metadata import DashboardMetadata
from databuilder.models.graph_node import GraphNode
from databuilder.models.usage.usage import Usage


class DashboardUsage(Usage):
    """
    A model that encapsulate Dashboard usage between Dashboard and User
    """

    def __init__(self,
                 dashboard_group_id: Optional[str],
                 dashboard_id: Optional[str],
                 email: str,
                 view_count: int,
                 should_create_user_node: Optional[bool] = False,
                 product: Optional[str] = '',
                 cluster: Optional[str] = 'gold',
                 **kwargs: Any
                 ) -> None:
        """
        :param dashboard_group_id:
        :param dashboard_id:
        :param email:
        :param view_count:
        :param should_create_user_node: Enable this if it is fine to create/update User node with only with email
        address. Please be advised that other fields will be emptied. Current use case is to create anonymous user.
        For example, Mode dashboard does not provide which user viewed the dashboard and anonymous user can be used
        to show the usage.
        :param product:
        :param cluster:
        :param kwargs:
        """
        self._should_create_user_node = bool(should_create_user_node)
        Usage.__init__(
            self,
            start_label=DashboardMetadata.DASHBOARD_NODE_LABEL,
            start_key=DashboardMetadata.DASHBOARD_KEY_FORMAT.format(
                product=product,
                cluster=cluster,
                dashboard_group=dashboard_group_id,
                dashboard_name=dashboard_id
            ),
            user_email=email,
            read_count=view_count,
        )

    # override superclass for customized _should_create_user_node behavior
    def create_next_node(self) -> Union[GraphNode, None]:
        if self._should_create_user_node:
            return super().create_next_node()
        return None

    # override superclass for customized _should_create_user_node behavior
    def create_next_record(self) -> Union[RDSModel, None]:
        rec = super().create_next_record()
        if isinstance(rec, RDSUser) and not self._should_create_user_node:
            rec = super().create_next_record()
        return rec
