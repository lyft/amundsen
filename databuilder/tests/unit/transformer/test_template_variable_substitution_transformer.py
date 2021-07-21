# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import unittest

from pyhocon import ConfigFactory

from databuilder.transformer.template_variable_substitution_transformer import (
    FIELD_NAME, TEMPLATE, TemplateVariableSubstitutionTransformer,
)


class TestTemplateVariableSubstitutionTransformer(unittest.TestCase):

    def test_conversion(self) -> None:

        transformer = TemplateVariableSubstitutionTransformer()
        config = ConfigFactory.from_dict({
            FIELD_NAME: 'baz',
            TEMPLATE: 'Hello {foo}'
        })
        transformer.init(conf=config)

        actual = transformer.transform({'foo': 'bar'})
        expected = {
            'foo': 'bar',
            'baz': 'Hello bar'
        }
        self.assertDictEqual(expected, actual)


if __name__ == '__main__':
    unittest.main()
