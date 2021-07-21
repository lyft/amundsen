# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import unittest

from amundsen_common.tests.fixtures import (next_application, next_col_type,
                                            next_columns, next_database,
                                            next_description,
                                            next_description_source,
                                            next_descriptions, next_int, next_item,
                                            next_range, next_string, next_table,
                                            next_tag, next_tags, next_user)
from amundsen_common.models.table import Column, ProgrammaticDescription, Stat


class TestFixtures(unittest.TestCase):
    # tests are numbered to ensure they execute in order
    def test_00_next_int(self) -> None:
        self.assertEqual(1000, next_int())

    def test_01_next_string(self) -> None:
        self.assertEqual('nopqrstuvw001011', next_string())

    def test_02_next_string(self) -> None:
        self.assertEqual('foo_yzabcdefgh001022', next_string(prefix='foo_'))

    def test_03_next_string(self) -> None:
        self.assertEqual('jklm001027', next_string(length=4))

    def test_04_next_string(self) -> None:
        self.assertEqual('bar_opqr001032', next_string(prefix='bar_', length=4))

    def test_05_next_range(self) -> None:
        self.assertEqual(3, len(next_range()))

    def test_06_next_item(self) -> None:
        self.assertEqual('c', next_item(items=['a', 'b', 'c']))

    def test_07_next_database(self) -> None:
        self.assertEqual('database2', next_database())

    def test_08_next_application(self) -> None:
        app = next_application()
        self.assertEqual('Apwxyzabcd001044', app.name)
        self.assertEqual('apwxyzabcd001044', app.id)
        self.assertEqual('https://apwxyzabcd001044.example.com', app.application_url)

    def test_09_next_application(self) -> None:
        app = next_application(application_id='foo')
        self.assertEqual('Foo', app.name)
        self.assertEqual('foo', app.id)
        self.assertEqual('https://foo.example.com', app.application_url)

    def test_10_next_tag(self) -> None:
        tag = next_tag()
        self.assertEqual('tafghijklm001053', tag.tag_name)
        self.assertEqual('default', tag.tag_type)

    def test_11_next_tags(self) -> None:
        tags = next_tags()
        self.assertEqual(4, len(tags))
        self.assertEqual(['tahijklmno001081',
                          'tapqrstuvw001063',
                          'taqrstuvwx001090',
                          'tayzabcdef001072'], [tag.tag_name for tag in tags])

    def test_12_next_description_source(self) -> None:
        self.assertEqual('dezabcdefg001099', next_description_source())

    def test_13_next_description(self) -> None:
        self.assertEqual(ProgrammaticDescription(text='ijklmnopqrstuvwxyzab001120', source='dedefghijk001129'),
                         next_description())

    def test_14_next_col_type(self) -> None:
        self.assertEqual('varchar', next_col_type())

    def test_15_just_execute_next_columns(self) -> None:
        columns = next_columns(table_key='not_important')
        self.assertEqual(1, len(columns))
        self.assertEqual([Column(name='coopqrstuv001140', key='not_important/coopqrstuv001140',
                                 description='coopqrstuv001140 description', col_type='int',
                                 sort_order=0, stats=[Stat(stat_type='num_rows', stat_val='114200',
                                                           start_epoch=None, end_epoch=None)])
                          ], columns)

    def test_16_just_execute_next_descriptions(self) -> None:
        descs = next_descriptions()
        self.assertEqual(3, len(descs))
        self.assertEqual([
            ProgrammaticDescription(source='dedefghijk001233', text='ijklmnopqrstuvwxyzab001224'),
            ProgrammaticDescription(source='devwxyzabc001173', text='abcdefghijklmnopqrst001164'),
            ProgrammaticDescription(source='dezabcdefg001203', text='efghijklmnopqrstuvwx001194')], descs)

    def test_17_just_execute_next_table(self) -> None:
        table = next_table()
        self.assertEqual(2, len(table.columns))
        self.assertEqual('tbnopqrstu001243', table.name)
        self.assertEqual('database1://clwxyzabcd001252.scfghijklm001261/tbnopqrstu001243', table.key)

    def test_18_next_user(self) -> None:
        user = next_user()
        self.assertEqual('Jklmno', user.last_name)
        self.assertEqual('Bob', user.first_name)
        self.assertEqual('usqrstuvwx001350', user.user_id)
        self.assertEqual('usqrstuvwx001350@example.com', user.email)
        self.assertEqual(True, user.is_active)
