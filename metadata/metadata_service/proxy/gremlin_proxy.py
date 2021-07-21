# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import collections
import json
import logging
from abc import abstractmethod
from datetime import date, datetime, timedelta
from operator import attrgetter
from typing import (Any, Callable, Dict, Iterable, List, Mapping, Optional,
                    Sequence, Set, Tuple, Type, TypeVar, Union, no_type_check,
                    overload)
from urllib.parse import unquote

import gremlin_python
from amundsen_common.entity.resource_type import ResourceType
from amundsen_common.models.dashboard import DashboardSummary
from amundsen_common.models.feature import Feature
from amundsen_common.models.generation_code import GenerationCode
from amundsen_common.models.lineage import Lineage
from amundsen_common.models.popular_table import PopularTable
from amundsen_common.models.table import (Application, Column,
                                          ProgrammaticDescription, Reader,
                                          Source, Stat, Table, Tag, Watermark)
from amundsen_common.models.user import User
from amundsen_gremlin.gremlin_model import (EdgeType, EdgeTypes, VertexType,
                                            VertexTypes, WellKnownProperties)
from amundsen_gremlin.gremlin_shared import \
    append_traversal as _append_traversal  # TODO: rename the references
from amundsen_gremlin.gremlin_shared import (make_column_uri,
                                             make_description_uri)
from amundsen_gremlin.neptune_bulk_loader.gremlin_model_converter import \
    ensure_vertex_type
from amundsen_gremlin.script_translator import (
    ScriptTranslator, ScriptTranslatorTargetJanusgraph)
from amundsen_gremlin.test_and_development_shard import get_shard
from gremlin_python.driver.client import Client
from gremlin_python.driver.driver_remote_connection import \
    DriverRemoteConnection
from gremlin_python.driver.resultset import ResultSet
from gremlin_python.driver.tornado.transport import TornadoTransport
from gremlin_python.process.anonymous_traversal import traversal
from gremlin_python.process.graph_traversal import (GraphTraversal,
                                                    GraphTraversalSource, V,
                                                    __, bothV, coalesce,
                                                    constant, has, inE, inV,
                                                    outE, outV, select, unfold,
                                                    valueMap, values)
from gremlin_python.process.traversal import Cardinality
from gremlin_python.process.traversal import Column as MapColumn
from gremlin_python.process.traversal import (Direction, Order, P, T, TextP,
                                              Traversal, gte, not_, within,
                                              without)
from neptune_python_utils.gremlin_utils import ExtendedGraphSONSerializersV3d0
from overrides import overrides
from tornado import httpclient
from typing_extensions import Protocol  # TODO: it's in typing 3.8

from metadata_service.entity.dashboard_detail import \
    DashboardDetail as DashboardDetailEntity
from metadata_service.entity.description import Description
from metadata_service.entity.tag_detail import TagDetail
from metadata_service.exception import NotFoundException
from metadata_service.proxy.statsd_utilities import timer_with_counter
from metadata_service.util import UserResourceRel

from .base_proxy import BaseProxy
from .shared import checkNotNone, retrying

# don't use statics.load_statics(globals()) it plays badly with mypy

__all__ = ['AbstractGremlinProxy', 'GenericGremlinProxy']

LOGGER = logging.getLogger(__name__)
PUBLISH_TAG_TIME_FORMAT: str = "%Y-%m-%d %H:%M"
AMUNDSEN_TIMESTAMP_KEY: str = 'amundsen_updated_timestamp'


def timestamp() -> datetime:
    """
    mostly for mocking
    See also https://docs.aws.amazon.com/neptune/latest/userguide/best-practices-gremlin-datetime-glv.html
    and DateIO in gremlin python
    """
    return datetime.now()


def is_reasonable_vertex_label(label: str) -> bool:
    vertex_labels = set([each.value.label for each in VertexTypes])
    return label in vertex_labels


def get_label_from(_entity_type_or_enum_or_str: Union[str, VertexTypes, EdgeTypes, VertexType, EdgeType]) -> str:
    if isinstance(_entity_type_or_enum_or_str, str):
        return _entity_type_or_enum_or_str
    elif isinstance(_entity_type_or_enum_or_str, (VertexTypes, EdgeTypes)):
        return _entity_type_or_enum_or_str.value.label
    elif isinstance(_entity_type_or_enum_or_str, (VertexType, EdgeType)):
        return _entity_type_or_enum_or_str.label
    else:
        raise RuntimeError(f'what the heck is label? {type(_entity_type_or_enum_or_str)} {_entity_type_or_enum_or_str}')


def get_cardinality_for(_entity_type_or_enum: Union[VertexTypes, EdgeTypes, VertexType, EdgeType],
                        name: str) -> Optional[Cardinality]:
    _entity_type: Union[VertexType, EdgeType]
    if isinstance(_entity_type_or_enum, (VertexTypes, EdgeTypes)):
        _entity_type = _entity_type_or_enum.value
    elif isinstance(_entity_type_or_enum, (VertexType, EdgeType)):
        _entity_type = _entity_type_or_enum
    else:
        raise AssertionError(f'thing is not a VertexType(s) or EdgeType(s): {_entity_type_or_enum}')
    properties = _entity_type.properties_as_map()

    # TODO: this will expose missing properties
    if name not in properties:
        raise AssertionError(f'missing {name} property in {_entity_type_or_enum} {properties}')

    maybe = properties[name].cardinality
    if isinstance(_entity_type, VertexType):
        return maybe.value if maybe is not None else Cardinality.single
    elif isinstance(_entity_type, EdgeType):
        return maybe.value if maybe is not None else None
    else:
        raise AssertionError(f'thing is not a VertexType(s) or EdgeType(s): {_entity_type_or_enum}')


class FromResultSet:
    @classmethod
    def generator(cls, result_set: ResultSet) -> Iterable[Any]:
        for part in result_set:
            for item in part:
                yield item

    @classmethod
    def iterate(cls, result_set: ResultSet) -> None:
        # haiku for consuming an interator
        collections.deque(cls.generator(result_set), maxlen=0)

    @classmethod
    def next(cls, result_set: ResultSet) -> Any:
        """
        really this is like first, but
        """
        return next(iter(cls.generator(result_set)))

    @classmethod
    def toList(cls, result_set: ResultSet) -> List:
        return list(cls.generator(result_set))

    @classmethod
    def toSet(cls, result_set: ResultSet) -> Set:
        return set(cls.generator(result_set))

    @classmethod
    def getOptional(cls, result_set: ResultSet) -> Optional[Any]:
        try:
            return cls.getOnly(result_set)
        except StopIteration:
            return None

    @classmethod
    def getOnly(cls, result_set: ResultSet) -> Any:
        i = iter(cls.generator(result_set))
        value = next(i)
        try:
            next(i)
        except StopIteration:
            return value
        raise RuntimeError('Expected one item, but there was more!')


TYPE = TypeVar('TYPE')


class ExecuteQuery(Protocol):
    @overload  # noqa: F811
    def __call__(self, query: Traversal, get: Callable[[ResultSet], V]) -> V:
        ...

    @overload  # noqa: F811
    def __call__(self, query: str, get: Callable[[ResultSet], V], *,  # noqa: F811
                 bindings: Optional[Mapping[str, Any]] = None) -> V:
        ...

    def __call__(self, query: Union[str, Traversal], get: Callable[[ResultSet], V], *,  # noqa: F811
                 bindings: Optional[Mapping[str, Any]] = None) -> V:
        ...


class ClientQueryExecutor(ExecuteQuery):
    def __init__(self, *, client: Client, traversal_translator: Callable[[Traversal], str]) -> None:
        self.client = client
        self.traversal_translator = traversal_translator

    def __call__(self, query: Union[str, Traversal], get: Callable[[ResultSet], V], *,  # noqa: F811
                 bindings: Optional[Mapping[str, Any]] = None) -> V:
        if isinstance(query, Traversal):
            if bindings is not None:
                raise AssertionError(f'expected bindings to be none')
            query_text = self.traversal_translator(query)
        else:
            query_text = query

        if not isinstance(query_text, str):
            raise AssertionError(f'expected str')
        result_set = self.client.submit(query_text, bindings)
        return get(result_set)


class RetryingClientQueryExecutor(ClientQueryExecutor):
    def __init__(self, client: Client, traversal_translator: Callable[[Traversal], str],
                 is_retryable: Callable[[Exception], bool]) -> None:
        ClientQueryExecutor.__init__(self, client=client, traversal_translator=traversal_translator)
        self.is_retryable = is_retryable

    def __enter__(self) -> Any:
        return self

    def __exit__(self, *args: Any, **kwargs: Any) -> None:
        return self.client.close()

    # TODO: ideally this would be __call__(*args: Any, **kwargs: Any) -> Any (and then this could be mixinable) but I
    # can't get mypy to not think that conflicts
    def __call__(self, query: Union[str, Traversal], get: Callable[[ResultSet], V], *,
                 bindings: Optional[Mapping[str, Any]] = None) -> V:
        def callable() -> V:
            return ClientQueryExecutor.__call__(self, query, get, bindings=bindings)
        try:
            return retrying(callable, is_retryable=self.is_retryable)
        except Exception as e:
            LOGGER.warning(f'got exception executing query={query}, get={get}, bindings={bindings}', exc_info=e)
            raise


@no_type_check
def _safe_get_any(root, *keys):
    """
    Helper method for getting value from nested dict, special for Gremlin valueMap things where properties can be lists
    of one or 0.
    :param root:
    :param keys:
    :return:
    """
    current = root
    for key in keys:
        # first get the only element if it's a list/set
        if isinstance(current, Sequence):
            if len(current) > 1:
                raise RuntimeError(f'{current} is not a singleton!  root={root} keys={keys}')
            elif len(current) == 0:
                current = None
            else:
                current = current[0]
        if not current:
            return None
        if not isinstance(current, Mapping):
            raise RuntimeError(f'{current} is not a Mapping!  root={root} keys={keys}')
        current = current.get(key)
        if not current:
            return None
    # don't dereference the list this usually is, we might want it or not
    return current


