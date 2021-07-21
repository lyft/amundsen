# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0
import unittest

from amundsen_common.utils.atlas import AtlasColumnKey, AtlasTableKey


class TestAtlasTableKey(unittest.TestCase):
    def test_table_key(self) -> None:
        params = [
            ('hive_table://gold.database_name/table_name',
             None,
             'hive_table://gold.database_name/table_name',
             'database_name.table_name@gold',
             dict(database='hive_table', cluster='gold', schema='database_name', table='table_name'),
             False,
             True),
            ('database_name.table_name@gold',
             'hive_table',
             'hive_table://gold.database_name/table_name',
             'database_name.table_name@gold',
             dict(cluster='gold', schema='database_name', table='table_name'),
             True,
             False)
        ]

        for key, database, amundsen_key, qualified_name, details, is_key_qualified_name, is_key_amundsen_key in params:
            with self.subTest():
                result = AtlasTableKey(key, database=database)

                self.assertEqual(result.amundsen_key, amundsen_key)
                self.assertEqual(result.qualified_name, qualified_name)
                self.assertEqual(result.is_qualified_name, is_key_qualified_name)
                self.assertEqual(result.is_amundsen_key, is_key_amundsen_key)
                self.assertDictEqual(result.get_details(), details)

    def test_table_key_amundsen_key_validation(self) -> None:
        params = [
            ('hive://cluster_name.db_name/table_name', True),
            ('hive_table://cluster_name.with.dot.db_name/table_name', True),
            ('db_name.table_name@cluster_name', False)
        ]

        for key, is_amundsen_key in params:
            with self.subTest(f'Amundsen key validation for key: {key}'):
                result = AtlasTableKey(key)

                self.assertEqual(is_amundsen_key, result.is_amundsen_key)

    def test_table_key_qualified_name_validation(self) -> None:
        params = [
            ('hive://cluster_name.db_name/table_name', False),
            ('hive_table://cluster_name.db_name/table_name', False),
            ('db_name.table_name@cluster_name', True),
            ('db.table@cluster.dot', True)
        ]

        for key, is_amundsen_key in params:
            with self.subTest(f'Amundsen qualified name validation for key: {key}'):
                result = AtlasTableKey(key)

                self.assertEqual(is_amundsen_key, result.is_qualified_name)

    def test_table_key_qualified_name_from_amundsen_key(self) -> None:
        params = [
            ('hive_table://cluster_name.db_name/table_name', 'db_name.table_name@cluster_name'),
            ('hive://cluster_name.db_name/table_name', 'hive://cluster_name.db_name/table_name')
        ]

        for key, qn in params:
            with self.subTest(f'Test rendering qualified name from amundsen key: {key}'):
                result = AtlasTableKey(key)

                self.assertEqual(qn, result.qualified_name)

    def test_table_key_amundsen_key_from_qualified_name(self) -> None:
        params = [
            ('db_name.table_name@cluster_name', 'hive', 'hive://cluster_name.db_name/table_name'),
            ('db_name.table_name@cluster_name.dot', 'hive_table', 'hive_table://cluster_name.dot.db_name/table_name')
        ]

        for qn, database, key in params:
            with self.subTest(f'Test rendering amundsen key from qualified name: {qn}'):
                result = AtlasTableKey(qn, database=database)

                self.assertEqual(key, result.amundsen_key)

    def test_table_key_details_from_amundsen_key(self) -> None:
        params = [
            ('hive://cluster_name.db_name/table_name',
             dict(database='hive', cluster='cluster_name', schema='db_name', table='table_name')),
            ('hive_table://cluster_name.dot.db_name/table_name',
             dict(database='hive_table', cluster='cluster_name.dot', schema='db_name', table='table_name'))
        ]

        for key, details in params:
            with self.subTest(f'Test extract details from amundsen key: {key}'):
                result = AtlasTableKey(key)

                self.assertEqual(details, result.get_details())

    def test_table_key_details_from_qualified_name(self) -> None:
        params = [
            ('db_name.table_name@cluster_name',
             dict(cluster='cluster_name', schema='db_name', table='table_name')),
            ('db_name.table_name@cluster_name.dot',
             dict(cluster='cluster_name.dot', schema='db_name', table='table_name'))
        ]

        for qn, details in params:
            with self.subTest(f'Test extract details from qualified name: {qn}'):
                result = AtlasTableKey(qn)

                self.assertEqual(details, result.get_details())


