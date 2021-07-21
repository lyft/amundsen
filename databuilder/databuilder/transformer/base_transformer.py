# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import abc
from typing import (
    Any, Iterable, Iterator, List, Optional,
)

from pyhocon import ConfigTree

from databuilder import Scoped


class Transformer(Scoped):
    """
    A transformer transforms a record
    """
    @abc.abstractmethod
    def init(self, conf: ConfigTree) -> None:
        pass

    @abc.abstractmethod
    def transform(self, record: Any) -> Any:
        pass


class NoopTransformer(Transformer):
    """
    A no-op transformer
    """

    def init(self, conf: ConfigTree) -> None:
        pass

    def transform(self, record: Any) -> Any:
        return record

    def get_scope(self) -> str:
        pass


class ChainedTransformer(Transformer):
    """
    A chained transformer that iterates transformers and transforms a record.
    Transfomers implemented using generator functons can yield multiple records,
    which all get passed to the next transformer.
    Returning None from a transformer filters the record out.
    """

    def __init__(self,
                 transformers: Iterable[Transformer],
                 is_init_transformers: Optional[bool] = False) -> None:
        self.transformers = transformers
        self.is_init_transformers = is_init_transformers

    def init(self, conf: ConfigTree) -> None:
        if self.is_init_transformers:
            for transformer in self.transformers:
                transformer.init(Scoped.get_scoped_conf(conf, transformer.get_scope()))

    def transform(self, record: Any) -> Any:
        records = [record]
        for t in self.transformers:
            new_records: List[Any] = []
            for r in records:
                result = t.transform(r)
                # Get all records if the transformer returns an Iterator.
                if isinstance(result, Iterator):
                    new_records += list(result)

                # Filter the record if it is None
                elif result is not None:
                    new_records.append(result)
            records = new_records

        yield from records

    def get_scope(self) -> str:
        return 'transformer.chained'

    def close(self) -> None:
        for t in self.transformers:
            t.close()
