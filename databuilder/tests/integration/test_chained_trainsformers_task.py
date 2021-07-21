# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import unittest
from typing import (
    Any, Iterable, List, Optional,
)

from pyhocon import ConfigFactory, ConfigTree

from databuilder.extractor.base_extractor import Extractor
from databuilder.job.job import DefaultJob
from databuilder.loader.base_loader import Loader
from databuilder.models.table_metadata import TableMetadata
from databuilder.models.table_owner import TableOwner
from databuilder.task.task import DefaultTask
from databuilder.transformer.base_transformer import (
    ChainedTransformer, NoopTransformer, Transformer,
)

TEST_DATA = [
    TableMetadata(
        database="db1", schema="schema1", name="table1", cluster="prod", description=""
    ),
    TableMetadata(
        database="db2", schema="schema2", name="table2", cluster="prod", description=""
    ),
]

EXPECTED_OWNERS = [
    TableOwner(
        db_name="db1",
        cluster="prod",
        schema="schema1",
        table_name="table1",
        owners=["foo", "bar"],
    ),
    TableOwner(
        db_name="db2",
        cluster="prod",
        schema="schema2",
        table_name="table2",
        owners=["foo", "bar"],
    ),
]


class TestChainedTransformerTask(unittest.TestCase):
    def test_multi_yield_task(self) -> None:
        """ Test that MultiYieldTask is able to unpack a transformer which yields multiple nodes """

        result = _run_transformer(AddFakeOwnerTransformer())

        expected = [TEST_DATA[0], EXPECTED_OWNERS[0], TEST_DATA[1], EXPECTED_OWNERS[1]]

        self.assertEqual(repr(result), repr(expected))

    def test_multi_yield_chained_transformer(self) -> None:
        """
        Test that MultiYieldChainedTransformer is able handle both:
            - transformers which yield multiple nodes
            - transformers which transform single nodes
        """

        transformer = ChainedTransformer(
            [AddFakeOwnerTransformer(), NoopTransformer(), DuplicateTransformer()]
        )

        result = _run_transformer(transformer)

        expected = [
            TEST_DATA[0],
            TEST_DATA[0],
            EXPECTED_OWNERS[0],
            EXPECTED_OWNERS[0],
            TEST_DATA[1],
            TEST_DATA[1],
            EXPECTED_OWNERS[1],
            EXPECTED_OWNERS[1],
        ]

        self.assertEqual(repr(result), repr(expected))


class AddFakeOwnerTransformer(Transformer):
    """ A transformer which yields the input record, and also a TableOwner """

    def init(self, conf: ConfigTree) -> None:
        pass

    def get_scope(self) -> str:
        return "transformer.fake_owner"

    def transform(self, record: Any) -> Iterable[Any]:
        yield record
        if isinstance(record, TableMetadata):
            yield TableOwner(
                db_name=record.database,
                schema=record.schema,
                table_name=record.name,
                cluster=record.cluster,
                owners=["foo", "bar"],
            )


class DuplicateTransformer(Transformer):
    """ A transformer which yields the input record twice"""

    def init(self, conf: ConfigTree) -> None:
        pass

    def get_scope(self) -> str:
        return "transformer.duplicate"

    def transform(self, record: Any) -> Iterable[Any]:
        yield record
        yield record


class ListExtractor(Extractor):
    """ An extractor which yields a list of records """

    def init(self, conf: ConfigTree) -> None:
        self.items = conf.get("items")

    def extract(self) -> Optional[Any]:
        try:
            return self.items.pop(0)
        except IndexError:
            return None

    def get_scope(self) -> str:
        return "extractor.test"


class ListLoader(Loader):
    """ A loader which appends all records to a list """

    def init(self, conf: ConfigTree) -> None:
        self.loaded: List[Any] = []

    def load(self, record: Any) -> None:
        self.loaded.append(record)


def _run_transformer(transformer: Transformer) -> List[Any]:
    job_config = ConfigFactory.from_dict({"extractor.test.items": TEST_DATA})

    loader = ListLoader()
    task = DefaultTask(
        extractor=ListExtractor(), transformer=transformer, loader=loader
    )
    job = DefaultJob(conf=job_config, task=task)

    job.launch()
    return loader.loaded