class TestAtlasColumnKey(unittest.TestCase):
    def test_table_column_key(self) -> None:
        params = [
            ('hive_table://gold.database_name/table_name/column_name',
             None,
             'hive_table://gold.database_name/table_name/column_name',
             'database_name.table_name.column_name@gold',
             dict(database='hive_table', cluster='gold', schema='database_name', table='table_name',
                  column='column_name'),
             False,
             True),
            ('database_name.table_name.column_name@gold',
             'hive_table',
             'hive_table://gold.database_name/table_name/column_name',
             'database_name.table_name.column_name@gold',
             dict(cluster='gold', schema='database_name', table='table_name', column='column_name'),
             True,
             False)
        ]

        for key, database, amundsen_key, qualified_name, details, is_key_qualified_name, is_key_amundsen_key in params:
            with self.subTest():
                result = AtlasColumnKey(key, database=database)

                self.assertEqual(result.amundsen_key, amundsen_key)
                self.assertEqual(result.qualified_name, qualified_name)
                self.assertEqual(result.is_qualified_name, is_key_qualified_name)
                self.assertEqual(result.is_amundsen_key, is_key_amundsen_key)
                self.assertDictEqual(result.get_details(), details)

    def test_table_column_key_amundsen_key_validation(self) -> None:
        params = [
            ('hive://cluster_name.db_name/table_name/column_name', True),
            ('hive_table://cluster_name.with.dot.db_name/table_name/column_name', True),
            ('db_name.table_name.column_name@cluster_name', False),
            ('db.table.column@cluster.dot', False)
        ]

        for key, is_amundsen_key in params:
            with self.subTest(f'Amundsen key validation for key: {key}'):
                result = AtlasColumnKey(key)

                self.assertEqual(is_amundsen_key, result.is_amundsen_key)

    def test_table_column_key_qualified_name_validation(self) -> None:
        params = [
            ('hive://cluster_name.db_name/table_name/column_name', False),
            ('hive_table://cluster_name.with.dot.db_name/table_name/column_name', False),
            ('db_name.table_name.column_name@cluster_name', True),
            ('db.table.column@cluster.dot', True)
        ]

        for key, is_amundsen_key in params:
            with self.subTest(f'Amundsen qualified name validation for key: {key}'):
                result = AtlasColumnKey(key)

                self.assertEqual(is_amundsen_key, result.is_qualified_name)

    def test_table_column_key_qualified_name_from_amundsen_key(self) -> None:
        params = [
            ('hive://cluster_name.db_name/table_name/column_name',
             'db_name.table_name.column_name@cluster_name'),
            ('hive_table://cluster_name.dot.db_name/table_name/column_name',
             'db_name.table_name.column_name@cluster_name.dot')
        ]

        for key, qn in params:
            with self.subTest(f'Test rendering qualified name from amundsen key: {key}'):
                result = AtlasColumnKey(key)

                self.assertEqual(qn, result.qualified_name)

    def test_table_column_key_amundsen_key_from_qualified_name(self) -> None:
        params = [
            ('db_name.table_name.column_name@cluster_name', 'hive',
             'hive://cluster_name.db_name/table_name/column_name'),
            ('db_name.table_name.column_name.dot@cluster_name.dot', 'hive_table',
             'hive_table://cluster_name.dot.db_name/table_name/column_name.dot')
        ]

        for qn, database, key in params:
            with self.subTest(f'Test rendering amundsen key from qualified name: {qn}'):
                result = AtlasColumnKey(qn, database=database)

                self.assertEqual(key, result.amundsen_key)

    def test_table_column_key_details_from_amundsen_key(self) -> None:
        params = [
            ('hive://cluster_name.db_name/table_name/column_name',
             dict(database='hive', cluster='cluster_name', schema='db_name', table='table_name',
                  column='column_name')),
            ('hive_table://cluster_name.dot.db_name/table_name/column_name.dot',
             dict(database='hive_table', cluster='cluster_name.dot', schema='db_name', table='table_name',
                  column='column_name.dot'))
        ]

        for key, details in params:
            with self.subTest(f'Test extract details from amundsen key: {key}'):
                result = AtlasColumnKey(key)

                self.assertEqual(details, result.get_details())

    def test_table_column_key_details_from_qualified_name(self) -> None:
        params = [
            ('db_name.table_name.column_name@cluster_name',
             dict(cluster='cluster_name', schema='db_name', table='table_name', column='column_name')),
            ('db_name.table_name.column_name.dot@cluster_name.dot',
             dict(cluster='cluster_name.dot', schema='db_name', table='table_name', column='column_name.dot'))
        ]

        for qn, details in params:
            with self.subTest(f'Test extract details from qualified name: {qn}'):
                result = AtlasColumnKey(qn)

                self.assertEqual(details, result.get_details())


if __name__ == '__main__':
    unittest.main()
