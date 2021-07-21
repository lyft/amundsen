# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import unittest
from typing import List

from mock import MagicMock

from databuilder.callback.call_back import Callback, notify_callbacks


class TestCallBack(unittest.TestCase):

    def test_success_notify(self) -> None:
        callback1 = MagicMock()
        callback2 = MagicMock()
        callbacks: List[Callback] = [callback1, callback2]

        notify_callbacks(callbacks, is_success=True)

        self.assertTrue(callback1.on_success.called)
        self.assertTrue(not callback1.on_failure.called)
        self.assertTrue(callback2.on_success.called)
        self.assertTrue(not callback2.on_failure.called)

    def test_failure_notify(self) -> None:
        callback1 = MagicMock()
        callback2 = MagicMock()
        callbacks: List[Callback] = [callback1, callback2]

        notify_callbacks(callbacks, is_success=False)

        self.assertTrue(not callback1.on_success.called)
        self.assertTrue(callback1.on_failure.called)
        self.assertTrue(not callback2.on_success.called)
        self.assertTrue(callback2.on_failure.called)

    def test_notify_failure(self) -> None:
        callback1 = MagicMock()
        callback2 = MagicMock()
        callback2.on_success.side_effect = Exception('Boom')
        callback3 = MagicMock()
        callbacks: List[Callback] = [callback1, callback2, callback3]

        try:
            notify_callbacks(callbacks, is_success=True)
            self.assertTrue(False)
        except Exception:
            self.assertTrue(True)

        self.assertTrue(callback1.on_success.called)
        self.assertTrue(callback2.on_success.called)
        self.assertTrue(callback3.on_success.called)


if __name__ == '__main__':
    unittest.main()