@no_type_check
def _safe_get_list(root, *keys, transform: Optional[Callable] = None):
    """
    Like _safe_get_any, but for gremlin where we get a list for a single property
    """
    values = _safe_get_any(root, *keys)
    # is List the only type? it seems so
    if values is None:
        return None
    elif not isinstance(values, List):
        raise RuntimeError(f'{values} is not a List!  root={root} keys={keys}')
    elif transform is None:
        return sorted(values)
    elif len(values) > 0 and type(values[0]) == datetime and transform == int:
        # need to do something special for datetimes we are transforming into int's
        return sorted([transform(value.timestamp()) for value in values])
    else:
        return sorted([transform(value) for value in values])


@no_type_check
def _safe_get(root, *keys, transform: Optional[Callable] = None, default: Any = None):
    """
    Like _safe_get_any, but for gremlin where we get a list for a single property
    """
    value = _safe_get_list(root, *keys, transform=transform)
    if value is None or len(value) == 0:
        return default
    elif len(value) > 1:
        raise RuntimeError(f'{value} is not a singleton!  root={root} keys={keys}')
    else:
        return value[0]


def _properties_or_drop_if_changed_except(
        *excludes: str, label: Union[VertexTypes, EdgeTypes, VertexType, EdgeType],
        thing: Union[object, Dict[str, Any]], existing: Union[object, Dict[str, Any]]) -> GraphTraversal:
    if isinstance(thing, Mapping):
        _thing = thing
    elif hasattr(thing, '__dict__'):
        _thing = vars(thing)
    else:
        raise AssertionError(f'thing must be a dict or have __dict__: {type(thing)}')

    if isinstance(existing, Mapping):
        _existing = existing
    elif hasattr(existing, '__dict__'):
        _existing = vars(existing)
    else:
        raise AssertionError(f'existing must be a dict or have __dict__: {type(existing)}')

    def p(name: str) -> Optional[GraphTraversal]:
        return _property_or_drop_if_changed(name=name, value=_thing.get(name, None), existing=_existing.get(name, None),
                                            cardinality=get_cardinality_for(label, name))

    names = sorted(set(_thing.keys()).difference(set(excludes)))
    traversals = [t for t in [p(name) for name in names] if t is not None]
    return _append_traversal(__.start(), *traversals) if traversals else None


def _property_unchanged(*, value: Any, existing: Any, cardinality: Optional[Cardinality]) -> bool:
    # this is the usual case: either an Edge property (no cardinality) or Vertex property with Cardinality.single
    if existing is None:
        return value is None
    elif cardinality is None or cardinality == Cardinality.single:
        return tuple(existing) == (value,)
    elif cardinality in (Cardinality.set_, Cardinality.list_):
        return value in tuple(existing)
    else:
        return False


def _property_or_drop_if_changed(*, name: str, value: Any, existing: Any, cardinality: Optional[Cardinality]) \
        -> Optional[GraphTraversal]:
    """
    You want to use _vertex_property or _edge_property.
    """
    if _property_unchanged(value=value, existing=existing, cardinality=cardinality):
        return None
    elif value is None:
        return __.sideEffect(__.properties(name).drop())
    else:
        # complicated: edges can't have cardinality supplied and are implied to be single
        if cardinality is None:
            return __.property(name, value)
        else:
            return __.property(cardinality, name, value)


def _properties_or_drop_except(label: Union[VertexTypes, EdgeTypes, VertexType, EdgeType],
                               thing: Union[object, Dict[str, Any]], *excludes: str) -> GraphTraversal:
    if isinstance(thing, Mapping):
        pass
    elif hasattr(thing, '__dict__'):
        thing = vars(thing)
    else:
        raise AssertionError(f'must be a dict or have __dict__: {type(thing)}')
    g = __.start()
    for name in set(thing.keys()).difference(set(excludes)):
        g = _property_or_drop(g=g, name=name, value=thing.get(name, None), cardinality=get_cardinality_for(label, name))
    return g


def _properties_or_drop_of(label: Union[VertexTypes, EdgeTypes, VertexType, EdgeType],
                           thing: Union[object, Dict[str, Any]], *includes: str) -> GraphTraversal:
    if isinstance(thing, Mapping):
        pass
    elif hasattr(thing, '__dict__'):
        thing = vars(thing)
    else:
        raise AssertionError(f'must be a dict or have __dict__: {type(thing)}')
    g = __.start()
    for name in includes:
        g = _property_or_drop(g=g, name=name, value=thing.get(name, None), cardinality=get_cardinality_for(label, name))
    return g


def _properties_except(thing: Union[object, Dict[str, Any]], *excludes: str) -> Mapping[str, Any]:
    if isinstance(thing, Mapping):
        pass
    elif hasattr(thing, '__dict__'):
        thing = vars(thing)
    else:
        raise AssertionError(f'must be a dict or have __dict__: {type(thing)}')
    _excludes = set(excludes)
    return dict([(k, v) for k, v in thing.items() if k not in _excludes])


def _properties_of(thing: Union[object, Dict[str, Any]], *includes: str) -> Mapping[str, Any]:
    if isinstance(thing, Mapping):
        pass
    elif hasattr(thing, '__dict__'):
        thing = vars(thing)
    else:
        raise AssertionError(f'must be a dict or have __dict__: {type(thing)}')
    return dict([(k, thing.get(k, None)) for k in includes])


def _is_select_traversal(g: GraphTraversal) -> Optional[str]:
    if not g.bytecode.source_instructions and len(g.bytecode.step_instructions) == 1 and \
       len(g.bytecode.step_instructions[0]) == 2 and g.bytecode.step_instructions[0][0] == 'select':
        return g.bytecode.step_instructions[0][1]
    else:
        return None


def _vertex_property(*, g: GraphTraversal, name: str, value: Any, cardinality: Optional[Cardinality] = None,
                     label: Optional[VertexTypes] = None) -> GraphTraversal:

    if (cardinality is None) and (label is None):
        raise AssertionError('must pass one of label or cardinality')
    if cardinality is not None:
        _cardinality = cardinality
    elif label is not None:
        _cardinality = get_cardinality_for(label, name)
    else:
        raise RuntimeError()

    return _property_or_drop(g=g, name=name, value=value, cardinality=checkNotNone(_cardinality))


def _edge_property(*, g: GraphTraversal, name: str, value: Any) -> GraphTraversal:
    return _property_or_drop(g=g, name=name, value=value, cardinality=None)


def _property_or_drop(*, g: GraphTraversal, name: str, value: Any, cardinality: Optional[Cardinality]) \
        -> GraphTraversal:
    """
    You want to use _vertex_property or _edge_property.
    """
    if value is None:
        return g.sideEffect(__.properties(name).drop())
    else:
        # complicated: edges can't have cardinality supplied and are implied to be single
        p = __.property(name, value) if cardinality is None else __.property(cardinality, name, value)
        return _append_traversal(g, p)


def _V(label: Union[str, VertexTypes, VertexType], key: Optional[Union[str, TextP]],
       key_property_name: Optional[str] = None, g: Optional[Union[Traversal, GraphTraversalSource]] = None,
       **properties: Any) -> GraphTraversal:
    """
    Gets a vertex with the given label and key and returns the valueMap.  If no such vertex exists, None is
    returned.  (If more than one exists, which would be super surprising, an exception is raised.)
    """
    if g is None:
        g = __.start()
    properties = dict(properties or {})
    if isinstance(key, str):
        id = ensure_vertex_type(label).id(key=key)
        g = g.V(id)
    elif key is not None:
        # let's support predicates on the key, but need to limit it to either the test_shard (or unsharded perhaps)

        if key_property_name is None:
            raise AssertionError('expected key_property_name')
        g = g.V().has(get_label_from(label), key_property_name, key)
        if get_shard():
            properties.setdefault(WellKnownProperties.TestShard.value.name, get_shard())
    else:
        # let's support hasLabel, but need to limit it to either the test_shard (or unsharded perhaps)
        g = g.V().hasLabel(get_label_from(label))
        if get_shard():
            properties.setdefault(WellKnownProperties.TestShard.value.name, get_shard())

    # should we do this when using the V(id)? there are a couple or one case where we use it to filter  so seems handy
    if properties is not None:
        for name, value in properties.items():
            if value is not None:
                # you can have value be a predicate, like within('foo','bar') or such
                g = g.has(name, value)
            else:
                g = g.hasNot(name)

    return g


def _has(*, g: Traversal, label: Union[None, str, VertexTypes, EdgeTypes, VertexType, EdgeType],
         key: Optional[str], key_property_name: Optional[str] = 'key',
         properties: Optional[Mapping[str, Any]] = None) -> GraphTraversal:
    """
    Matches a vertex or edge with the given label and key
    """

    if (label is None) and (key is None) and (properties is None):
        raise AssertionError('at least label or key or properties must be present')
    if label is not None:
        _label = get_label_from(label)
        if key is None:
            g = g.hasLabel(_label)
        else:
            if key_property_name is None:
                raise AssertionError('must supply key_property_name if supplying key')
            # you can have key be a predicate, like within('foo','bar') or such
            g = g.has(_label, key_property_name, key)
    elif key is not None:
        if key_property_name is None:
            raise AssertionError('must supply key_property_name if supplying key')
        g = g.has(key_property_name, key)

    # don't usually need to blend in the shard for test isolation (since _has almost always is used at the end of a
    # traversal rooted in one component)

    if properties is not None:
        for name, value in properties.items():
            if value is not None:
                # you can have value be a predicate, like within('foo','bar') or such
                g = g.has(name, value)
            else:
                g = g.hasNot(name)

    return g


