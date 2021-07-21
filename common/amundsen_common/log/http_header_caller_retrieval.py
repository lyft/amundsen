# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from flask import current_app as flask_app
from flask import request

from amundsen_common.log.caller_retrieval import BaseCallerRetriever

CALLER_HEADER_KEY = 'CALLER_HEADER_KEY'


class HttpHeaderCallerRetrieval(BaseCallerRetriever):
    def get_caller(self) -> str:
        header_key = flask_app.config.get(CALLER_HEADER_KEY, 'user-agent')
        return request.headers.get(header_key) or 'UNKNOWN'
