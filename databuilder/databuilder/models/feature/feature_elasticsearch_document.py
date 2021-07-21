# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from typing import List, Optional

from databuilder.models.elasticsearch_document import ElasticsearchDocument


class FeatureESDocument(ElasticsearchDocument):
    """
    Schema for the Feature ES document
    """

    def __init__(self,
                 feature_group: str,
                 feature_name: str,
                 version: str,
                 key: str,
                 total_usage: int,
                 status: Optional[str] = None,
                 entity: Optional[str] = None,
                 description: Optional[str] = None,
                 availability: Optional[List[str]] = None,
                 badges: Optional[List[str]] = None,
                 tags: Optional[List[str]] = None,
                 last_updated_timestamp: Optional[int] = None,
                 ) -> None:
        self.feature_group = feature_group
        self.feature_name = feature_name
        self.version = version
        self.key = key
        self.total_usage = total_usage
        self.status = status
        self.entity = entity
        self.description = description
        self.availability = availability
        self.badges = badges
        self.tags = tags
        self.last_updated_timestamp = last_updated_timestamp
