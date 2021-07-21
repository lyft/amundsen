# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import unittest
import flask

from amundsen_application.base.base_issue_tracker_client import BaseIssueTrackerClient


app = flask.Flask(__name__)
app.config.from_object('amundsen_application.config.TestConfig')


class IssueTrackerClientTest(unittest.TestCase):

    def test_abstract_class_methods(self) -> None:
        abstract_methods_set = {
            '__init__',
            'create_issue',
            'get_issues'
        }
        # Use getattr to prevent mypy warning
        cls_abstrct_methods = getattr(BaseIssueTrackerClient, '__abstractmethods__')
        self.assertEquals(cls_abstrct_methods, abstract_methods_set)
