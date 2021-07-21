# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from typing import Any, Optional, Dict

import attr
from marshmallow import EXCLUDE, ValidationError, validates_schema, pre_load
from marshmallow3_annotations.ext.attrs import AttrsSchema

"""
TODO: Explore all internationalization use cases and
redesign how User handles names

TODO - Delete pre processing of the Data
Once all of the upstream services provide a complete User object we will no
longer need to supplement the User objects as done in `preprocess_data`
"""


@attr.s(auto_attribs=True, kw_only=True)
class User:
    # ToDo (Verdan): Make user_id a required field.
    #  In case if there is only email, id could be email.
    #  All the transactions and communication will be handled by ID
    user_id: Optional[str] = None
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    display_name: Optional[str] = None
    is_active: bool = True
    github_username: Optional[str] = None
    team_name: Optional[str] = None
    slack_id: Optional[str] = None
    employee_type: Optional[str] = None
    manager_fullname: Optional[str] = None
    manager_email: Optional[str] = None
    manager_id: Optional[str] = None
    role_name: Optional[str] = None
    profile_url: Optional[str] = None
    other_key_values: Optional[Dict[str, str]] = attr.ib(factory=dict)  # type: ignore
    # TODO: Add frequent_used, bookmarked, & owned resources


class UserSchema(AttrsSchema):
    class Meta:
        target = User
        register_as_scheme = True
        unknown = EXCLUDE

    # noinspection PyMethodMayBeStatic
    def _str_no_value(self, s: Optional[str]) -> bool:
        # Returns True if the given string is None or empty
        if not s:
            return True
        if len(s.strip()) == 0:
            return True
        return False

    @pre_load
    def preprocess_data(self, data: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        if self._str_no_value(data.get('user_id')):
            data['user_id'] = data.get('email')

        if self._str_no_value(data.get('profile_url')):
            data['profile_url'] = ''
            if data.get('GET_PROFILE_URL'):
                data['profile_url'] = data.get('GET_PROFILE_URL')(data['user_id'])  # type: ignore

        first_name = data.get('first_name')
        last_name = data.get('last_name')

        if self._str_no_value(data.get('full_name')) and first_name and last_name:
            data['full_name'] = f"{first_name} {last_name}"

        if self._str_no_value(data.get('display_name')):
            if self._str_no_value(data.get('full_name')):
                data['display_name'] = data.get('email')
            else:
                data['display_name'] = data.get('full_name')

        return data

    @validates_schema
    def validate_user(self, data: Dict[str, Any], **kwargs: Any) -> None:
        if self._str_no_value(data.get('display_name')):
            raise ValidationError('"display_name", "full_name", or "email" must be provided')

        if self._str_no_value(data.get('user_id')):
            raise ValidationError('"user_id" or "email" must be provided')