def _upsert(*, executor: ExecuteQuery, execute: Callable[[ResultSet], TYPE] = FromResultSet.getOnly,
            g: GraphTraversalSource, label: Union[VertexTypes, VertexType], key_property_name: str, key: str,
            traversal_if_exists: Optional[Traversal] = None, traversal_if_add: Optional[Traversal] = None,
            traversal: Optional[Traversal] = __.id(), **properties: Any) -> TYPE:

    if not isinstance(label, (VertexTypes, VertexType)):
        raise AssertionError(f'expected label to be a VertexType or VertexTypes: {label}')
    if isinstance(label, VertexTypes):
        id = label.value.id(key=key, **properties)
    elif isinstance(label, VertexType):
        id = label.id(key=key, **properties)
    else:
        raise AssertionError('wat')  # appease mypy
    if get_shard():
        properties.setdefault(WellKnownProperties.TestShard.value.name, get_shard())

    existing_node = executor(query=g.V(id).valueMap(True), get=FromResultSet.getOptional)
    _label = get_label_from(label)

    if existing_node is None:
        add = __.addV(_label).property(T.id, id).property(Cardinality.single, key_property_name, key)
        set_properties = _properties_or_drop_except(label, properties) if properties else None
        g = _append_traversal(g, add, traversal_if_add, set_properties, traversal)
    else:
        # get existing vertex...
        get = __.V(id)
        set_properties = _properties_or_drop_if_changed_except(
            label=label, thing=properties, existing=existing_node) if properties else None
        g = _append_traversal(g, get, traversal_if_exists, set_properties, traversal)

    # return the result
    return executor(query=g, get=execute)


def _link(*, executor: ExecuteQuery, execute: Optional[Callable[[ResultSet], TYPE]] = None,  # noqa: C901
          g: GraphTraversalSource, edge_label: Union[EdgeTypes, EdgeType], key_property_name: Optional[str] = None,
          vertex1_label: Optional[Union[str, VertexTypes]] = None, vertex1_key: Optional[str] = None,
          vertex2_label: Optional[Union[str, VertexTypes]] = None, vertex2_key: Optional[str] = None,
          vertex1_id: Optional[Any] = None, vertex2_id: Optional[Any] = None,
          edge_properties: Dict[str, Any] = {}, traversal_if_exists: Optional[Traversal] = None,
          traversal_if_add: Optional[Traversal] = None, traversal: Optional[Traversal] = None,
          **properties: Any) -> Optional[TYPE]:
    """
    Creates an edge from vertex 1 to vertex 2 with a given label, if such
    an edge does not exist.  It does not create vertex1 or vertex 2, so if
    they don't exist, you will get some kind of error (usually an interation error).

    :param edge_properties: A map of edge properties and values to be used for
                            edge idempotence. If an unexpired edge with these
                            properties and values exists, no edge will be created.

    """

    if (vertex1_label is not None and vertex1_key is not None) == (vertex1_id is not None):
        raise AssertionError(f'pass either vertex1_label and vertex1_key or vertex1_id, but not both')
    if (vertex2_label is not None and vertex2_key is not None) == (vertex2_id is not None):
        raise AssertionError(f'pass either vertex2_label and vertex2_key or vertex2_id, but not both')

    # Return the raw id of a vertex
    if vertex1_id is None:
        if (key_property_name is None) or (vertex1_label is None):
            raise AssertionError(f'expected both key_property_name and vertex1_label')
        # we used to query to find this, but now that we're deterministically generating them we can do:
        vertex1_id = ensure_vertex_type(vertex1_label).id(**{key_property_name: vertex1_key})
        # but let's query to ensure it exists (which the previous pattern also ensured
        executor(query=g.V(vertex1_id), get=FromResultSet.getOnly)

    if vertex2_id is None:
        if (key_property_name is None) or (vertex2_label is None):
            raise AssertionError(f'expected both key_property_name and vertex2_label')
        vertex2_id = ensure_vertex_type(vertex2_label).id(**{key_property_name: vertex2_key})
        executor(query=g.V(vertex2_id), get=FromResultSet.getOnly)

    if (vertex1_id is None) or (vertex2_id is None):
        raise AssertionError(f'vertex1_label={vertex1_label}, vertex1_key={vertex1_key} \
                               or vertex2_label={vertex2_label}, vertex2_key={vertex2_key} either does not exist! \
                               vertex1_id={vertex1_id}, vertex2_id={vertex2_id}')

    _label = get_label_from(edge_label)

    edge_traversal = g.V(vertex1_id).outE(_label).where(__.inV().hasId(vertex2_id))
    for key, value in edge_properties.items():
        edge_traversal = edge_traversal.has(key, value)
    edge_id = executor(query=edge_traversal.id(), get=FromResultSet.getOptional)

    # If no link exists, create one!
    if edge_id is None:
        g = g.V(vertex1_id).as_('one').V(vertex2_id).addE(_label).from_('one').property('created', timestamp())
        g = _append_traversal(g, traversal_if_add)
    else:
        # Just get the edge in case we need to add properties
        g = _append_traversal(g.E(edge_id), traversal_if_exists)

    if properties:
        g = _append_traversal(g, _properties_or_drop_except(edge_label, properties))

    # updated properties, etc.
    if traversal is not None:
        g = _append_traversal(g, traversal)

    # return the result
    return executor(query=g, get=execute if execute is not None else FromResultSet.getOnly)


def _expire_other_links(  # noqa: C901
        *, executor: ExecuteQuery, g: GraphTraversalSource,
        edge_label: EdgeTypes, key_property_name: Optional[str] = None,
        vertex1_label: Optional[Union[str, VertexTypes]] = None, vertex1_key: Optional[str] = None,
        vertex2_label: Optional[Union[str, VertexTypes]] = None, vertex2_key: Optional[str] = None,
        vertex1_id: Optional[Union[int, str, P]] = None, vertex2_id: Optional[Union[int, str, P]] = None,
        edge_direction: Direction = Direction.OUT,
        **properties: Any) -> None:
    """
    Expires edges of a given label other than the ones connecting
    vertex 1 and 2. If keys are not specified, will expire all edges between the two
    vertex types
    """

    if (vertex1_label is not None) == (vertex1_id is not None):
        raise AssertionError('pass either vertex1_label and vertex1_key or vertex1_id, but not both')
    if (vertex2_label is not None) == (vertex2_id is not None):
        raise AssertionError('pass either vertex2_label and vertex2_key or vertex2_id, but not both')

    # Return the raw id of a vertex
    if vertex1_id is None:
        if (key_property_name is None) or (vertex1_label is None):
            raise AssertionError(f'expected both key_property_name and vertex1_label')
        # we used to query to find this, but now that we're deterministically generating them we can do:
        vertex1_id = ensure_vertex_type(vertex1_label).id(**{key_property_name: vertex1_key})
        # but let's query to ensure it exists (which the previous pattern also ensured
        executor(query=g.V(vertex1_id), get=FromResultSet.getOnly)

    if vertex2_id is None and vertex2_key is not None:
        # TODO support getting more than one here
        if (key_property_name is None) or (vertex2_label is None):
            raise AssertionError(f'expected both key_property_name and vertex2_label')
        vertex2_id = ensure_vertex_type(vertex2_label).id(**{key_property_name: vertex2_key})
        executor(query=g.V(vertex2_id), get=FromResultSet.getOnly)

    if vertex1_id is not None:
        g = g.V(vertex1_id)
    else:
        if vertex1_label is None:
            raise AssertionError(f'expected vertex1_label')
        g = g.V().hasLabel(get_label_from(vertex1_label))

    # Traverse the edges from vertex 1
    if edge_direction == Direction.OUT:
        g = g.outE(get_label_from(edge_label))
    else:
        g = g.inE(get_label_from(edge_label))
    g = g

    # Find edges to vertexes with the label but an id that isn't vertex 2
    _filter = __.inV() if edge_direction == Direction.OUT else __.outV()
    if vertex2_id is None:
        if vertex2_label is None:
            raise AssertionError(f'expected vertex2_label')
        g = g.filter(_filter)
    elif isinstance(vertex2_id, (int, str)):
        g = g.filter(_append_traversal(_filter, __.id().is_(P.neq(vertex2_id))))
    elif isinstance(vertex2_id, P):
        g = g.filter(_append_traversal(_filter, __.id().is_(not_(vertex2_id))))
    g = g.drop()
    executor(g, get=FromResultSet.iterate)


