# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import unittest

import flask
from mock import patch
from mock import MagicMock

from amundsen_common.log import http_header_caller_retrieval
from amundsen_common.log.http_header_caller_retrieval import HttpHeaderCallerRetrieval

app = flask.Flask(__name__)


class ActionLogTest(unittest.TestCase):
    def test(self) -> None:
        with app.test_request_context(), \
                patch.object(http_header_caller_retrieval, 'request', new=MagicMock()) as mock_request:
            mock_request.headers.get.return_value = 'foo'
            actual = HttpHeaderCallerRetrieval().get_caller()
            self.assertEqual(actual, 'foo')


if __name__ == '__main__':
    unittest.main()
