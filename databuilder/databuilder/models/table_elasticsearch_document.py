# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from typing import List, Optional

from databuilder.models.elasticsearch_document import ElasticsearchDocument


class TableESDocument(ElasticsearchDocument):
    """
    Schema for the Search index document
    """

    def __init__(self,
                 database: str,
                 cluster: str,
                 schema: str,
                 name: str,
                 key: str,
                 description: str,
                 last_updated_timestamp: Optional[int],
                 column_names: List[str],
                 column_descriptions: List[str],
                 total_usage: int,
                 unique_usage: int,
                 tags: List[str],
                 badges: Optional[List[str]] = None,
                 display_name: Optional[str] = None,
                 schema_description: Optional[str] = None,
                 programmatic_descriptions: List[str] = [],
                 ) -> None:
        self.database = database
        self.cluster = cluster
        self.schema = schema
        self.name = name
        self.display_name = display_name if display_name else f'{schema}.{name}'
        self.key = key
        self.description = description
        # todo: use last_updated_timestamp to match the record in metadata
        self.last_updated_timestamp = int(last_updated_timestamp) if last_updated_timestamp else None
        self.column_names = column_names
        self.column_descriptions = column_descriptions
        self.total_usage = total_usage
        self.unique_usage = unique_usage
        # todo: will include tag_type once we have better understanding from UI flow.
        self.tags = tags
        self.badges = badges
        self.schema_description = schema_description
        self.programmatic_descriptions = programmatic_descriptions