def _expire_link(*, executor: ExecuteQuery, g: GraphTraversalSource,
                 key_property_name: str, edge_label: Union[EdgeTypes, EdgeType],
                 vertex1_label: Optional[Union[str, VertexTypes, VertexType]] = None,
                 vertex1_key: Optional[Union[str, P]] = None,
                 vertex1_id: Optional[Union[int, str, P]] = None,
                 vertex2_label: Optional[Union[str, VertexTypes, VertexType]] = None,
                 vertex2_key: Optional[Union[str, P]] = None,
                 vertex2_id: Optional[Union[int, str, P]] = None) -> None:
    """
    Expires link between two vertices. Refer to vertices either by supplying
    label + key, or by providing the gremlin vertex ids directly
    """
    if (vertex1_label is not None and vertex1_key is not None) == (vertex1_id is not None):
        raise AssertionError(f'pass either vertex1_label and vertex1_key or vertex1_id, but not both')
    if (vertex2_label is not None and vertex2_key is not None) == (vertex2_id is not None):
        raise AssertionError(f'pass either vertex2_label and vertex2_key or vertex2_id, but not both')

    # Return the raw ids of the vertices
    if vertex1_id is None:
        if (key_property_name is None) or (vertex1_label is None):
            raise AssertionError(f'expected both key_property_name and vertex1_label')
        # we used to query to find this, but now that we're deterministically generating them we can do:
        vertex1_id = ensure_vertex_type(vertex1_label).id(**{key_property_name: vertex1_key})
        # but let's query to ensure it exists (which the previous pattern also ensured
        executor(query=g.V(vertex1_id), get=FromResultSet.getOnly)

    if vertex2_id is None:
        if (key_property_name is None) or (vertex2_label is None):
            raise AssertionError(f'expected both key_property_name and vertex2_label')
        # we used to query to find this, but now that we're deterministically generating them we can do:
        vertex2_id = ensure_vertex_type(vertex2_label).id(**{key_property_name: vertex2_key})
        # but let's query to ensure it exists (which the previous pattern also ensured
        executor(query=g.V(vertex2_id), get=FromResultSet.getOnly)

    if (vertex1_id is None) or (vertex2_id is None) or (vertex1_id == vertex2_id):
        raise AssertionError(f'pass either vertex1_label and vertex1_key or vertex1_id, but not both')

    g = g.V(vertex1_id)
    g = g.bothE(get_label_from(edge_label)).where(bothV().hasId(vertex2_id))
    g = g.drop()
    executor(g, get=FromResultSet.iterate)


def _edges_between(*, g: Traversal, label: Union[None, str, EdgeTypes, EdgeType], vertex1: Traversal,
                   vertex2: Traversal, **properties: Any) -> GraphTraversal:
    """
    get the edges from vertex1
    """
    vertex1_alias = _is_select_traversal(vertex1)
    if vertex1_alias is None:
        vertex1_alias = 'one'
        g = _append_traversal(g, vertex1).as_(vertex1_alias)

    vertex2_alias = _is_select_traversal(vertex1)
    g = _append_traversal(g, vertex2)

    if (vertex1_alias is None) or (vertex1_alias == vertex2_alias):
        raise AssertionError(f'vertex1_alias={vertex1_alias}, vertex2_alias={vertex2_alias}')

    if label is not None:
        g = g.bothE(get_label_from(label))
    else:
        g = g.bothE()

    g = g.where(__.otherV().as_(vertex1_alias))

    if 'expired' not in properties:
        properties['expired'] = None

    g = _has(g=g, properties=properties, label=None, key_property_name=None, key=None)
    return g


def _edges_from(*, g: Union[GraphTraversalSource, GraphTraversal],
                vertex1_label: Union[str, VertexTypes, VertexType], vertex1_key: str,
                vertex1_properties: Optional[Mapping[str, Any]] = None,
                vertex2_label: Optional[Union[str, VertexTypes, VertexType]], vertex2_key: Optional[str],
                vertex2_properties: Optional[Mapping[str, Any]] = None,
                edge_label: Optional[Union[str, EdgeTypes, EdgeType]],
                **edge_properties: Any) -> GraphTraversal:
    """
    get the edges from vertex1
    """
    vertex1 = _V(g=__.start(), label=vertex1_label, key=vertex1_key, **(vertex1_properties or {}))

    if vertex2_label is None and vertex2_key is None and not vertex2_properties:
        vertex2 = None
    else:
        vertex2 = _has(g=__.start(), label=vertex2_label, key=vertex2_key, properties=vertex2_properties or {})

    g = _append_traversal(g, vertex1)

    if edge_label is not None:
        g = g.outE(get_label_from(edge_label))
    else:
        g = g.outE()

    if 'expired' not in edge_properties:
        edge_properties['expired'] = None
    g = _has(g=g, label=None, key=None, key_property_name=None, properties=edge_properties)

    if vertex2 is not None:
        g = g.where(_append_traversal(__.otherV(), vertex2))

    return g


def _edges_to(*, g: Union[GraphTraversalSource, GraphTraversal],
              vertex1_label: Union[str, VertexTypes, VertexType], vertex1_key: str,
              vertex1_properties: Optional[Mapping[str, Any]] = None,
              vertex2_label: Optional[Union[str, VertexTypes, VertexType]], vertex2_key: Optional[str],
              vertex2_properties: Optional[Mapping[str, Any]] = None,
              edge_label: Optional[Union[str, EdgeTypes, EdgeType]],
              **edge_properties: Any) -> GraphTraversal:
    """
    get the edges to vertex1
    """
    vertex1 = _V(g=__.start(), label=vertex1_label, key=vertex1_key, **(vertex1_properties or {}))

    if vertex2_label is None and vertex2_key is None and not vertex2_properties:
        vertex2 = None
    else:
        vertex2 = _has(g=__.start(), label=vertex2_label, key=vertex2_key, properties=vertex2_properties or {})

    g = _append_traversal(g, vertex1)

    if edge_label is not None:
        g = g.inE(get_label_from(edge_label))
    else:
        g = g.inE()

    g = _has(g=g, label=None, key=None, key_property_name=None, properties=edge_properties)

    if vertex2 is not None:
        g = g.where(_append_traversal(__.otherV(), vertex2))

    return g


def _parse_gremlin_server_error(exception: Exception) -> Dict[str, Any]:
    if not isinstance(exception, gremlin_python.driver.protocol.GremlinServerError) or len(exception.args) != 1:
        return {}
    # this is like '444: {...json object...}'
    return json.loads(exception.args[0][exception.args[0].index(': ') + 1:])


