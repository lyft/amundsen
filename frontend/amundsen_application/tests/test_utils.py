# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from flask import current_app as app
from amundsen_application.models.user import load_user, User

TEST_USER_ID = 'test_user_id'


def get_test_user(app: app) -> User:  # type: ignore
    user_info = {
        'email': 'test@email.com',
        'user_id': TEST_USER_ID,
        'first_name': 'Firstname',
        'last_name': 'Lastname',
        'full_name': 'Firstname Lastname',
    }
    return load_user(user_info)
