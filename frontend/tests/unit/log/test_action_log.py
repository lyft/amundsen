# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import getpass
import socket
import unittest
from contextlib import contextmanager
from typing import Generator, Any

import flask

from amundsen_application.log import action_log, action_log_callback
from amundsen_application.log.action_log import action_logging
from amundsen_application.log.action_log import get_epoch_millisec

# from mock import patch
# from flask import current_app

app = flask.Flask(__name__)
app.config.from_object('amundsen_application.config.LocalConfig')


class ActionLogTest(unittest.TestCase):

    def test_metrics_build(self) -> None:
        # with patch.object(current_app, 'config'):
        with app.test_request_context():
            func_name = 'search'
            metrics = action_log._build_metrics(func_name, 'dummy', 777, foo='bar')

            expected = {'command': 'search',
                        'host_name': socket.gethostname(),
                        'pos_args_json': '["dummy", 777]',
                        'keyword_args_json': '{"foo": "bar"}',
                        'user': getpass.getuser()}

            for k, v in expected.items():
                self.assertEqual(v, metrics.get(k))

            self.assertTrue(metrics.get('start_epoch_ms') <= get_epoch_millisec())  # type: ignore

    def test_fail_function(self) -> None:
        """
        Actual function is failing and fail needs to be propagated.
        :return:
        """
        with app.test_request_context(), self.assertRaises(NotImplementedError):
            fail_func()

    def test_success_function(self) -> None:
        """
        Test success function but with failing callback.
        In this case, failure should not propagate.
        :return:
        """
        with app.test_request_context(), fail_action_logger_callback():
            success_func()


@contextmanager
def fail_action_logger_callback() -> Generator:
    """
    Adding failing callback and revert it back when closed.
    :return:
    """
    tmp = action_log_callback.__pre_exec_callbacks[:]

    def fail_callback(_action_callback: Any) -> None:
        raise NotImplementedError

    action_log_callback.register_pre_exec_callback(fail_callback)
    yield
    action_log_callback.__pre_exec_callbacks = tmp


@action_logging
def fail_func() -> None:
    raise NotImplementedError


@action_logging
def success_func() -> None:
    pass


if __name__ == '__main__':
    unittest.main()
