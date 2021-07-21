# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import unittest
from amundsen_application.models.data_issue import DataIssue, Priority


class DataIssueTest(unittest.TestCase):

    def setUp(self) -> None:
        self.issue_key = 'key'
        self.title = 'title'
        self.url = 'https://place'
        self.status = 'open'
        self.priority = Priority.P2
        self.maxDiff = None

    def test_mapping_priority(self) -> None:
        expected_priority_name = 'major'
        expected_priority_display_name = 'P2'
        data_issue = DataIssue(issue_key=self.issue_key,
                               title=self.title,
                               url=self.url,
                               status=self.status,
                               priority=self.priority).serialize()
        self.assertEqual(data_issue['priority_display_name'], expected_priority_display_name)
        self.assertEqual(data_issue['priority_name'], expected_priority_name)
        self.assertEqual(data_issue['issue_key'], self.issue_key)
        self.assertEqual(data_issue['title'], self.title)
        self.assertEqual(data_issue['url'], self.url)
        self.assertEqual(data_issue['status'], self.status)

    def test_mapping_priorty_missing(self) -> None:
        expected_priority_name = None  # type: ignore
        expected_priority_display_name = None  # type: ignore
        data_issue = DataIssue(issue_key=self.issue_key,
                               title=self.title,
                               url=self.url,
                               status=self.status,
                               priority=None).serialize()
        self.assertEqual(data_issue['priority_display_name'], expected_priority_display_name)
        self.assertEqual(data_issue['priority_name'], expected_priority_name)
        self.assertEqual(data_issue['issue_key'], self.issue_key)
        self.assertEqual(data_issue['title'], self.title)
        self.assertEqual(data_issue['url'], self.url)
        self.assertEqual(data_issue['status'], self.status)
