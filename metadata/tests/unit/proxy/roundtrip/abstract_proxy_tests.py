# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import logging
import time
import unittest
from abc import ABC, abstractmethod
from typing import (Any, Callable, Dict, Generic, List, Type, TypeVar,
                    no_type_check)

from amundsen_common.entity.resource_type import ResourceType
from amundsen_common.models.popular_table import PopularTable
from amundsen_common.models.table import ProgrammaticDescription, Table
from amundsen_common.tests.fixtures import Fixtures

from metadata_service.entity.tag_detail import TagDetail
from metadata_service.proxy.shared import checkNotNone
from metadata_service.util import UserResourceRel

from .roundtrip_base_proxy import RoundtripBaseProxy

__all__ = ['abstract_proxy_test_class']

T = TypeVar('T', bound=RoundtripBaseProxy)

LOGGER = logging.getLogger(__name__)


class AbstractProxyTest(ABC, Generic[T], unittest.TestCase):
    """
    Proxy integration testing

    use abstract_proxy_test_class() to get the class, e.g.

    class YourProxyTest(abstract_proxy_test_class(), unittest.TestCase):
        def get_proxy(self) -> YourProxy:
            return self.your_proxy
    ...
    """

    @abstractmethod
    def setUp(self) -> None:
        """
        this is for implementing classes (if they need it)
        """
        pass

    @abstractmethod
    def tearDown(self) -> None:
        """
        this is for implementing classes (if they need it)
        """
        pass

    @abstractmethod
    def get_proxy(self) -> T:
        pass

    @abstractmethod
    def get_relationship(self, *, node_type1: str, node_key1: str, node_type2: str,
                         node_key2: str) -> List[Any]:
        pass

    def test_rt_table(self) -> None:
        """
        it'd be nice to check that the result could be deserialized as a client of the metadata_service would
        """
        expected = Fixtures.next_table()
        expected.description = '"hello!" said no one'
        expected.tags.sort()

        self.get_proxy().put_table(table=expected)
        actual: Table = self.get_proxy().get_table(table_uri=checkNotNone(expected.key))
        actual.last_updated_timestamp = None
        actual.tags.sort()

        self.assertEqual(expected, actual)

    def test_rt_table_with_owner(self) -> None:
        user = Fixtures.next_user(is_active=True)
        self.get_proxy().put_user(data=user)
        application = Fixtures.next_application(application_id=user.user_id)
        expected = Fixtures.next_table(application=application)
        self.get_proxy().put_table(table=expected)

        actual: Table = self.get_proxy().get_table(table_uri=checkNotNone(expected.key))

        self.assertEqual(user.user_id, actual.owners[0].user_id)

    def test_rt_table_with_non_existent_app(self) -> None:
        application = Fixtures.next_application()
        # purposefully don't insert application
        expected_table = Fixtures.next_table(application=application)

        self.get_proxy().put_table(table=expected_table)
        actual_table: Table = self.get_proxy().get_table(table_uri=checkNotNone(expected_table.key))

        self.assertEqual(actual_table.table_writer, None)
        self.assertEqual(actual_table.owners, [])

    def test_get_popular_tables(self) -> None:
        application = Fixtures.next_application()
        self.get_proxy().put_app(data=application)
        # Add 10 tables
        tables: List[Table] = [Fixtures.next_table(application=application) for _ in range(10)]
        self.get_proxy().post_tables(tables=tables)

        user = Fixtures.next_user()
        self.get_proxy().put_user(data=user)

        # add reads to 6 of them, expecting that only the top five will be "popular"
        expected_popular_tables = []
        reads = 0
        for i in range(6):
            table_name: str = checkNotNone(tables[i].name)
            table_uri: str = checkNotNone(tables[i].key)
            self.get_proxy().add_read_count(table_uri=table_uri, user_id=f'{user.user_id}', read_count=reads)
            if reads > 0:
                expected_popular_tables.append(table_name)
            reads += 1000

        # ensure popular tables returns those 5 we added
        actual_popular_tables = self.get_proxy().get_popular_tables(num_entries=5)
        self.assertEqual(len(actual_popular_tables), 5)

        popular_tables = []
        for table in tables:
            if table.name in expected_popular_tables:
                popular_tables.append(
                    PopularTable(database=table.database,
                                 cluster=table.cluster,
                                 schema=table.schema,
                                 name=table.name,
                                 description=table.description))
        self.assertEqual(sorted(actual_popular_tables), sorted(popular_tables))

    def test_put_programmatic_table_description(self) -> None:
        table: Table = Fixtures.next_table()
        table.programmatic_descriptions = []
        self.get_proxy().put_table(table=table)
        expected_description: ProgrammaticDescription = Fixtures.next_description()
        self.get_proxy().put_programmatic_table_description(table_uri=checkNotNone(table.key),
                                                            description=expected_description)
        actual_table = self.get_proxy().get_table(table_uri=checkNotNone(table.key))
        self.assertEqual([expected_description], actual_table.programmatic_descriptions)

        # confirm that this runs without failing
        self.get_proxy().put_programmatic_table_description(table_uri=checkNotNone(Fixtures.next_table().key),
                                                            description=Fixtures.next_description())

    def test_add_delete_user_relation(self) -> None:
        table = Fixtures.next_table()
        self.get_proxy().put_table(table=table)
        user = Fixtures.next_user()
        self.get_proxy().put_user(data=user)

        self.get_proxy().add_resource_relation_by_user(id=f'{table.key}', user_id=f'{user.user_id}',
                                                       relation_type=UserResourceRel.read,
                                                       resource_type=ResourceType.Table)

        res: Dict[str, List[Table]] = self.get_proxy().get_table_by_user_relation(user_email=f'{user.user_id}',
                                                                                  relation_type=UserResourceRel.read)
        self.assertEqual(1, len(res['table']))
        relations = self.get_relationship(node_type1='User',
                                          node_key1=f'{user.user_id}',
                                          node_type2='Table',
                                          node_key2=checkNotNone(table.key))
        self.assertEqual(1, len(relations))

        # Now delete the relation
        self.get_proxy().delete_resource_relation_by_user(id=f'{table.key}', user_id=f'{user.user_id}',
                                                          relation_type=UserResourceRel.read,
                                                          resource_type=ResourceType.Table)
        res2: Dict[str, List[Table]] = self.get_proxy().get_table_by_user_relation(user_email=f'{user.user_id}',
                                                                                   relation_type=UserResourceRel.read)
        self.assertEqual(0, len(res2['table']))

    def test_owner_rt(self) -> None:
        application = Fixtures.next_application()
        self.get_proxy().put_app(data=application)
        table = Fixtures.next_table(application=application)
        self.get_proxy().put_table(table=table)
        user = Fixtures.next_user()
        self.get_proxy().put_user(data=user)
        user_id: str = user.user_id or 'test'
        self.get_proxy().add_owner(table_uri=checkNotNone(table.key), owner=user_id)
        table = self.get_proxy().get_table(table_uri=checkNotNone(table.key))
        self.assertEqual([user_id], [u.user_id for u in table.owners])
        self.get_proxy().delete_owner(table_uri=checkNotNone(table.key), owner=user_id)
        no_owner_table: Table = self.get_proxy().get_table(table_uri=checkNotNone(table.key))
        self.assertEqual([], no_owner_table.owners)
        relations = self.get_relationship(node_type1='User',
                                          node_key1=user_id,
                                          node_type2='Table',
                                          node_key2=checkNotNone(table.key))
        self.assertEqual(0, len(relations))

    def test_tag_rt(self) -> None:
        table = Fixtures.next_table()
        self.get_proxy().put_table(table=table)
        test_tag_detail = TagDetail(tag_name='a', tag_count=1)
        self.get_proxy().add_tag(id=checkNotNone(table.key), tag=test_tag_detail.tag_name,
                                 tag_type='default', resource_type=ResourceType.Table)
        tags_added = self.get_proxy().get_tags()
        self.assertIn(test_tag_detail, tags_added)
        self.get_proxy().delete_tag(id=checkNotNone(table.key), tag=test_tag_detail.tag_name,
                                    tag_type='default', resource_type=ResourceType.Table)
        tags_removed = self.get_proxy().get_tags()
        self.assertNotIn(test_tag_detail, tags_removed)
        relations = self.get_relationship(node_type1='Table',
                                          node_key1=checkNotNone(table.key),
                                          node_type2='Tag',
                                          node_key2=test_tag_detail.tag_name)
        self.assertEqual(0, len(relations))

    def test_get_latest_updated_ts(self) -> None:
        application = Fixtures.next_application()
        self.get_proxy().put_app(data=application)
        table = Fixtures.next_table(application=application)
        table_uri: str = checkNotNone(table.key)
        self.get_proxy().put_table(table=table)
        res = self.get_proxy().get_latest_updated_ts()
        self.assertEqual(type(res), int)
        actual: Table = self.get_proxy().get_table(table_uri=table_uri)
        self.assertEqual(actual.last_updated_timestamp, res)

        # try posting the same table again and make sure the timestamp updates
        time.sleep(1)
        self.get_proxy().put_table(table=table)
        res2 = self.get_proxy().get_latest_updated_ts()
        self.assertNotEqual(res, res2)
        actual = self.get_proxy().get_table(table_uri=table_uri)
        self.assertEqual(actual.last_updated_timestamp, res2)


@no_type_check
def class_getter_closure() -> Callable[[], Type[AbstractProxyTest]]:  # noqa: F821
    the_class: Type[AbstractProxyTest[Any]] = AbstractProxyTest  # noqa: F821

    def abstract_proxy_test_class() -> Type[AbstractProxyTest]:  # noqa: F821
        return the_class
    return abstract_proxy_test_class


abstract_proxy_test_class: Callable[[], Type[AbstractProxyTest]] = class_getter_closure()
del AbstractProxyTest
del class_getter_closure
