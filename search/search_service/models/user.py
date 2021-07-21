# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0


from typing import (
    List, Optional, Set,
)

import attr
from amundsen_common.models.user import User as CommonUser
from marshmallow3_annotations.ext.attrs import AttrsSchema

from search_service.models.base import Base


@attr.s(auto_attribs=True, kw_only=True)
class User(Base, CommonUser):
    """
    This represents the part of a user stored in the search proxy
    """
    manager_email: Optional[str] = None
    id: str

    def get_id(self) -> str:
        return self.id

    def get_attrs_dict(self) -> dict:
        return self.__dict__.copy()

    @classmethod
    def get_attrs(cls) -> Set:
        return {
            'id',
            'full_name',
            'first_name',
            'last_name',
            'team_name',
            'email',
            'manager_email',
            'github_username',
            'is_active',
            'employee_type',
            'role_name',
        }

    @staticmethod
    def get_type() -> str:
        return 'user'


class UserSchema(AttrsSchema):
    class Meta:
        target = User
        register_as_scheme = True


@attr.s(auto_attribs=True, kw_only=True)
class SearchUserResult:
    total_results: int = attr.ib()
    results: List[User] = attr.ib(factory=list)


class SearchUserResultSchema(AttrsSchema):
    class Meta:
        target = SearchUserResult
        register_as_scheme = True
