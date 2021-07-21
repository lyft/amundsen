# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from typing import (
    Iterator, List, Optional, Union,
)

from amundsen_common.utils.atlas import AtlasCommonParams, AtlasCommonTypes
from amundsen_rds.models import RDSModel
from amundsen_rds.models.dashboard import DashboardOwner as RDSDashboardOwner
from amundsen_rds.models.table import TableOwner as RDSTableOwner
from amundsen_rds.models.user import User as RDSUser

from databuilder.models.atlas_entity import AtlasEntity
from databuilder.models.atlas_relationship import AtlasRelationship
from databuilder.models.atlas_serializable import AtlasSerializable
from databuilder.models.dashboard.dashboard_metadata import DashboardMetadata
from databuilder.models.graph_node import GraphNode
from databuilder.models.graph_relationship import GraphRelationship
from databuilder.models.graph_serializable import GraphSerializable
from databuilder.models.owner_constants import OWNER_OF_OBJECT_RELATION_TYPE, OWNER_RELATION_TYPE
from databuilder.models.table_metadata import TableMetadata
from databuilder.models.table_serializable import TableSerializable
from databuilder.models.user import User
from databuilder.serializers.atlas_serializer import get_entity_attrs
from databuilder.utils.atlas import AtlasRelationshipTypes, AtlasSerializedEntityOperation


class Owner(GraphSerializable, TableSerializable, AtlasSerializable):
    LABELS_PERMITTED_TO_HAVE_OWNER = ['Table', 'Dashboard', 'Feature']

    def __init__(self,
                 start_label: str,
                 start_key: str,
                 owner_emails: Union[List, str],
                 ) -> None:
        if start_label not in Owner.LABELS_PERMITTED_TO_HAVE_OWNER:
            raise Exception(f'owners for {start_label} are not supported')
        self.start_label = start_label
        self.start_key = start_key
        if isinstance(owner_emails, str):
            owner_emails = owner_emails.split(',')
        self.owner_emails = [email.strip().lower() for email in owner_emails]

        self._node_iter = self._create_node_iterator()
        self._relation_iter = self._create_relation_iterator()
        self._record_iter = self._create_record_iterator()
        self._atlas_entity_iterator = self._create_next_atlas_entity()
        self._atlas_relation_iterator = self._create_atlas_relation_iterator()

    def __repr__(self) -> str:
        return f'Owner({self.start_label!r}, {self.start_key!r}, {self.owner_emails!r})'

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

    def create_next_record(self) -> Union[RDSModel, None]:
        try:
            return next(self._record_iter)
        except StopIteration:
            return None

    def _create_node_iterator(self) -> Iterator[GraphNode]:
        for email in self.owner_emails:
            if email:
                yield GraphNode(
                    key=User.get_user_model_key(email=email),
                    label=User.USER_NODE_LABEL,
                    attributes={
                        User.USER_NODE_EMAIL: email,
                    }
                )

    def _create_relation_iterator(self) -> Iterator[GraphRelationship]:
        for email in self.owner_emails:
            if email:
                yield GraphRelationship(
                    start_label=self.start_label,
                    start_key=self.start_key,
                    end_label=User.USER_NODE_LABEL,
                    end_key=User.get_user_model_key(email=email),
                    type=OWNER_RELATION_TYPE,
                    reverse_type=OWNER_OF_OBJECT_RELATION_TYPE,
                    attributes={}
                )

    def _create_record_iterator(self) -> Iterator[RDSModel]:
        for email in self.owner_emails:
            if email:
                user_record = RDSUser(
                    rk=User.get_user_model_key(email=email),
                    email=email
                )
                yield user_record

                if self.start_label == TableMetadata.TABLE_NODE_LABEL:
                    yield RDSTableOwner(
                        table_rk=self.start_key,
                        user_rk=User.get_user_model_key(email=email),
                    )
                elif self.start_label == DashboardMetadata.DASHBOARD_NODE_LABEL:
                    yield RDSDashboardOwner(
                        dashboard_rk=self.start_key,
                        user_rk=User.get_user_model_key(email=email)
                    )
                else:
                    raise Exception(f'{self.start_label}<>Owner relationship is not table serializable')

    def _create_atlas_owner_entity(self, owner: str) -> AtlasEntity:
        attrs_mapping = [
            (AtlasCommonParams.qualified_name, owner),
            ('email', owner)
        ]

        entity_attrs = get_entity_attrs(attrs_mapping)

        entity = AtlasEntity(
            typeName=AtlasCommonTypes.user,
            operation=AtlasSerializedEntityOperation.CREATE,
            attributes=entity_attrs,
            relationships=None
        )

        return entity

    def _create_atlas_owner_relation(self, owner: str) -> AtlasRelationship:
        table_relationship = AtlasRelationship(
            relationshipType=AtlasRelationshipTypes.resource_owner,
            entityType1=AtlasCommonTypes.data_set,
            entityQualifiedName1=self.start_key,
            entityType2=AtlasCommonTypes.user,
            entityQualifiedName2=User.get_user_model_key(email=owner),
            attributes={}
        )

        return table_relationship

    def _create_next_atlas_entity(self) -> Iterator[AtlasEntity]:
        for owner in self.owner_emails:
            if owner:
                yield self._create_atlas_owner_entity(owner)

    def create_next_atlas_entity(self) -> Union[AtlasEntity, None]:
        try:
            return next(self._atlas_entity_iterator)
        except StopIteration:
            return None

    def create_next_atlas_relation(self) -> Union[AtlasRelationship, None]:
        try:
            return next(self._atlas_relation_iterator)
        except StopIteration:
            return None

    def _create_atlas_relation_iterator(self) -> Iterator[AtlasRelationship]:
        for owner in self.owner_emails:
            if owner:
                yield self._create_atlas_owner_relation(owner)
