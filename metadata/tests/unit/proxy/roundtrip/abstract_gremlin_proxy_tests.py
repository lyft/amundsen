# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import unittest
from abc import abstractmethod
from typing import (Any, Callable, List, Mapping, Optional, Type, TypeVar,
                    Union, no_type_check, overload)
from unittest import mock

from amundsen_common.tests.fixtures import Fixtures
from amundsen_gremlin.gremlin_model import (EdgeType, EdgeTypes, GremlinType,
                                            Property, VertexType, VertexTypes)
from flask import Flask
from gremlin_python.driver.resultset import ResultSet
from gremlin_python.process.graph_traversal import __
from gremlin_python.process.traversal import Cardinality, Traversal, within

from metadata_service import create_app
from metadata_service.proxy.gremlin_proxy import (_V, AbstractGremlinProxy,
                                                  FromResultSet,
                                                  _append_traversal,
                                                  _edges_from, _expire_link,
                                                  _link, _safe_get,
                                                  _safe_get_list, _upsert)

from .abstract_proxy_tests import abstract_proxy_test_class

TYPE = TypeVar('TYPE')


class AbstractGremlinProxyTest(abstract_proxy_test_class(), unittest.TestCase):  # type: ignore
    """
    Gremlin proxy integration testing

    NOTE THAT THE CLEAN UP FOR THESE TESTS REMOVES ANY NODES CONNECTED TO WHAT YOU DO IN THIS TEST (SO YOU MAY
    ACCIDENTALLY REMOVE "REAL" DATA LOCALLY OR IN THE SHARED DEVELOPMENT NEPTUNE)
    """

    @classmethod
    @abstractmethod
    def _create_gremlin_proxy(cls, config: Mapping[str, Any]) -> AbstractGremlinProxy:
        pass

    def setUp(self) -> None:
        self.app: Flask = create_app(config_module_class='metadata_service.config.LocalConfig')
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.app.config['PROXY_HOST']
        self.gremlin_proxy = self._create_gremlin_proxy(self.app.config)
        self.key_property_name = self.gremlin_proxy.key_property_name
        self.get_proxy().drop()
        self.maxDiff = None

    def tearDown(self) -> None:
        # pass
        self.get_proxy().drop()

    def get_proxy(self) -> AbstractGremlinProxy:
        return self.gremlin_proxy

    def get_relationship(self, *, node_type1: str, node_key1: str, node_type2: str,
                         node_key2: str) -> List[Any]:
        return self.gremlin_proxy.get_relationship(
            node_type1=node_type1, node_key1=node_key1, node_type2=node_type2, node_key2=node_key2)

    def _upsert(self, **kwargs: Any) -> None:
        with self.get_proxy().query_executor() as executor:
            return _upsert(executor=executor, execute=FromResultSet.iterate, g=self.get_proxy().g,
                           key_property_name=self.get_proxy().key_property_name, **kwargs)

    def _link(self, **kwargs: Any) -> None:
        with self.get_proxy().query_executor() as executor:
            return _link(executor=executor, execute=FromResultSet.iterate, g=self.get_proxy().g,
                         key_property_name=self.get_proxy().key_property_name, **kwargs)

    @overload  # noqa: F811
    def _get(self, extra_traversal: Traversal, **kwargs: Any) -> Any:
        ...

    @overload  # noqa: F811
    def _get(self, extra_traversal: Traversal, get: Callable[[ResultSet], TYPE], **kwargs: Any) -> TYPE:  # noqa: F811
        ...

    def _get(self, extra_traversal: Traversal, get: Optional[Callable[[ResultSet], TYPE]] = None,  # noqa: F811
             **kwargs: Any) -> Union[TYPE, Any]:
        traversal = _append_traversal(_V(g=self.get_proxy().g, **kwargs), extra_traversal)
        return self.get_proxy().query_executor()(query=traversal, get=get or FromResultSet.getOnly)

    # everything below is a gremlin specific test

    def test_safe_get(self) -> None:
        self.assertEqual(_safe_get([]), None)
        self.assertEqual(_safe_get(['1']), '1')
        self.assertRaisesRegex(RuntimeError, r'is not a singleton!', _safe_get, ['1', '2'])
        self.assertEqual(_safe_get_list(['1', '2']), ['1', '2'])
        self.assertEqual(_safe_get(['1'], transform=int), 1)
        self.assertEqual(_safe_get_list(['1', '2'], transform=int), [1, 2])
        self.assertEqual(_safe_get([{'one': ['1']}], 'one'), '1')
        self.assertRaisesRegex(RuntimeError, r'is not a singleton!', _safe_get, [{'one': ['1', '2']}], 'one')
        self.assertRaisesRegex(RuntimeError, r'is not a singleton!', _safe_get, [{'one': ['1']}, 'two'], 'one')
        self.assertEqual(_safe_get_list([{'one': ['1', '2']}], 'one'), ['1', '2'])
        self.assertEqual(_safe_get_list([{'one': ['1', '2']}], 'one', transform=int), [1, 2])

    def test_safe_get_with_objects(self) -> None:
        app = Fixtures.next_application()
        app2 = Fixtures.next_application()
        fake_result = {key: [value] for key, value in app.__dict__.items()}
        fake_result2 = {key: [value] for key, value in app2.__dict__.items()}
        transform = self.get_proxy()._convert_to_application
        self.assertEqual(_safe_get([{'a': [fake_result]}], 'a', transform=transform), app)
        self.assertCountEqual(
            _safe_get_list([{'a': [fake_result, fake_result2]}], 'a', transform=transform),
            [app, app2])

    def test_upsert_rt(self) -> None:
        # test that we will insert
        db_name = Fixtures.next_database()
        database_uri = f'database://{db_name}'
        exists = self._get(label=VertexTypes.Database, key=database_uri, extra_traversal=__.count())
        self.assertEqual(exists, 0)
        self._upsert(label=VertexTypes.Database, key=database_uri, name='test')
        exists = self._get(label=VertexTypes.Database, key=database_uri, extra_traversal=__.count())
        self.assertEqual(exists, 1)

        # test that we will not insert (_get will explode if more than one vertex matches)
        self._upsert(label=VertexTypes.Database, key=database_uri, name='test')
        vertexValueMap = self._get(label=VertexTypes.Database, key=database_uri, extra_traversal=__.valueMap(),
                                   get=FromResultSet.toList)
        self.assertIsNotNone(vertexValueMap)

    def test_upsert_thrice(self) -> None:
        executor = mock.Mock(wraps=self.get_proxy().query_executor())

        # test that we will insert
        db_name = Fixtures.next_database()
        database_uri = f'database://{db_name}'
        vertex_type = VertexType(
            label=VertexTypes.Database.value.label,
            properties=VertexTypes.Database.value.properties + tuple([Property(name='foo', type=GremlinType.String)]))

        exists = self._get(label=vertex_type, key=database_uri, extra_traversal=__.count())
        self.assertEqual(exists, 0)
        _upsert(executor=executor, g=self.get_proxy().g, key_property_name=self.get_proxy().key_property_name,
                label=vertex_type, key=database_uri, name='test', foo='bar')
        exists = self._get(label=vertex_type, key=database_uri, extra_traversal=__.count())
        self.assertEqual(exists, 1)
        id = self._get(label=vertex_type, key=database_uri, extra_traversal=__.id())

        executor.reset_mock()
        _upsert(executor=executor, g=self.get_proxy().g, key_property_name=self.get_proxy().key_property_name,
                label=vertex_type, key=database_uri, name='test')
        exists = self._get(label=vertex_type, key=database_uri, extra_traversal=__.count())
        self.assertEqual(exists, 1)
        self.assertEqual(executor.call_count, 2)
        # first one is the get:
        self.assertEqual(executor.call_args_list[0][1]['query'].bytecode, __.V(id).valueMap(True).bytecode)
        # the second one should be like
        self.assertEqual(executor.call_args_list[1][1]['query'].bytecode, __.V(id).id().bytecode)

        executor.reset_mock()
        _upsert(executor=executor, g=self.get_proxy().g, key_property_name=self.get_proxy().key_property_name,
                label=vertex_type, key=database_uri, name='test2', foo=None)
        exists = self._get(label=vertex_type, key=database_uri, extra_traversal=__.count())
        self.assertEqual(exists, 1)
        self.assertEqual(executor.call_count, 2)
        # first one is the get:
        self.assertEqual(executor.call_args_list[0][1]['query'].bytecode, __.V(id).valueMap(True).bytecode)
        # the second one should be like
        self.assertEqual(
            executor.call_args_list[1][1]['query'].bytecode,
            __.V(id).sideEffect(__.properties('foo').drop()).property(Cardinality.single, 'name', 'test2').id().
            bytecode)

    def test_link_rt(self) -> None:
        db_name = Fixtures.next_database()
        database_uri = f'database://{db_name}'
        cluster_uri = f'{db_name}://acluster'
        self.assertEqual(self._get(label=VertexTypes.Database, key=database_uri, extra_traversal=__.count()), 0)
        self.assertEqual(self._get(label=VertexTypes.Cluster, key=cluster_uri, extra_traversal=__.count()), 0)
        self._upsert(label=VertexTypes.Database, key=database_uri, name='test')
        self._upsert(label=VertexTypes.Cluster, key=cluster_uri, name='acluster')
        self.assertEqual(self._get(label=VertexTypes.Database, key=database_uri, extra_traversal=__.count()), 1)
        self.assertEqual(self._get(label=VertexTypes.Cluster, key=cluster_uri, extra_traversal=__.count()), 1)

        # use non-standard EdgeType, so aproperty doesn't explode
        edge_type = EdgeType(label='CLUSTER', properties=tuple([
            Property(name='created', type=GremlinType.Date, required=True),
            Property(name='aproperty', type=GremlinType.String)]))

        # link
        self._link(vertex1_label=VertexTypes.Database, vertex1_key=database_uri,
                   vertex2_label=VertexTypes.Cluster, vertex2_key=cluster_uri,
                   edge_label=edge_type, aproperty='hi')
        rel = self.get_relationship(node_type1=VertexTypes.Database.value.label, node_key1=database_uri,
                                    node_type2=VertexTypes.Cluster.value.label, node_key2=cluster_uri)
        self.assertEqual(len(rel), 1)
        self.assertEqual(set(rel[0].keys()), set(['created', 'aproperty']))
        self.assertEqual(rel[0].get('aproperty'), 'hi')

        # repeat but with aproperty unset (e.g. like we want to use _link with expired)
        self._link(vertex1_label=VertexTypes.Database, vertex1_key=database_uri,
                   vertex2_label=VertexTypes.Cluster, vertex2_key=cluster_uri,
                   edge_label=edge_type, aproperty=None)
        rel = self.get_relationship(node_type1=VertexTypes.Database.value.label, node_key1=database_uri,
                                    node_type2=VertexTypes.Cluster.value.label, node_key2=cluster_uri)
        self.assertEqual(len(rel), 1)
        self.assertEqual(set(rel[0].keys()), set(['created']))
        self.assertEqual(rel[0].get('aproperty'), None)

    def test_link_dangling_from_rt(self) -> None:
        db_name = Fixtures.next_database()
        database_uri = f'database://{db_name}'
        cluster_uri = f'{db_name}://acluster'
        self.assertEqual(self._get(label=VertexTypes.Cluster, key=cluster_uri, extra_traversal=__.count()), 0)
        self._upsert(label=VertexTypes.Cluster, key=cluster_uri, name='acluster')
        self.assertEqual(self._get(label=VertexTypes.Database, key=database_uri, extra_traversal=__.count()), 0)
        self.assertEqual(self._get(label=VertexTypes.Cluster, key=cluster_uri, extra_traversal=__.count()), 1)

        with self.assertRaises(StopIteration):
            self._link(vertex1_label=VertexTypes.Database, vertex1_key=database_uri,
                       vertex2_label=VertexTypes.Cluster, vertex2_key=cluster_uri,
                       edge_label=EdgeTypes.Cluster, aproperty='hi')

    def test_link_dangling_to_rt(self) -> None:
        db_name = Fixtures.next_database()
        database_uri = f'database://{db_name}'
        cluster_uri = f'{db_name}://acluster'
        self.assertEqual(self._get(label=VertexTypes.Database, key=database_uri, extra_traversal=__.count()), 0)
        self._upsert(label=VertexTypes.Database, key=database_uri, name='test')
        self.assertEqual(self._get(label=VertexTypes.Database, key=database_uri, extra_traversal=__.count()), 1)
        self.assertEqual(self._get(label=VertexTypes.Cluster, key=cluster_uri, extra_traversal=__.count()), 0)

        with self.assertRaises(StopIteration):
            self._link(vertex1_label=VertexTypes.Database, vertex1_key=database_uri,
                       vertex2_label=VertexTypes.Cluster, vertex2_key=cluster_uri,
                       edge_label=EdgeTypes.Cluster, aproperty='hi')

    def test_edges(self) -> None:
        db_name = Fixtures.next_database()
        database_uri = f'database://{db_name}'
        cluster1_uri = f'{db_name}://acluster'
        cluster2_uri = f'{db_name}://bcluster'
        self.assertNotEqual(cluster1_uri, cluster2_uri)
        cluster_vertex_type = VertexType.construct_type(label=VertexTypes.Cluster.value.label, properties=tuple([
            Property(name='aproperty', type=GremlinType.String),
            Property(name='b', type=GremlinType.String),
            Property(name='c', type=GremlinType.String)]))
        self._upsert(label=VertexTypes.Database, key=database_uri, name='test')
        self._upsert(label=cluster_vertex_type, key=cluster1_uri, aproperty='one', b='b')
        self._upsert(label=cluster_vertex_type, key=cluster2_uri, aproperty='two', c='c')

        cluster_edge_type = EdgeType(label=EdgeTypes.Cluster.value.label, properties=tuple([
            Property(name='created', type=GremlinType.Date, required=True),
            Property(name='aproperty', type=GremlinType.String),
            Property(name='b', type=GremlinType.String),
            Property(name='c', type=GremlinType.String)]))
        self._link(vertex1_label=VertexTypes.Database, vertex1_key=database_uri,
                   vertex2_label=VertexTypes.Cluster, vertex2_key=cluster1_uri,
                   edge_label=cluster_edge_type, aproperty='won', b='bee')
        self._link(vertex1_label=VertexTypes.Database, vertex1_key=database_uri,
                   vertex2_label=VertexTypes.Cluster, vertex2_key=cluster2_uri,
                   edge_label=cluster_edge_type, aproperty='too', c='sea')

        # get the one
        e1 = _edges_from(g=self.get_proxy().g, vertex1_label=VertexTypes.Database, vertex1_key=database_uri,
                         vertex2_label=None, vertex2_key=None, edge_label=None, aproperty='won').id().toList()
        self.assertEqual(len(e1), 1)

        # get the other
        e2 = _edges_from(g=self.get_proxy().g, vertex1_label=VertexTypes.Database, vertex1_key=database_uri,
                         vertex2_label=None, vertex2_key=None, edge_label=None, aproperty='too').id().toList()
        self.assertEqual(len(e2), 1)
        self.assertNotEqual(e1[0], e2[0])

        # get both edges
        e = _edges_from(g=self.get_proxy().g, vertex1_label=VertexTypes.Database, vertex1_key=database_uri,
                        vertex2_label=None, vertex2_key=None, edge_label=EdgeTypes.Cluster).id().toList()
        self.assertTrue(e == e1 + e2 or e == e2 + e1)

        # get both edges
        e = _edges_from(g=self.get_proxy().g, vertex1_label=VertexTypes.Database, vertex1_key=database_uri,
                        vertex2_label=None, vertex2_key=None,
                        edge_label=None, aproperty=within('won', 'too')).id().toList()
        self.assertTrue(e == e1 + e2 or e == e2 + e1)

        # get the one
        e = _edges_from(g=self.get_proxy().g, vertex1_label=VertexTypes.Database, vertex1_key=database_uri,
                        vertex2_label=VertexTypes.Cluster, vertex2_key=cluster1_uri, edge_label=None).id().toList()
        self.assertEqual(e, e1)

        # get the other
        e = _edges_from(g=self.get_proxy().g, vertex1_label=VertexTypes.Database, vertex1_key=database_uri,
                        vertex2_label=VertexTypes.Cluster, vertex2_key=cluster2_uri, edge_label=None).id().toList()
        self.assertEqual(e, e2)

        # get the one
        e = _edges_from(g=self.get_proxy().g, vertex1_label=VertexTypes.Database, vertex1_key=database_uri,
                        vertex2_label=None, vertex2_key=None, vertex2_properties=dict(aproperty='one'),
                        edge_label=None).id().toList()
        self.assertEqual(e, e1)

        # get the other
        e = _edges_from(g=self.get_proxy().g, vertex1_label=VertexTypes.Database, vertex1_key=database_uri,
                        vertex2_label=None, vertex2_key=None, vertex2_properties=dict(aproperty='two'),
                        edge_label=None).id().toList()
        self.assertEqual(e, e2)

        # get the one
        e = _edges_from(g=self.get_proxy().g, vertex1_label=VertexTypes.Database, vertex1_key=database_uri,
                        vertex2_label=None, vertex2_key=None, vertex2_properties=dict(c=None),
                        edge_label=None).id().toList()
        self.assertEqual(e, e1)

        # get the other
        e = _edges_from(g=self.get_proxy().g, vertex1_label=VertexTypes.Database, vertex1_key=database_uri,
                        vertex2_label=None, vertex2_key=None, vertex2_properties=dict(b=None),
                        edge_label=None).id().toList()
        self.assertEqual(e, e2)

        # get none
        e = _edges_from(g=self.get_proxy().g, vertex1_label=VertexTypes.Database, vertex1_key=database_uri,
                        vertex2_label=None, vertex2_key=None, edge_label=EdgeTypes.Schema).id().toList()
        self.assertEqual(len(e), 0)

        # get none
        e = _edges_from(g=self.get_proxy().g, vertex1_label=VertexTypes.Database, vertex1_key=database_uri,
                        vertex2_label=VertexTypes.Schema, vertex2_key=None, edge_label=None).id().toList()
        self.assertEqual(len(e), 0)

    def test_expire_link(self) -> None:
        db_name = Fixtures.next_database()
        database_uri = f'database://{db_name}'
        database2_uri = f'database://{db_name}2'
        cluster_uri = f'{db_name}://acluster'
        cluster2_uri = f'{db_name}2://acluster'
        self._upsert(label=VertexTypes.Database, key=database_uri, name='test')
        self._upsert(label=VertexTypes.Database, key=database2_uri, name='test1')
        self._upsert(label=VertexTypes.Cluster, key=cluster_uri, name='test2')
        self._upsert(label=VertexTypes.Cluster, key=cluster2_uri, name='test3')

        # use non-standard EdgeType, so aproperty doesn't explode
        edge_type = EdgeType(label='CLUSTER', properties=tuple([
            Property(name='created', type=GremlinType.Date, required=True),
            Property(name='aproperty', type=GremlinType.String)]))
        self._link(vertex1_label=VertexTypes.Database, vertex1_key=database_uri,
                   vertex2_label=VertexTypes.Cluster, vertex2_key=cluster_uri,
                   edge_label=edge_type, aproperty='hi1')
        self._link(vertex1_label=VertexTypes.Database, vertex1_key=database_uri,
                   vertex2_label=VertexTypes.Cluster, vertex2_key=cluster2_uri,
                   edge_label=edge_type, aproperty='hi2')
        self._link(vertex1_label=VertexTypes.Database, vertex1_key=database2_uri,
                   vertex2_label=VertexTypes.Cluster, vertex2_key=cluster_uri,
                   edge_label=edge_type, aproperty='hi3')
        self._link(vertex1_label=VertexTypes.Database, vertex1_key=database2_uri,
                   vertex2_label=VertexTypes.Cluster, vertex2_key=cluster2_uri,
                   edge_label=edge_type, aproperty='hi4')

        with self.get_proxy().query_executor() as executor:
            _expire_link(executor=executor, g=self.get_proxy().g, key_property_name=self.key_property_name,
                         edge_label=edge_type, vertex1_label=VertexTypes.Database,
                         vertex1_key=database_uri, vertex2_label=VertexTypes.Cluster, vertex2_key=cluster_uri)

        # db -> cluster link was expired properly
        rel = self.get_relationship(node_type1=VertexTypes.Database.value.label, node_key1=database_uri,
                                    node_type2=VertexTypes.Cluster.value.label, node_key2=cluster_uri)
        self.assertEqual(_safe_get(rel), None)

        # db is still linked to its other cluster (not expired)
        rel = self.get_relationship(node_type1=VertexTypes.Database.value.label, node_key1=database_uri,
                                    node_type2=VertexTypes.Cluster.value.label, node_key2=cluster2_uri)
        self.assertIsNone(_safe_get(rel).get('expired'))

        # cluster is still linked to its other db (not expired)
        rel = self.get_relationship(node_type1=VertexTypes.Database.value.label, node_key1=database2_uri,
                                    node_type2=VertexTypes.Cluster.value.label, node_key2=cluster_uri)
        self.assertIsNone(_safe_get(rel).get('expired'))


@no_type_check
def class_getter_closure() -> Callable[[], Type[AbstractGremlinProxyTest]]:  # noqa: F821
    the_class: Type[AbstractGremlinProxyTest[Any]] = AbstractGremlinProxyTest  # noqa: F821

    def abstract_gremlin_proxy_test_class() -> Type[AbstractGremlinProxyTest]:  # noqa: F821
        return the_class
    return abstract_gremlin_proxy_test_class


# so we don't try to test it directly
abstract_gremlin_proxy_test_class: Callable[[], Type[AbstractGremlinProxyTest]] = class_getter_closure()
del AbstractGremlinProxyTest
del class_getter_closure