class AbstractGremlinProxy(BaseProxy):
    """
    A proxy to a server using TinkerPop Gremlin (e.g. JanusGraph, AWS Neptune, Azure CosmosDB, NEO4J with the gremlin
    plugin).  There are some differences between them!  The implementation here is intended to not rely on features of
    any one of them very much.

    :param key_property_name defaults to 'key', but some some servers don't allow key so their proxies will pick a different key property name (e.g. _key)
    :param remote_connection a RemoteConnection e.g. `DriverRemoteConnection(url='wss://host:8182/gremlin')`

    If you see:
    gremlin_python.driver.protocol.GremlinServerError: 498: {"requestId":"80a1d05e-bcde-4f43-95c7-d48db3966c0a","code":"UnsupportedOperationException","detailedMessage:"com.amazon.neptune.storage.volcano.ast.CutoffNode cannot be cast to com.amazon.neptune.storage.volcano.ast.AbstractGroupNode"}
    go look at https://stackoverflow.com/questions/58720484/gremlin-neptune-sort-edges-by-vertex-property

    === A short guide to writing queries that support the test sharding. ===
    The round trip tests are not fast.  To improve our experience, we are running tests in parallel, which means that
    tests need to play nicely with each other.  The simplest way to do this is start queries with some method that will
    restrict the query to a subgraph for the test shard: _V, _upsert, _edges_to, _edges_from, _edges_between. What they
    do is either get vertex id (which are specific to test shards), or sprinkle in a .property('shard', xxx) filter.
    You will almost certainly not need to observe this in tests, but may need to in the proxy code/queries.

    """  # noqa: E501

    def __init__(self, *, key_property_name: str, driver_remote_connection_options: Mapping[str, Any] = {},
                 gremlin_client_options: Mapping[str, Any] = {}) -> None:
        # these might vary from datastore type to another, but if you change these while talking to the same instance
        # without migration, it will go poorly
        self.key_property_name: str = key_property_name

        self.driver_remote_connection_options = dict(driver_remote_connection_options or {})
        self.gremlin_client_options = dict(gremlin_client_options or {})
        self.gremlin_client_options.setdefault(
            'traversal_source', self.driver_remote_connection_options.get('traversal_source', 'g'))
        # set message_serializer in client creation
        # override these since we need so little
        self.gremlin_client_options.setdefault('pool_size', 1),
        self.gremlin_client_options.setdefault('max_workers', 1),

        # safe this for use in _submit
        self.remote_connection: DriverRemoteConnection = DriverRemoteConnection(
            url=self.possibly_signed_ws_client_request_or_url(),
            transport_factory=lambda: TornadoTransport(read_timeout=None, write_timeout=None),
            **_properties_except(self.driver_remote_connection_options, 'url'))

        self._g: GraphTraversalSource = traversal().withRemote(self.remote_connection)

    def drop(self) -> None:
        LOGGER.warning('DROPPING ALL NODES')
        with self.query_executor() as executor:
            executor(query=self.g.V().drop(), get=FromResultSet.iterate)
        LOGGER.warning('COMPLETED DROP OF ALL NODES')

    @property
    def g(self) -> GraphTraversalSource:
        """
        might not actually refer to g, but usually is so let's call it that here.  no setter so we don't accidentally
        self.g = somewhere
        """
        return self._g

    @classmethod
    def get_is_retryable(cls, method_name: str) -> Callable[[Exception], bool]:
        def is_retryable(exception: Exception) -> bool:
            nonlocal method_name
            return cls._is_retryable_exception(method_name=method_name, exception=exception)
        return is_retryable

    @classmethod
    @abstractmethod
    def script_translator(cls) -> Type[ScriptTranslator]:
        pass

    @abstractmethod
    def possibly_signed_ws_client_request_or_url(self) -> Union[httpclient.HTTPRequest, str]:
        pass

    def client(self) -> Client:
        gremlin_client_options = dict(self.gremlin_client_options)
        gremlin_client_options.setdefault('message_serializer', ExtendedGraphSONSerializersV3d0())
        gremlin_client_options['url'] = self.possibly_signed_ws_client_request_or_url()
        return Client(**gremlin_client_options)

    def query_executor(self, *, method_name: str = "nope") -> \
            RetryingClientQueryExecutor:
        return RetryingClientQueryExecutor(
            client=self.client(), is_retryable=self.get_is_retryable(method_name),
            traversal_translator=self.script_translator().translateT)

    @classmethod
    def _is_retryable_exception(cls, *, method_name: str, exception: Exception) -> bool:
        """
        overridde this if you want to retry the exception for the given method_name
        """
        return False

    def _submit(self, *, command: str, bindings: Any = None) -> Any:
        """
        Do not use this.

        ...except if you are doing graph management or other things not supported by Gremlin.  For example, with
        JanusGraph, you might:

        >>> self._submit('''
        graph.tx().rollback()
        mgmt = graph.openManagement()
        keyProperty = mgmt.getPropertyKey('_key')
        vertexLabel = mgmt.getVertexLabel('Table')
        mgmt.buildIndex('TableByKeyUnique', Vertex.class).addKey(keyProperty).indexOnly(vertexLabel).unique().buildCompositeIndex()
        mgmt.commit()
        ''')

        >>> self._submit('''
        graph.openManagement().getGraphIndex('TableByKey')
        ''')

        >>> self._submit('''
        graph.openManagement().getGraphIndexes(Vertex.class)
        ''')

        >>> self._submit('''
        graph.openManagement().getGraphIndexes(Edge.class)
        ''')

        """  # noqa: E501

        # we use the client from the DriverRemoteConnection, which is sneaky.  We could probably pull out parameters
        # from the DriverRemoteConnection and construct a Client directly, but that feels even sneakier and more
        # fragile.
        return self.remote_connection._client.submit(message=command, bindings=bindings).all().result()

    def is_healthy(self) -> None:
        # throws if cluster unhealthy or can't connect.  Neptune proxy overrides and uses status endpoint
        self.query_executor()(query=self.g.V().limit(0).fold, get=FromResultSet.iterate)

    def get_relationship(self, *, node_type1: str, node_key1: str, node_type2: str, node_key2: str) -> List[Any]:
        """
        This method is largely meant for testing. It returns any relationships between
        two nodes

        See AbstractProxyTest
        """
        g = self.g
        g = _V(g=g, label=node_type1, key=node_key1).as_('v')
        g = _V(g=g, label=node_type2, key=node_key2)
        g = g.bothE()
        # as creates an alias, BUT ALSO in filter, where, or some other predicate filters the traversal with the
        # previously aliased value (which is what it does here)
        g = g.where(__.otherV().as_('v'))
        g = g.valueMap()
        return self.query_executor()(query=g, get=FromResultSet.toList)

    @timer_with_counter
    @overrides
    def get_user(self, *, id: str) -> Union[User, None]:
        g = _V(g=self.g, label=VertexTypes.User, key=id).as_('user')
        g = g.coalesce(outE(EdgeTypes.ManagedBy.value.label).inV().
                       hasLabel(VertexTypes.User.value.label).fold()).as_('managers')
        g = g.select('user', 'managers').by(valueMap()).by(unfold().valueMap().fold())
        results = self.query_executor()(query=g, get=FromResultSet.toList)

        result = _safe_get(results)
        if not result:
            return result

        user = self._convert_to_user(result['user'])
        managers = _safe_get_list(result, 'managers')
        user.manager_fullname = _safe_get(managers[0], 'full_name', default=None) if managers else None
        return user

    def _get_user(self, *, id: str, executor: ExecuteQuery) -> Union[User, None]:
        g = _V(g=self.g, label=VertexTypes.User, key=id).as_('user')
        g = g.coalesce(outE(EdgeTypes.ManagedBy.value.label).inV().
                       hasLabel(VertexTypes.User.value.label).fold()).as_('managers')
        g = g.select('user', 'managers').by(valueMap()).by(unfold().valueMap().fold())
        results = executor(query=g, get=FromResultSet.toList)

        result = _safe_get(results)
        if not result:
            return result

        user = self._convert_to_user(result['user'])
        managers = _safe_get_list(result, 'managers')
        user.manager_fullname = _safe_get(managers[0], 'full_name', default=None) if managers else None
        return user

    def create_update_user(self, *, user: User) -> Tuple[User, bool]:
        pass

    @timer_with_counter
    @overrides
    def get_users(self) -> List[User]:
        g = _V(g=self.g, label=VertexTypes.User, key=None).not_(has('is_active', False)).as_('user'). \
            coalesce(outE(EdgeTypes.ManagedBy.value.label).inV().
                     hasLabel(VertexTypes.User.value.label).fold()).as_('managers'). \
            select('user', 'managers').by(valueMap()).by(unfold().valueMap().fold())
        results = self.query_executor()(query=g, get=FromResultSet.toList)

        users = []
        for result in results:
            user = self._convert_to_user(result['user'])
            managers = _safe_get_list(result, 'managers')
            user.manager_fullname = _safe_get(managers[0], 'full_name', default=None) if managers else None
            users.append(user)
        return users

    @timer_with_counter
    @overrides
    def get_table(self, *, table_uri: str, is_reviewer: bool = False) -> Table:
        """
        :param table_uri: Table URI
        :return:  A Table object
        """

        result = self._get_table_itself(table_uri=table_uri)
        if not result:
            raise NotFoundException(f'Table URI( {table_uri} ) does not exist')

        cols = self._get_table_columns(table_uri=table_uri)
        readers = self._get_table_readers(table_uri=table_uri)

        users_by_type: Dict[str, List[User]] = {}
        users_by_type['owner'] = _safe_get_list(result, f'all_owners', transform=self._convert_to_user) or []

        stats = _safe_get_list(result, 'stats', transform=self._convert_to_statistics) or []

        # add in the last 5 days (but only if present according to test)
        def transform(x: int) -> Optional[Stat]:
            return None if x == 0 else Stat(stat_type='num_reads_last_5_days', stat_val=str(x))
        num_reads_last_5_days = _safe_get(result, 'num_reads_last_5_days', transform=transform)
        if num_reads_last_5_days:
            stats.append(num_reads_last_5_days)

        table = Table(database=_safe_get(result, 'database', 'name'),
                      cluster=_safe_get(result, 'cluster', 'name'),
                      schema=_safe_get(result, 'schema', 'name'),
                      name=_safe_get(result, 'table', 'name'),
                      key=_safe_get(result, 'table', self.key_property_name),
                      is_view=_safe_get(result, 'table', 'is_view'),
                      tags=_safe_get_list(result, 'tags', transform=self._convert_to_tag) or [],
                      description=_safe_get(result, 'description', 'description'),
                      programmatic_descriptions=_safe_get_list(
                          result, 'programmatic_descriptions', transform=self._convert_to_description) or [],
                      columns=cols,
                      table_readers=readers,
                      watermarks=_safe_get_list(result, 'watermarks', transform=self._convert_to_watermark) or [],
                      table_writer=_safe_get(result, 'application', transform=self._convert_to_application),
                      last_updated_timestamp=_safe_get(result, 'timestamp', transform=int),
                      source=_safe_get(result, 'source', transform=self._convert_to_source),
                      owners=users_by_type['owner'])

        return table

    def _get_table_itself(self, *, table_uri: str) -> Mapping[str, Any]:
        g = _V(g=self.g, label=VertexTypes.Table, key=table_uri).as_('table')
        g = g.coalesce(inE(EdgeTypes.Table.value.label).outV().
                       hasLabel(VertexTypes.Schema.value.label).fold()).as_('schema')
        g = g.coalesce(unfold().inE(EdgeTypes.Schema.value.label).outV().
                       hasLabel(VertexTypes.Cluster.value.label).fold()).as_('cluster')
        g = g.coalesce(unfold().inE(EdgeTypes.Cluster.value.label).outV().
                       hasLabel(VertexTypes.Database.value.label).fold()).as_('database')
        g = g.coalesce(select('table').inE(EdgeTypes.BelongToTable.value.label).outV().
                       hasLabel(VertexTypes.Watermark.value.label).fold()).as_('watermarks')
        g = g.coalesce(select('table').inE(EdgeTypes.Generates.value.label).outV().
                       hasLabel(VertexTypes.Application.value.label).fold()).as_('application')
        g = g.coalesce(select('table').outE(EdgeTypes.LastUpdatedAt.value.label).inV().
                       hasLabel(VertexTypes.Updatedtimestamp.value.label).
                       values('timestamp').fold()).as_('timestamp')
        g = g.coalesce(select('table').inE(EdgeTypes.Tag.value.label).outV().
                       hasLabel(VertexTypes.Tag.value.label).fold()).as_('tags')
        g = g.coalesce(select('table').outE(EdgeTypes.Source.value.label).inV().
                       hasLabel(VertexTypes.Source.value.label).fold()).as_('source')
        g = g.coalesce(select('table').outE(EdgeTypes.Stat.value.label).inV().
                       hasLabel(VertexTypes.Stat.value.label).fold()).as_('stats')
        g = g.coalesce(select('table').outE(EdgeTypes.Description.value.label).
                       inV().hasLabel(VertexTypes.Description.value.label).fold()).as_('description')
        g = g.coalesce(
            select('table').out(EdgeTypes.Description.value.label).hasLabel('Programmatic_Description').fold()
        ).as_('programmatic_descriptions')
        g = g.coalesce(select('table').inE(EdgeTypes.Read.value.label).
                       has('date', gte(date.today() - timedelta(days=5))).
                       where(outV().hasLabel(VertexTypes.User.value.label)).
                       # TODO: is this wrong? (the test expects count instead of sum it seems)
                       values('read_count').sum().fold()).as_('num_reads_last_5_days')

        for user_label, edge_type in dict(owner=EdgeTypes.Owner, admin=EdgeTypes.Admin,
                                          rw=EdgeTypes.ReadWrite, ro=EdgeTypes.ReadOnly).items():
            g = g.coalesce(select('table').outE(edge_type.value.label).inV().
                           hasLabel(VertexTypes.User.value.label).fold()).as_(f'all_{user_label}s')

        g = g.select('table', 'schema', 'cluster', 'database',
                     'watermarks', 'application', 'timestamp', 'tags', 'source', 'stats',
                     'description', 'programmatic_descriptions', 'all_owners',
                     'num_reads_last_5_days'). \
            by(valueMap()). \
            by(unfold().dedup().valueMap().fold()). \
            by(unfold().dedup().valueMap().fold()). \
            by(unfold().dedup().valueMap().fold()). \
            by(unfold().dedup().valueMap().fold()). \
            by(unfold().dedup().valueMap().fold()). \
            by(). \
            by(unfold().dedup().valueMap().fold()). \
            by(unfold().dedup().valueMap().fold()). \
            by(unfold().dedup().valueMap().fold()). \
            by(unfold().dedup().valueMap().fold()). \
            by(unfold().dedup().valueMap().fold()). \
            by(unfold().dedup().valueMap().fold()). \
            by()

        results = self.query_executor()(query=g, get=FromResultSet.toList)
        return _safe_get(results)

    def _get_table_columns(self, *, table_uri: str) -> List[Column]:
        g = _V(g=self.g, label=VertexTypes.Table.value.label, key=table_uri). \
            outE(EdgeTypes.Column.value.label). \
            inV().hasLabel(VertexTypes.Column.value.label).as_('column')
        g = g.coalesce(
            select('column').out(EdgeTypes.Description.value.label).hasLabel(VertexTypes.Description.value.label).fold()
        ).as_('description')
        g = g.coalesce(select('column').outE(EdgeTypes.Stat.value.label).inV().
                       hasLabel(VertexTypes.Stat.value.label).fold()).as_('stats')
        g = g.select('column', 'description', 'stats'). \
            by(valueMap()). \
            by(unfold().valueMap().fold()). \
            by(unfold().valueMap().fold())
        results = self.query_executor()(query=g, get=FromResultSet.toList)

        cols = []
        for result in results:
            col = Column(name=_safe_get(result, 'column', 'name'),
                         key=_safe_get(result, 'column', self.key_property_name),
                         description=_safe_get(result, 'description', 'description'),
                         col_type=_safe_get(result, 'column', 'col_type'),
                         sort_order=_safe_get(result, 'column', 'sort_order', transform=int),
                         stats=_safe_get_list(result, 'stats', transform=self._convert_to_statistics) or [])
            cols.append(col)
        cols = sorted(cols, key=attrgetter('sort_order'))
        return cols

    def _get_table_readers(self, *, table_uri: str) -> List[Reader]:
        g = _edges_to(g=self.g, vertex1_label=VertexTypes.Table, vertex1_key=table_uri,
                      vertex2_label=VertexTypes.User, vertex2_key=None,
                      edge_label=EdgeTypes.Read, date=gte(date.today() - timedelta(days=5)))
        g = g.order().by(coalesce(__.values('read_count'), constant(0)), Order.decr).limit(5)
        g = g.project('user', 'read', 'table')
        g = g.by(outV().project('id', 'email').by(values('user_id')).by(values('email')))
        g = g.by(coalesce(values('read_count'), constant(0)))
        g = g.by(inV().values('name'))
        results = self.query_executor()(query=g, get=FromResultSet.toList)

        readers = []
        for result in results:
            # no need for _safe_get in here because the query
            readers.append(Reader(
                user=User(user_id=result['user']['id'], email=result['user']['email']),
                read_count=int(result['read'])))

        return readers

    @timer_with_counter
    @overrides
    def delete_owner(self, *, table_uri: str, owner: str) -> None:
        with self.query_executor() as executor:
            return self._delete_owner(table_uri=table_uri, owner=owner, executor=executor)

    def _delete_owner(self, *, table_uri: str, owner: str, executor: ExecuteQuery) -> None:
        """
        Delete the owner / owned_by relationship.

        :param table_uri:
        :param owner:
        :return:
        """
        _expire_link(executor=executor, g=self.g, edge_label=EdgeTypes.Owner,
                     key_property_name=self.key_property_name, vertex1_label=VertexTypes.Table,
                     vertex1_key=table_uri, vertex2_label=VertexTypes.User, vertex2_key=owner)

    @timer_with_counter
    @overrides
    def add_owner(self, *, table_uri: str, owner: str) -> None:
        """
        Update table owner informations.
        1. Do a create if not exists query of the owner(user) node.
        2. Do a upsert of the owner/owned_by relation.

        :param table_uri:
        :param user_id:
        :return:
        """
        with self.query_executor() as executor:
            return self._add_owner(table_uri=table_uri, owner=owner, executor=executor)

    def _add_owner(self, *, table_uri: str, owner: str, executor: ExecuteQuery) -> None:
        _link(executor=executor, g=self.g, edge_label=EdgeTypes.Owner, key_property_name=self.key_property_name,
              vertex1_label=VertexTypes.Table, vertex1_key=table_uri,
              vertex2_label=VertexTypes.User, vertex2_key=owner)

    @timer_with_counter
    @overrides
    def get_table_description(self, *, table_uri: str) -> Union[str, None]:
        """
        Get the table description based on table uri. Any exception will propagate back to api server.

        :param table_uri:
        :return:
        """

        g = _V(g=self.g, label=VertexTypes.Table, key=table_uri). \
            outE(EdgeTypes.Description.value.label).inV(). \
            has('description_source', 'description'). \
            values('description').fold()
        descriptions = self.query_executor()(query=g, get=FromResultSet.getOnly)
        return _safe_get(descriptions)

    @timer_with_counter
    @overrides
    def put_table_description(self, *, table_uri: str, description: str) -> None:
        """
        Update table description with one from user
        :param table_uri: Table uri
        :param description: new value for table description
        """
        with self.query_executor() as executor:
            return self._put_table_description(table_uri=table_uri, description=description, executor=executor)

    def _put_table_description(self, *, table_uri: str, description: str, executor: ExecuteQuery) -> None:
        description = unquote(description)

        # default table description is user added
        desc_key = make_description_uri(subject_uri=table_uri, source='description')

        _upsert(executor=executor, g=self.g, label=VertexTypes.Description, key=desc_key,
                key_property_name=self.key_property_name, description=description, description_source='description')
        _link(executor=executor, g=self.g, edge_label=EdgeTypes.Description, key_property_name=self.key_property_name,
              vertex1_label=VertexTypes.Table, vertex1_key=table_uri,
              vertex2_label=VertexTypes.Description, vertex2_key=desc_key)

    @timer_with_counter
    @overrides
    def add_tag(self, *,
                id: str,
                tag: str,
                tag_type: str = 'default',
                resource_type: ResourceType = ResourceType.Table) -> None:
        """
        Add new tag
        1. Create the node with type Tag if the node doesn't exist.
        2. Create the relation between tag and table if the relation doesn't exist.

        :param id:
        :param tag:
        :param tag_type:
        :param resource_type:
        :return: None
        """
        with self.query_executor() as executor:
            return self._add_tag(id=id, tag=tag, tag_type=tag_type,
                                 resource_type=resource_type, executor=executor)

    def _add_tag(self, *,
                 id: str,
                 tag: str,
                 tag_type: str = 'default',
                 resource_type: ResourceType = ResourceType.Table,
                 executor: ExecuteQuery) -> None:
        vertex_id: Any = _upsert(executor=executor, g=self.g, label=VertexTypes.Tag, key=tag,
                                 key_property_name=self.key_property_name, tag_type=tag_type)
        vertex_type: VertexTypes = self._get_vertex_type_from_resource_type(resource_type=resource_type)
        _link(executor=executor, g=self.g, edge_label=EdgeTypes.Tag, key_property_name=self.key_property_name,
              vertex1_id=vertex_id, vertex2_label=vertex_type, vertex2_key=id)

    def add_badge(self, *, id: str, badge_name: str, category: str = '',
                  resource_type: ResourceType) -> None:
        pass

    def delete_badge(self, *, id: str, badge_name: str, category: str,
                     resource_type: ResourceType) -> None:
        pass

    @timer_with_counter
    @overrides
    def delete_tag(self, *,
                   id: str,
                   tag: str,
                   tag_type: str = 'default',
                   resource_type: ResourceType = ResourceType.Table) -> None:
        """
        Deletes tag
        1. Delete the relation between resource and the tag
        2. todo(Tao): need to think about whether we should delete the tag if it is an orphan tag.
        :param id:
        :param tag:
        :param tag_type: {default-> normal tag, badge->non writable tag from UI}
        :param resource_type:
        :return:
        """
        with self.query_executor() as executor:
            return self._delete_tag(id=id, tag=tag, tag_type=tag_type,
                                    resource_type=resource_type, executor=executor)

    def _delete_tag(self, *,
                    id: str,
                    tag: str,
                    tag_type: str = 'default',
                    resource_type: ResourceType = ResourceType.Table,
                    executor: ExecuteQuery) -> None:
        LOGGER.info(f'Expire {tag} for {id}')
        vertex_type: VertexTypes = self._get_vertex_type_from_resource_type(resource_type=resource_type)
        _expire_link(executor=executor, g=self.g, edge_label=EdgeTypes.Tag,
                     key_property_name=self.key_property_name, vertex1_label=VertexTypes.Tag,
                     vertex1_key=tag, vertex2_label=vertex_type, vertex2_key=id)

    @timer_with_counter
    @overrides
    def put_column_description(self, *, table_uri: str, column_name: str, description: str) -> None:
        """
        Update column description with input from user
        :param table_uri:
        :param column_name:
        :param description:
        :return:
        """
        with self.query_executor() as executor:
            return self._put_column_description(
                table_uri=table_uri, column_name=column_name, description=description, executor=executor)

    def _put_column_description(
            self, *, table_uri: str, column_name: str, description: str, executor: ExecuteQuery) -> None:
        description = unquote(description)

        column_uri = make_column_uri(table_uri=table_uri, column_name=column_name)
        # default table description is user added
        desc_key = make_description_uri(subject_uri=column_uri, source='description')
        vertex_id: Any = _upsert(
            executor=executor, g=self.g,
            label=VertexTypes.Description, key=desc_key, key_property_name=self.key_property_name,
            description=description, description_source='description'
        )
        _link(executor=executor, g=self.g, edge_label=EdgeTypes.Description, key_property_name=self.key_property_name,
              vertex1_label=VertexTypes.Column, vertex1_key=column_uri, vertex2_id=vertex_id)

    @timer_with_counter
    @overrides
    def get_column_description(self, *, table_uri: str, column_name: str) -> Union[str, None]:
        """
        Get the column description based on table uri. Any exception will propagate back to api server.

        :param table_uri:
        :param column_name:
        :return:
        """
        column_uri = make_column_uri(table_uri=table_uri, column_name=column_name)
        g = _V(g=self.g, label=VertexTypes.Column, key=column_uri)
        g = g.outE(EdgeTypes.Description.value.label).inV()
        g = g.has(VertexTypes.Description.value.label, 'description_source', 'description').values('description')
        return self.query_executor()(query=g, get=FromResultSet.getOptional)

    @timer_with_counter
    @overrides
    def get_popular_tables(self, *,
                           num_entries: int = 10,
                           user_id: Optional[str] = None) -> List[PopularTable]:
        """
        Retrieve popular tables. As popular table computation requires full scan of table and user relationship,
        it will utilize cached method _get_popular_tables_uris.

        :param num_entries:
        :return: Iterable of PopularTable
        """

        table_uris = self._get_popular_tables_uris(num_entries)
        if not table_uris:
            return []

        g = _V(g=self.g, label=VertexTypes.Table, key=within(*table_uris), key_property_name=self.key_property_name)
        g = g.as_('table')
        g = g.inE(EdgeTypes.Table.value.label). \
            outV().hasLabel(VertexTypes.Schema.value.label).as_('schema')
        g = g.inE(EdgeTypes.Schema.value.label). \
            outV().hasLabel(VertexTypes.Cluster.value.label).as_('cluster')
        g = g.inE(EdgeTypes.Cluster.value.label). \
            outV().hasLabel(VertexTypes.Database.value.label).as_('database')
        g = g.coalesce(
            select('table').out(EdgeTypes.Description.value.label).hasLabel(VertexTypes.Description.value.label).fold()
        ).as_('description')
        g = g.select('database', 'cluster', 'schema', 'table', 'description'). \
            by('name').by('name').by('name').by('name').by(unfold().values('description').fold())
        results = self.query_executor()(query=g, get=FromResultSet.toList)

        if not results:
            return []

        popular_tables = []
        for result in results:
            popular_tables.append(PopularTable(
                database=result['database'], cluster=result['cluster'], schema=result['schema'], name=result['table'],
                description=_safe_get(result, 'description')
            ))
        return popular_tables

    def _get_popular_tables_uris(self, num_entries: int) -> List[str]:
        """
        Retrieve popular table uris. Will provide tables with top x popularity score.
        Popularity score = number of distinct readers * log(total number of reads)

        For score computation, it uses logarithm on total number of reads so that score won't be affected by small
        number of users reading a lot of times.
        :return: Iterable of table uri
        """

        g = _V(g=self.g, label=VertexTypes.User, key=None)
        g = g.outE(EdgeTypes.Read.value.label).as_('r')
        g = g.inV().hasLabel(VertexTypes.Table.value.label).values(self.key_property_name).as_('t')
        g = g.group().by(select('t')).by(coalesce(select('r').values('read_count'), constant(0)).sum())
        # the group then unfold is a little weird, it ends up being a list of singleton maps, but we get no more than
        # num_entries
        g = g.unfold().order().by(MapColumn.values, Order.decr).limit(num_entries)

        results_list = self.query_executor()(query=g, get=FromResultSet.toList)
        if not results_list:
            return []

        results = [key for result in results_list for key, count in result.items()]
        return results

    @timer_with_counter
    @overrides
    def get_latest_updated_ts(self) -> int:
        """
        API method to fetch last updated / index timestamp

        :return:
        """

        results = _V(g=self.g, label=VertexTypes.Updatedtimestamp,
                     key=AMUNDSEN_TIMESTAMP_KEY).values('latest_timestamp').toList()
        return _safe_get(results, transform=int)

    def get_statistics(self) -> Dict[str, Any]:
        # Not implemented
        pass

    @timer_with_counter
    @overrides
    def get_tags(self) -> List:
        """
        Get all existing tags from graph

        :return:
        """
        g = _V(g=self.g, label=VertexTypes.Tag, key=None).as_('tag'). \
            outE(EdgeTypes.Tag.value.label).inV().\
            hasLabel(VertexTypes.Table.value.label).as_('table').\
            group().by(select('tag').values(self.key_property_name)).by(select('table').dedup().count())
        counts = self.query_executor()(query=g, get=FromResultSet.getOnly)
        return [TagDetail(tag_name=name, tag_count=value) for name, value in counts.items()]

    def get_badges(self) -> List:
        pass

    # TODO: switch the base proxy to use user_id instead
    @timer_with_counter
    @overrides
    def get_table_by_user_relation(self, *, user_email: str, relation_type: UserResourceRel) -> Dict[str, Any]:
        """
        Retrieve all follow the resources per user based on the relation.
        We start with table resources only, then add dashboard.

        :param user_email: the id of the user
        :param relation_type: the relation between the user and the resource
        :return:
        """

        g = _V(g=self.g, label=VertexTypes.User, key=user_email).as_('user')
        if relation_type == UserResourceRel.follow:
            g = g.outE(EdgeTypes.Follow.value.label).inV()
        elif relation_type == UserResourceRel.own:
            g = g.inE(EdgeTypes.Owner.value.label).outV()
        elif relation_type == UserResourceRel.read:
            g = g.outE(EdgeTypes.Read.value.label).inV()
        else:
            raise NotImplementedError(f'The relation type {relation_type} is not defined!')

        # for some edge types (like READ), its possible for a user -> table to
        # have more than one that isn't expired (hence, the dedup)
        g = g.hasLabel(VertexTypes.Table.value.label).dedup().as_('table')
        g = g.coalesce(inE(EdgeTypes.Table.value.label).outV().
                       hasLabel(VertexTypes.Schema.value.label).fold()).as_('schema')
        g = g.coalesce(unfold().inE(EdgeTypes.Schema.value.label).outV().
                       hasLabel(VertexTypes.Cluster.value.label).fold()).as_('cluster')
        g = g.coalesce(unfold().inE(EdgeTypes.Cluster.value.label).outV().
                       hasLabel(VertexTypes.Database.value.label).fold()).as_('database')
        g = g.coalesce(select('table').outE(EdgeTypes.Description.value.label).
                       inV().has(VertexTypes.Description.value.label, 'source', 'user').fold()).as_('description')
        g = g.coalesce(select('table').outE(EdgeTypes.Description.value.label).
                       inV().has(VertexTypes.Description.value.label, 'source', without('user')).fold()). \
            as_('programmatic_descriptions')
        g = g.select('database', 'cluster', 'schema', 'table', 'description', 'programmatic_descriptions'). \
            by(unfold().values('name').fold()). \
            by(unfold().values('name').fold()). \
            by(unfold().values('name').fold()). \
            by('name'). \
            by(unfold().valueMap().fold()). \
            by(unfold().valueMap().fold())

        results = self.query_executor()(query=g, get=FromResultSet.toList)
        if not results:
            # raise NotFoundException(f'User {user_id} does not {relation_type} any resources')
            return {'table': []}

        popular_tables = []
        for r in results:
            popular_tables.append(PopularTable(
                database=_safe_get(r, 'database'), cluster=_safe_get(r, 'cluster'), schema=_safe_get(r, 'schema'),
                name=r.get('table'),
                description=_safe_get(r, 'description', 'description')))

        # this is weird but the convention
        return {'table': popular_tables}

    @timer_with_counter
    @overrides
    def get_dashboard_by_user_relation(self, *, user_email: str, relation_type: UserResourceRel) \
            -> Dict[str, List[DashboardSummary]]:
        pass

    # TODO: impl
    @timer_with_counter
    @overrides
    def get_frequently_used_tables(self, *, user_email: str) -> Dict[str, Any]:
        pass

    @timer_with_counter
    @overrides
    def add_resource_relation_by_user(self, *,
                                      id: str,
                                      user_id: str,
                                      relation_type: UserResourceRel,
                                      resource_type: ResourceType) -> None:

        vertex_type: VertexTypes = self._get_vertex_type_from_resource_type(resource_type=resource_type)
        edge_type: EdgeTypes = self._get_edge_type_from_user_resource_rel_type(relation=relation_type)

        with self.query_executor() as executor:
            _link(executor=executor, g=self.g, edge_label=edge_type, key_property_name=self.key_property_name,
                  vertex1_label=VertexTypes.User, vertex1_key=user_id,
                  vertex2_label=vertex_type, vertex2_key=id)

    @timer_with_counter
    @overrides
    def delete_resource_relation_by_user(self, *,
                                         id: str,
                                         user_id: str,
                                         relation_type: UserResourceRel,
                                         resource_type: ResourceType) -> None:

        vertex_type: VertexTypes = self._get_vertex_type_from_resource_type(resource_type=resource_type)
        edge_type: EdgeTypes = self._get_edge_type_from_user_resource_rel_type(relation=relation_type)

        with self.query_executor() as executor:
            _expire_link(executor=executor, g=self.g, edge_label=edge_type, key_property_name=self.key_property_name,
                         vertex1_label=VertexTypes.User, vertex1_key=user_id,
                         vertex2_label=vertex_type, vertex2_key=id)

    @timer_with_counter
    @overrides
    def get_dashboard(self,
                      dashboard_uri: str,
                      ) -> DashboardDetailEntity:
        pass

    @timer_with_counter
    @overrides
    def get_dashboard_description(self, *,
                                  id: str) -> Description:
        pass

    @timer_with_counter
    @overrides
    def put_dashboard_description(self, *,
                                  id: str,
                                  description: str) -> None:
        pass

    @timer_with_counter
    @overrides
    def get_resources_using_table(self, *,
                                  id: str,
                                  resource_type: ResourceType) -> Dict[str, List[DashboardSummary]]:
        pass

    def _get_user_table_relationship_clause(self, *, g: Traversal, relation_type: UserResourceRel,
                                            table_uri: str = None, user_key: str = None) -> GraphTraversal:
        """
        Returns the relationship traversal for get_table_by_user_relation et al.
        """

        # these are as if g will start with a User vertex, and end with a Table
        if relation_type == UserResourceRel.follow:
            def relation_matcher(g: Traversal) -> Traversal:
                return g.outE(EdgeTypes.Follow.value.label).inV()
        elif relation_type == UserResourceRel.own:
            def relation_matcher(g: Traversal) -> Traversal:
                return g.inE(EdgeTypes.Owner.value.label).outV()
        elif relation_type == UserResourceRel.read:
            def relation_matcher(g: Traversal) -> Traversal:
                return g.outE(EdgeTypes.Read.value.label).inV()
        else:
            raise NotImplementedError(f'The relation type {relation_type} is not defined!')

        table_matcher = self._get_user_table_relationship_clause_matcher(vertex_type=VertexTypes.Table, key=table_uri)
        user_matcher = self._get_user_table_relationship_clause_matcher(vertex_type=VertexTypes.User, key=user_key)
        return table_matcher(relation_matcher(user_matcher(g.V())))

    def _get_user_table_relationship_clause_matcher(self, *, vertex_type: VertexTypes, key: Optional[str]) -> \
            Callable[[Traversal], Traversal]:
        """
        Returns the relationship matcher for a Table or User get_table_by_user_relation et al.
        """

        if key is None:
            def matcher(_g: Traversal) -> Traversal:
                return _g
        elif not key:
            def matcher(_g: Traversal) -> Traversal:
                return _g.hasLabel(vertex_type.value.label)
        else:
            def matcher(_g: Traversal) -> Traversal:
                return _g.has(vertex_type.value.label, self.key_property_name, key)
        return matcher

    def _get_parent_table_from_column(self, *, column_vertex_id: str,
                                      executor: Optional[ExecuteQuery] = None) -> Dict[str, str]:
        """
        Returns the parent table key and id given a column vertex_id.

        Can be refactored in the future to return all table values, plus id with valueMap(True).
        However, this wasn't necessary at time of writing
        """
        g = self.g.V(column_vertex_id).inE().hasLabel(EdgeTypes.Column.value.label)
        g = g.outV().hasLabel(VertexTypes.Table.value.label).project('id', self.key_property_name)
        g = g.by(__.id()).by(self.key_property_name)
        if executor:
            return executor(query=g, get=FromResultSet.getOnly)
        else:
            return self.query_executor()(query=g, get=FromResultSet.getOnly)

    def _convert_to_application(self, result: Mapping[str, Any]) -> Application:
        return Application(
            application_url=_safe_get(result, 'application_url'),
            description=_safe_get(result, 'description'),
            name=_safe_get(result, 'name'),
            id=_safe_get(result, 'id', default='')
        )

    def _convert_to_description(self, result: Mapping[str, Any]) -> ProgrammaticDescription:
        return ProgrammaticDescription(text=_safe_get(result, 'description'),
                                       source=_safe_get(result, 'description_source'))

    def _convert_to_user(self, result: Mapping[str, Any]) -> User:
        return User(email=_safe_get(result, 'email'),
                    first_name=_safe_get(result, 'first_name'),
                    last_name=_safe_get(result, 'last_name'),
                    full_name=_safe_get(result, 'full_name'),
                    is_active=_safe_get(result, 'is_active'),
                    github_username=_safe_get(result, 'github_username'),
                    team_name=_safe_get(result, 'team_name'),
                    slack_id=_safe_get(result, 'slack_id'),
                    employee_type=_safe_get(result, 'employee_type'),
                    profile_url=_safe_get(result, 'profile_url'),
                    role_name=_safe_get(result, 'role_name'),
                    user_id=_safe_get(result, 'user_id'),
                    # filled in separately
                    manager_fullname=None)

    def _convert_to_source(self, result: Mapping[str, Any]) -> Source:
        return Source(source_type=_safe_get(result, 'source_type'), source=_safe_get(result, 'source'))

    def _convert_to_statistics(self, result: Mapping[str, Any]) -> Stat:
        return Stat(
            stat_type=_safe_get(result, 'stat_type'),
            stat_val=_safe_get(result, 'stat_val'),
            start_epoch=_safe_get(result, 'start_epoch'),
            end_epoch=_safe_get(result, 'end_epoch'))

    def _convert_to_tag(self, result: Mapping[str, Any]) -> Tag:
        return Tag(tag_name=_safe_get(result, self.key_property_name), tag_type=_safe_get(result, 'tag_type'))

    def _convert_to_watermark(self, result: Mapping[str, Any]) -> Watermark:
        return Watermark(
            watermark_type=_safe_get(result, self.key_property_name, transform=lambda x: x.split('/')[-2]),
            partition_key=_safe_get(result, 'partition_key'),
            partition_value=_safe_get(result, 'partition_value'),
            create_time=_safe_get(result, 'create_time'))

    def _get_vertex_type_from_resource_type(self, resource_type: ResourceType) -> VertexTypes:
        if resource_type == ResourceType.Table:
            return VertexTypes.Table
        elif resource_type == ResourceType.User:
            return VertexTypes.User

        raise NotImplementedError(f"Don't know how to handle ResourceType={resource_type}")

    def _get_edge_type_from_user_resource_rel_type(self, relation: UserResourceRel) -> EdgeTypes:
        if relation == UserResourceRel.read:
            return EdgeTypes.Read
        elif relation == UserResourceRel.own:
            return EdgeTypes.Owner
        elif relation == UserResourceRel.follow:
            return EdgeTypes.Follow

        raise NotImplementedError(f"Don't know how to handle UserResourceRel={relation}")

    def get_lineage(self, *,
                    id: str, resource_type: ResourceType, direction: str, depth: int) -> Lineage:
        pass

    def get_feature(self, *, feature_uri: str) -> Feature:
        pass

    def get_resource_description(self, *,
                                 resource_type: ResourceType,
                                 uri: str) -> Description:
        pass

    def put_resource_description(self, *,
                                 resource_type: ResourceType,
                                 uri: str,
                                 description: str) -> None:
        pass

    def add_resource_owner(self, *,
                           uri: str,
                           resource_type: ResourceType,
                           owner: str) -> None:
        pass

    def delete_resource_owner(self, *,
                              uri: str,
                              resource_type: ResourceType,
                              owner: str) -> None:
        pass

    def get_resource_generation_code(self, *,
                                     uri: str,
                                     resource_type: ResourceType) -> GenerationCode:
        pass

    def get_popular_resources(self, *,
                              num_entries: int,
                              resource_types: List[str],
                              user_id: Optional[str] = None) -> Dict[str, List]:
        raise NotImplementedError


