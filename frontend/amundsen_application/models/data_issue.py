# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from enum import Enum
from typing import Optional


class Priority(Enum):
    P0 = ('P0', 'Blocker')
    P1 = ('P1', 'Critical')
    P2 = ('P2', 'Major')
    P3 = ('P3', 'Minor')

    def __init__(self, level: str, jira_severity: str):
        self.level = level
        self.jira_severity = jira_severity

    # JIRA SDK does not return priority beyond the name
    @staticmethod
    def from_jira_severity(jira_severity: str) -> 'Optional[Priority]':
        jira_severity_to_priority = {
            p.jira_severity: p for p in Priority
        }

        return jira_severity_to_priority.get(jira_severity)

    @staticmethod
    def from_level(level: str) -> 'Optional[Priority]':
        level_to_priority = {
            p.level: p for p in Priority
        }

        return level_to_priority.get(level)


class DataIssue:
    def __init__(self,
                 issue_key: str,
                 title: str,
                 url: str,
                 status: str,
                 priority: Optional[Priority]) -> None:
        self.issue_key = issue_key
        self.title = title
        self.url = url
        self.status = status
        self.priority = priority

    def serialize(self) -> dict:
        return {'issue_key': self.issue_key,
                'title': self.title,
                'url': self.url,
                'status': self.status,
                'priority_name': self.priority.jira_severity.lower() if self.priority else None,
                'priority_display_name': self.priority.level if self.priority else None}
