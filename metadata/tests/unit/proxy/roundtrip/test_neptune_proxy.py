# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import json
import unittest
from typing import Any, Mapping

import gremlin_python.driver.protocol
from amundsen_gremlin.gremlin_model import VertexTypes
from amundsen_gremlin.script_translator import ScriptTranslator
from gremlin_python.process.graph_traversal import __
from gremlin_python.process.traversal import Cardinality

from metadata_service.proxy.neptune_proxy import NeptuneGremlinProxy

from .abstract_gremlin_proxy_tests import abstract_gremlin_proxy_test_class
from .roundtrip_neptune_proxy import RoundtripNeptuneGremlinProxy


class NeptuneGremlinProxyTest(
        abstract_gremlin_proxy_test_class(), unittest.TestCase):  # type: ignore
    def _create_gremlin_proxy(self, config: Mapping[str, Any]) -> RoundtripNeptuneGremlinProxy:
        # Don't use PROXY_HOST, PROXY_PORT, PROXY_PASSWORD.  They might not be neptune
        client_kwargs = {
            'neptune_bulk_loader_s3_bucket_name': config['NEPTUNE_BULK_LOADER_S3_BUCKET_NAME'],
            'ignore_neptune_shard': False
        }
        return RoundtripNeptuneGremlinProxy(
            host=config['NEPTUNE_URL'],
            password=config['NEPTUNE_SESSION'],
            client_kwargs=client_kwargs
        )  # noqa E501

    def test_is_retryable(self) -> None:
        exception = gremlin_python.driver.protocol.GremlinServerError(dict(
            code=408, attributes=(), message=json.dumps(dict(code='ConcurrentModificationException'))))
        self.assertTrue(NeptuneGremlinProxy._is_retryable_exception(method_name=None, exception=exception))
        exception = gremlin_python.driver.protocol.GremlinServerError(dict(
            code=408, attributes=(), message=json.dumps(dict(code='InternalError'))))
        self.assertFalse(NeptuneGremlinProxy._is_retryable_exception(method_name=None, exception=exception))
        exception = RuntimeError()
        self.assertFalse(NeptuneGremlinProxy._is_retryable_exception(method_name=None, exception=exception))

    def test_gremlin_status(self) -> None:
        proxy = self.get_proxy()
        results = proxy._gremlin_status()
        self.assertIsNotNone(results)

    def test_sparql_status(self) -> None:
        proxy = self.get_proxy()
        results = proxy._sparql_status()
        self.assertIsNotNone(results)

    def test_explain(self) -> None:
        proxy = self.get_proxy()
        g = proxy.g.V().has(VertexTypes.User.value.label, proxy.key_property_name, 'jack').fold().coalesce(
            __.unfold(),
            __.addV(VertexTypes.User.value.label).property(Cardinality.single, proxy.key_property_name, 'jack'))
        g = g.property(Cardinality.single, 'email', 'jack@squareup.com')
        query = ScriptTranslator.translateT(g)
        g.iterate()
        # just enough to not explode
        proxy._explain(query)

    def test_profile(self) -> None:
        count = self._get(label=VertexTypes.User, key='jack', extra_traversal=__.count())
        self.assertEqual(count, 0)
        # just enough to not explode
        self._upsert(label=VertexTypes.User, key='jack', email='jack@squareup.com')
        # and show it ran
        count = self._get(label=VertexTypes.User, key='jack', extra_traversal=__.count())
        self.assertEqual(count, 1)
