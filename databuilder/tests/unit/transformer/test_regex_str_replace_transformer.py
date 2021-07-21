# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import unittest
from typing import Any

from pyhocon import ConfigFactory

from databuilder.transformer.regex_str_replace_transformer import (
    ATTRIBUTE_NAME, REGEX_REPLACE_TUPLE_LIST, RegexStrReplaceTransformer,
)


class TestRegexReplacement(unittest.TestCase):

    def test(self) -> None:
        transformer = self._default_test_transformer()

        foo = Foo('abc')
        actual = transformer.transform(foo)

        self.assertEqual('bba', actual.val)

    def test_numeric_val(self) -> None:
        transformer = self._default_test_transformer()

        foo = Foo(6)
        actual = transformer.transform(foo)

        self.assertEqual(6, actual.val)

    def test_none_val(self) -> None:
        transformer = self._default_test_transformer()

        foo = Foo(None)
        actual = transformer.transform(foo)

        self.assertEqual(None, actual.val)

    def _default_test_transformer(self) -> RegexStrReplaceTransformer:
        config = ConfigFactory.from_dict({
            REGEX_REPLACE_TUPLE_LIST: [('a', 'b'), ('c', 'a')],
            ATTRIBUTE_NAME: 'val'
        })

        transformer = RegexStrReplaceTransformer()
        transformer.init(config)

        return transformer

    def test_dict_replace(self) -> None:
        config = ConfigFactory.from_dict({
            REGEX_REPLACE_TUPLE_LIST: [('\\', '\\\\')],
            ATTRIBUTE_NAME: 'val'
        })

        transformer = RegexStrReplaceTransformer()
        transformer.init(config)

        d = {'val': '\\'}

        actual = transformer.transform(d)

        self.assertEqual({'val': '\\\\'}, actual)


class Foo(object):
    def __init__(self, val: Any) -> None:
        self.val = val


if __name__ == '__main__':
    unittest.main()
