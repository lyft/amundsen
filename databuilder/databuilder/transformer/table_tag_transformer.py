# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from typing import Any

from pyhocon import ConfigFactory, ConfigTree

from databuilder.models.table_metadata import TableMetadata
from databuilder.transformer.base_transformer import Transformer


class TableTagTransformer(Transformer):
    """Simple transformer that adds tags to all table nodes produced as part of a job."""
    # Config
    TAGS = 'tags'
    DEFAULT_CONFIG = ConfigFactory.from_dict({TAGS: None})

    def init(self, conf: ConfigTree) -> None:
        conf = conf.with_fallback(TableTagTransformer.DEFAULT_CONFIG)
        tags = conf.get_string(TableTagTransformer.TAGS)

        self.tags = TableMetadata.format_tags(tags)

    def transform(self, record: Any) -> Any:
        if isinstance(record, TableMetadata):
            if record.tags:
                record.tags += self.tags
            else:
                record.tags = self.tags
        return record

    def get_scope(self) -> str:
        return 'transformer.table_tag'
