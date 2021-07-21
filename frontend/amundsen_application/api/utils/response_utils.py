# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import logging

from typing import Dict  # noqa: F401

from flask import Response, jsonify, make_response


def create_error_response(*, message: str, payload: Dict, status_code: int) -> Response:
    """
    Logs and info level log with the given message, and returns a response with:
    1. The given message as 'msg' in the response data
    2. The given status code as thge response status code
    """
    logging.info(message)
    payload['msg'] = message
    return make_response(jsonify(payload), status_code)
