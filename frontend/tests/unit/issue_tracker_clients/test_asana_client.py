# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from unittest.mock import Mock

import flask
import unittest
from amundsen_application.proxy.issue_tracker_clients.issue_exceptions import IssueConfigurationException
from amundsen_application.proxy.issue_tracker_clients.asana_client import AsanaClient
from amundsen_application.models.data_issue import DataIssue, Priority

app = flask.Flask(__name__)
app.config.from_object('amundsen_application.config.TestConfig')


class AsanaClientTest(unittest.TestCase):

    def setUp(self) -> None:
        self.mock_issue_instance = DataIssue(issue_key='key',
                                             title='some title',
                                             url='http://somewhere',
                                             status='open',
                                             priority=Priority.P2)

    @unittest.mock.patch('amundsen_application.proxy.issue_tracker_clients.asana_client.asana.Client')
    def test_create_AsanaClient_validates_config(self, mock_asana_client: Mock) -> None:
        with app.test_request_context():
            try:
                AsanaClient(
                    issue_labels=[],
                    issue_tracker_url='',
                    issue_tracker_user='',
                    issue_tracker_password='',
                    issue_tracker_project_id=-1,
                    issue_tracker_max_results=-1)

            except IssueConfigurationException as e:
                self.assertTrue(type(e), type(IssueConfigurationException))
                self.assertTrue(e, 'The following config settings must be set for Asana: '
                                   'ISSUE_TRACKER_URL, ISSUE_TRACKER_USER, ISSUE_TRACKER_PASSWORD, '
                                   'ISSUE_TRACKER_PROJECT_ID')
