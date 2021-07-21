# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0
import json

from typing import Dict, Optional
from flask import Flask, session
from amundsen_application.config import LocalConfig
from amundsen_application.models.user import load_user, User


def get_access_headers(app: Flask) -> Optional[Dict]:
    """
    Function to retrieve and format the Authorization Headers
    that can be passed to various microservices who are expecting that.
    :param oidc: OIDC object having authorization information
    :return: A formatted dictionary containing access token
    as Authorization header.
    """
    try:
        # noinspection PyUnresolvedReferences
        access_token = json.dumps(app.auth_client.token)
        return {'Authorization': 'Bearer {}'.format(access_token)}
    except Exception:
        return {}


def get_auth_user(app: Flask) -> User:
    """
    Retrieves the user information from oidc token, and then makes
    a dictionary 'UserInfo' from the token information dictionary.
    We need to convert it to a class in order to use the information
    in the rest of the Amundsen application.
    :param app: The instance of the current app.
    :return: A class UserInfo (Note, there isn't a UserInfo class, so we use Any)
    """
    user_info = load_user(session.get("user"))
    return user_info


class OidcConfig(LocalConfig):
    AUTH_USER_METHOD = get_auth_user
    REQUEST_HEADERS_METHOD = get_access_headers
