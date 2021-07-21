# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import unittest

from pyhocon import ConfigFactory

from databuilder.models.table_metadata import TableMetadata
from databuilder.transformer.table_tag_transformer import TableTagTransformer


class TestTableTagTransformer(unittest.TestCase):
    def test_single_tag(self) -> None:
        transformer = TableTagTransformer()
        config = ConfigFactory.from_dict({
            TableTagTransformer.TAGS: 'foo',
        })
        transformer.init(conf=config)

        result = transformer.transform(TableMetadata(
            database='test_db',
            cluster='test_cluster',
            schema='test_schema',
            name='test_table',
            description='',
        ))

        self.assertEqual(result.tags, ['foo'])

    def test_multiple_tags_comma_delimited(self) -> None:
        transformer = TableTagTransformer()
        config = ConfigFactory.from_dict({
            TableTagTransformer.TAGS: 'foo,bar',
        })
        transformer.init(conf=config)

        result = transformer.transform(TableMetadata(
            database='test_db',
            cluster='test_cluster',
            schema='test_schema',
            name='test_table',
            description='',
        ))

        self.assertEqual(result.tags, ['foo', 'bar'])

    def test_add_tag_to_existing_tags(self) -> None:
        transformer = TableTagTransformer()
        config = ConfigFactory.from_dict({
            TableTagTransformer.TAGS: 'baz',
        })
        transformer.init(conf=config)

        result = transformer.transform(TableMetadata(
            database='test_db',
            cluster='test_cluster',
            schema='test_schema',
            name='test_table',
            description='',
            tags='foo,bar',
        ))
        self.assertEqual(result.tags, ['foo', 'bar', 'baz'])

    def test_tags_not_added_to_other_objects(self) -> None:
        transformer = TableTagTransformer()
        config = ConfigFactory.from_dict({
            TableTagTransformer.TAGS: 'new_tag',
        })
        transformer.init(conf=config)

        class NotATable():
            tags = 'existing_tag'

        result = transformer.transform(NotATable())

        self.assertEqual(result.tags, 'existing_tag')


if __name__ == '__main__':
    unittest.main()
