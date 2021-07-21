# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import textwrap
import unittest
import uuid

from databuilder.publisher.neo4j_preprocessor import DeleteRelationPreprocessor, NoopRelationPreprocessor


class TestNeo4jPreprocessor(unittest.TestCase):

    def testNoopRelationPreprocessor(self) -> None:
        preprocessor = NoopRelationPreprocessor()

        self.assertTrue(not preprocessor.is_perform_preprocess())

    def testDeleteRelationPreprocessor(self) -> None:  # noqa: W293
        preprocessor = DeleteRelationPreprocessor()

        self.assertTrue(preprocessor.is_perform_preprocess())

        preprocessor.filter(start_label='foo_label',
                            end_label='bar_label',
                            start_key='foo_key',
                            end_key='bar_key',
                            relation='foo_relation',
                            reverse_relation='bar_relation')

        self.assertTrue(preprocessor.filter(start_label=str(uuid.uuid4()),
                                            end_label=str(uuid.uuid4()),
                                            start_key=str(uuid.uuid4()),
                                            end_key=str(uuid.uuid4()),
                                            relation=str(uuid.uuid4()),
                                            reverse_relation=str(uuid.uuid4())))

        actual = preprocessor.preprocess_cypher(start_label='foo_label',
                                                end_label='bar_label',
                                                start_key='foo_key',
                                                end_key='bar_key',
                                                relation='foo_relation',
                                                reverse_relation='bar_relation')

        expected = (textwrap.dedent("""
    MATCH (n1:foo_label {key: $start_key })-[r]-(n2:bar_label {key: $end_key })

    WITH r LIMIT 2
    DELETE r
    RETURN count(*) as count;
    """), {'start_key': 'foo_key', 'end_key': 'bar_key'})

        self.assertEqual(expected, actual)

    def testDeleteRelationPreprocessorFilter(self) -> None:
        preprocessor = DeleteRelationPreprocessor(label_tuples=[('foo', 'bar')])

        self.assertTrue(preprocessor.filter(start_label='foo',
                                            end_label='bar',
                                            start_key=str(uuid.uuid4()),
                                            end_key=str(uuid.uuid4()),
                                            relation=str(uuid.uuid4()),
                                            reverse_relation=str(uuid.uuid4())))

        self.assertTrue(preprocessor.filter(start_label='bar',
                                            end_label='foo',
                                            start_key=str(uuid.uuid4()),
                                            end_key=str(uuid.uuid4()),
                                            relation=str(uuid.uuid4()),
                                            reverse_relation=str(uuid.uuid4())))

        self.assertFalse(preprocessor.filter(start_label='foz',
                                             end_label='baz',
                                             start_key=str(uuid.uuid4()),
                                             end_key=str(uuid.uuid4()),
                                             relation=str(uuid.uuid4()),
                                             reverse_relation=str(uuid.uuid4())))


if __name__ == '__main__':
    unittest.main()