class GenericGremlinProxy(AbstractGremlinProxy):
    """
    A generic Gremlin proxy
    :param host: a websockets URL
    :param port: None (put it in the URL passed in host)
    :param user: (as optional as your server allows) username
    :param password: (as optional as your server allows) password
    :param driver_remote_connection_options: passed to DriverRemoteConnection's constructor.
    """

    def __init__(self, *, host: str, port: Optional[int] = None, user: Optional[str] = None,
                 password: Optional[str] = None, traversal_source: 'str' = 'g', key_property_name: str = 'key',
                 driver_remote_connection_options: Mapping[str, Any] = {},
                 **kwargs: dict) -> None:
        driver_remote_connection_options = dict(driver_remote_connection_options)

        # as others, we repurpose host a url
        if not isinstance(host, str):
            raise AssertionError('expected a URL')
        self.url = host

        # port should be part of that url
        if port is not None:
            raise NotImplementedError(f'port is not allowed! port={port}')

        if user is not None:
            driver_remote_connection_options.update(username=user)
        if password is not None:
            driver_remote_connection_options.update(password=password)

        driver_remote_connection_options.update(traversal_source=traversal_source)

        super().__init__(key_property_name=key_property_name,
                         driver_remote_connection_options=driver_remote_connection_options)

    @classmethod
    @overrides
    def script_translator(cls) -> Type[ScriptTranslatorTargetJanusgraph]:
        # TODO: is there such a thing?
        return ScriptTranslatorTargetJanusgraph

    @overrides
    def possibly_signed_ws_client_request_or_url(self) -> str:
        return self.url

    def get_popular_resources(self, *,
                              num_entries: int,
                              resource_types: List[str],
                              user_id: Optional[str] = None) -> Dict[str, List]:
        raise NotImplementedError
