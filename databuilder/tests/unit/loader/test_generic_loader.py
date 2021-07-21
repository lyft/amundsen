# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import unittest

from mock import MagicMock
from pyhocon import ConfigFactory

from databuilder.loader.generic_loader import CALLBACK_FUNCTION, GenericLoader


class TestGenericLoader(unittest.TestCase):

    def test_loading(self) -> None:

        loader = GenericLoader()
        callback_func = MagicMock()
        loader.init(conf=ConfigFactory.from_dict({
            CALLBACK_FUNCTION: callback_func
        }))

        loader.load({'foo': 'bar'})
        loader.close()

        callback_func.assert_called_once()

    def test_none_loading(self) -> None:

        loader = GenericLoader()
        callback_func = MagicMock()
        loader.init(conf=ConfigFactory.from_dict({
            CALLBACK_FUNCTION: callback_func
        }))

        loader.load(None)
        loader.close()

        callback_func.assert_not_called()
