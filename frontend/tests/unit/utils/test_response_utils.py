# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import json
import unittest
from typing import Dict

from amundsen_application import create_app
from amundsen_application.api.utils.response_utils import create_error_response

local_app = create_app('amundsen_application.config.TestConfig', 'tests/templates')


class ResponseUtilsTest(unittest.TestCase):
    def setUp(self) -> None:
        pass

    def test_create_error_response(self) -> None:
        """
        Verify that the returned response contains the given messag and status_code
        :return:
        """
        test_message = 'Success'
        test_payload: Dict = {}
        status_code = 200
        with local_app.app_context():
            response = create_error_response(message=test_message,
                                             payload=test_payload,
                                             status_code=status_code)
        data = json.loads(response.data)
        self.assertEqual(response.status_code, status_code)
        self.assertEqual(data.get('msg'), test_message)
