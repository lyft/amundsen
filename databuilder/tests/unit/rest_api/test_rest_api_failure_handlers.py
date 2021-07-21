# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import unittest

from mock import MagicMock

from databuilder.rest_api.rest_api_failure_handlers import HttpFailureSkipOnStatus


class TestHttpFailureSkipOnStatus(unittest.TestCase):

    def testSkip(self) -> None:
        failure_handler = HttpFailureSkipOnStatus([404, 400])

        exception = MagicMock()
        exception.response.status_code = 404
        self.assertTrue(failure_handler.can_skip_failure(exception=exception))

        exception.response.status_code = 400
        self.assertTrue(failure_handler.can_skip_failure(exception=exception))

        exception.response.status_code = 500
        self.assertFalse(failure_handler.can_skip_failure(exception=exception))
