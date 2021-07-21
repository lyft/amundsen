# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import getpass

from flask import current_app as flask_app

from amundsen_common.log.caller_retrieval import BaseCallerRetriever


class AuthCallerRetrieval(BaseCallerRetriever):
    def get_caller(self) -> str:
        if flask_app.config.get('AUTH_USER_METHOD', None):
            return flask_app.config['AUTH_USER_METHOD'](flask_app).email
        return getpass.getuser()
