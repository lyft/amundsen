# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import unittest
from typing import (
    Iterable, Iterator, Union,
)

from amundsen_rds.models import RDSModel
from sqlalchemy import (
    BigInteger, Column, ForeignKey, String,
)
from sqlalchemy.ext.declarative import declarative_base

from databuilder.models.table_serializable import TableSerializable
from databuilder.serializers import mysql_serializer

Base = declarative_base()


class TestTableSerializable(unittest.TestCase):

    def test_table_serializable(self) -> None:
        actors = [Actor('Tom Cruise'), Actor('Meg Ryan')]
        movie = Movie('Top Gun', actors)

        actual = []
        node_row = movie.next_record()
        while node_row:
            actual.append(mysql_serializer.serialize_record(node_row))
            node_row = movie.next_record()

        expected = [
            {
                'rk': 'movie://Top Gun',
                'name': 'Top Gun'
            },
            {
                'rk': 'actor://Tom Cruise',
                'name': 'Tom Cruise'
            },
            {
                'movie_rk': 'movie://Top Gun',
                'actor_rk': 'actor://Tom Cruise'
            },
            {
                'rk': 'actor://Meg Ryan',
                'name': 'Meg Ryan'
            },
            {
                'movie_rk': 'movie://Top Gun',
                'actor_rk': 'actor://Meg Ryan'
            }
        ]

        self.assertEqual(expected, actual)


class RDSMovie(Base):  # type: ignore
    __tablename__ = 'movie'

    rk = Column(String(128), primary_key=True)
    name = Column(String(128))
    published_tag = Column(String(128), nullable=False)
    publisher_last_updated_epoch_ms = Column(BigInteger, nullable=False)


class RDSActor(Base):  # type: ignore
    __tablename__ = 'actor'

    rk = Column(String(128), primary_key=True)
    name = Column(String(128))
    published_tag = Column(String(128), nullable=False)
    publisher_last_updated_epoch_ms = Column(BigInteger, nullable=False)


class RDSMovieActor(Base):  # type: ignore
    __tablename__ = 'movie_actor'

    movie_rk = Column(String(128), ForeignKey('movie.rk'), primary_key=True)
    actor_rk = Column(String(128), ForeignKey('actor.rk'), primary_key=True)
    published_tag = Column(String(128), nullable=False)
    publisher_last_updated_epoch_ms = Column(BigInteger, nullable=False)


class Actor(object):
    KEY_FORMAT = 'actor://{}'

    def __init__(self, name: str) -> None:
        self.name = name


class Movie(TableSerializable):
    KEY_FORMAT = 'movie://{}'

    def __init__(self,
                 name: str,
                 actors: Iterable[Actor]) -> None:
        self._name = name
        self._actors = actors
        self._record_iter = self._create_record_iterator()

    def create_next_record(self) -> Union[RDSModel, None]:
        try:
            return next(self._record_iter)
        except StopIteration:
            return None

    def _create_record_iterator(self) -> Iterator[RDSModel]:
        movie_record = RDSMovie(
            rk=Movie.KEY_FORMAT.format(self._name),
            name=self._name
        )
        yield movie_record

        for actor in self._actors:
            actor_record = RDSActor(
                rk=Actor.KEY_FORMAT.format(actor.name),
                name=actor.name
            )
            yield actor_record

            movie_actor_record = RDSMovieActor(
                movie_rk=Movie.KEY_FORMAT.format(self._name),
                actor_rk=Actor.KEY_FORMAT.format(actor.name)
            )
            yield movie_actor_record


if __name__ == '__main__':
    unittest.main()
