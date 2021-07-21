# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import unittest

from mock import MagicMock
from pyhocon import ConfigTree

from databuilder.publisher.base_publisher import NoopPublisher, Publisher


class TestPublisher(unittest.TestCase):

    def testCallback(self) -> None:
        publisher = NoopPublisher()
        callback = MagicMock()
        publisher.register_call_back(callback)
        publisher.publish()

        self.assertTrue(callback.on_success.called)

    def testFailureCallback(self) -> None:
        publisher = FailedPublisher()
        callback = MagicMock()
        publisher.register_call_back(callback)

        try:
            publisher.publish()
        except Exception:
            pass

        self.assertTrue(callback.on_failure.called)


class FailedPublisher(Publisher):
    def __init__(self) -> None:
        super(FailedPublisher, self).__init__()

    def init(self, conf: ConfigTree) -> None:
        pass

    def publish_impl(self) -> None:
        raise Exception('Bomb')


if __name__ == '__main__':
    unittest.main()
