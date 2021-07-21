# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import unittest
from typing import Iterable, Union

from databuilder.models.graph_node import GraphNode
from databuilder.models.graph_relationship import GraphRelationship
from databuilder.models.graph_serializable import GraphSerializable
from databuilder.serializers import neo4_serializer


class TestSerialize(unittest.TestCase):

    def test_serialize(self) -> None:
        actors = [Actor('Tom Cruise'), Actor('Meg Ryan')]
        cities = [City('San Diego'), City('Oakland')]
        movie = Movie('Top Gun', actors, cities)

        actual = []
        node_row = movie.next_node()
        while node_row:
            actual.append(neo4_serializer.serialize_node(node_row))
            node_row = movie.next_node()

        expected = [
            {'name': 'Top Gun', 'KEY': 'movie://Top Gun', 'LABEL': 'Movie'},
            {'name': 'Top Gun', 'KEY': 'actor://Tom Cruise', 'LABEL': 'Actor'},
            {'name': 'Top Gun', 'KEY': 'actor://Meg Ryan', 'LABEL': 'Actor'},
            {'name': 'Top Gun', 'KEY': 'city://San Diego', 'LABEL': 'City'},
            {'name': 'Top Gun', 'KEY': 'city://Oakland', 'LABEL': 'City'}
        ]
        self.assertEqual(expected, actual)

        actual = []
        relation_row = movie.next_relation()
        while relation_row:
            actual.append(neo4_serializer.serialize_relationship(relation_row))
            relation_row = movie.next_relation()

        expected = [
            {'END_KEY': 'actor://Tom Cruise', 'START_LABEL': 'Movie',
             'END_LABEL': 'Actor', 'START_KEY': 'movie://Top Gun',
             'TYPE': 'ACTOR', 'REVERSE_TYPE': 'ACTED_IN'},
            {'END_KEY': 'actor://Meg Ryan', 'START_LABEL': 'Movie',
             'END_LABEL': 'Actor', 'START_KEY': 'movie://Top Gun',
             'TYPE': 'ACTOR', 'REVERSE_TYPE': 'ACTED_IN'},
            {'END_KEY': 'city://San Diego', 'START_LABEL': 'Movie',
             'END_LABEL': 'City', 'START_KEY': 'movie://Top Gun',
             'TYPE': 'FILMED_AT', 'REVERSE_TYPE': 'APPEARS_IN'},
            {'END_KEY': 'city://Oakland', 'START_LABEL': 'Movie',
             'END_LABEL': 'City', 'START_KEY': 'movie://Top Gun',
             'TYPE': 'FILMED_AT', 'REVERSE_TYPE': 'APPEARS_IN'}
        ]
        self.assertEqual(expected, actual)


class Actor(object):
    LABEL = 'Actor'
    KEY_FORMAT = 'actor://{}'

    def __init__(self, name: str) -> None:
        self.name = name


class City(object):
    LABEL = 'City'
    KEY_FORMAT = 'city://{}'

    def __init__(self, name: str) -> None:
        self.name = name


class Movie(GraphSerializable):
    LABEL = 'Movie'
    KEY_FORMAT = 'movie://{}'
    MOVIE_ACTOR_RELATION_TYPE = 'ACTOR'
    ACTOR_MOVIE_RELATION_TYPE = 'ACTED_IN'
    MOVIE_CITY_RELATION_TYPE = 'FILMED_AT'
    CITY_MOVIE_RELATION_TYPE = 'APPEARS_IN'

    def __init__(self,
                 name: str,
                 actors: Iterable[Actor],
                 cities: Iterable[City]) -> None:
        self._name = name
        self._actors = actors
        self._cities = cities
        self._node_iter = iter(self.create_nodes())
        self._relation_iter = iter(self.create_relation())

    def create_next_node(self) -> Union[GraphNode, None]:
        try:
            return next(self._node_iter)
        except StopIteration:
            return None

    def create_next_relation(self) -> Union[GraphRelationship, None]:
        try:
            return next(self._relation_iter)
        except StopIteration:
            return None

    def create_nodes(self) -> Iterable[GraphNode]:
        result = [GraphNode(
            key=Movie.KEY_FORMAT.format(self._name),
            label=Movie.LABEL,
            attributes={
                'name': self._name
            }
        )]

        for actor in self._actors:
            actor_node = GraphNode(
                key=Actor.KEY_FORMAT.format(actor.name),
                label=Actor.LABEL,
                attributes={
                    'name': self._name
                }
            )
            result.append(actor_node)

        for city in self._cities:
            city_node = GraphNode(
                key=City.KEY_FORMAT.format(city.name),
                label=City.LABEL,
                attributes={
                    'name': self._name
                }
            )
            result.append(city_node)
        return result

    def create_relation(self) -> Iterable[GraphRelationship]:
        result = []
        for actor in self._actors:
            movie_actor_relation = GraphRelationship(
                start_key=Movie.KEY_FORMAT.format(self._name),
                end_key=Actor.KEY_FORMAT.format(actor.name),
                start_label=Movie.LABEL,
                end_label=Actor.LABEL,
                type=Movie.MOVIE_ACTOR_RELATION_TYPE,
                reverse_type=Movie.ACTOR_MOVIE_RELATION_TYPE,
                attributes={}
            )
            result.append(movie_actor_relation)

        for city in self._cities:
            city_movie_relation = GraphRelationship(
                start_key=Movie.KEY_FORMAT.format(self._name),
                end_key=City.KEY_FORMAT.format(city.name),
                start_label=Movie.LABEL,
                end_label=City.LABEL,
                type=Movie.MOVIE_CITY_RELATION_TYPE,
                reverse_type=Movie.CITY_MOVIE_RELATION_TYPE,
                attributes={}
            )
            result.append(city_movie_relation)
        return result


if __name__ == '__main__':
    unittest.main()
