# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from typing import Any, List


class SearchResult:
    def __init__(self, *,
                 total_results: int,
                 results: List[Any]) -> None:
        self.total_results = total_results
        self.results = results

    def __repr__(self) -> str:
        return 'SearchResult(total_results={!r}, results{!r})'.format(self.total_results, self.results)
