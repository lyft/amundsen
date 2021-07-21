# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from typing import (
    List, Optional, Union,
)

from databuilder.models.elasticsearch_document import ElasticsearchDocument


class DashboardESDocument(ElasticsearchDocument):
    """
    Schema for the ES dashboard ES document
    """

    def __init__(self,
                 group_name: str,
                 name: str,
                 description: Union[str, None],
                 total_usage: int,
                 product: Optional[str] = '',
                 cluster: Optional[str] = '',
                 group_description: Optional[str] = None,
                 query_names: Union[List[str], None] = None,
                 chart_names: Optional[List[str]] = None,
                 group_url: Optional[str] = None,
                 url: Optional[str] = None,
                 uri: Optional[str] = None,
                 last_successful_run_timestamp: Optional[int] = None,
                 tags: Optional[List[str]] = None,
                 badges: Optional[List[str]] = None,
                 ) -> None:
        self.group_name = group_name
        self.name = name
        self.description = description
        self.cluster = cluster
        self.product = product
        self.group_url = group_url
        self.url = url
        self.uri = uri
        self.last_successful_run_timestamp = last_successful_run_timestamp
        self.total_usage = total_usage
        self.group_description = group_description
        self.query_names = query_names
        self.chart_names = chart_names
        self.tags = tags
        self.badges = badges
