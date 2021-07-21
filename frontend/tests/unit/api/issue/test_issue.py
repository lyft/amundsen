# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import json
import unittest
from http import HTTPStatus
from amundsen_application import create_app
from amundsen_application.proxy.issue_tracker_clients.issue_exceptions import IssueConfigurationException
from amundsen_application.models.data_issue import DataIssue, Priority
from amundsen_application.models.issue_results import IssueResults

local_app = create_app('amundsen_application.config.TestConfig', 'tests/templates')


class IssueTest(unittest.TestCase):

    def setUp(self) -> None:
        local_app.config['ISSUE_TRACKER_URL'] = 'url'
        local_app.config['ISSUE_TRACKER_CLIENT_ENABLED'] = True
        self.mock_issue = {
            'issue_key': 'key',
            'title': 'some title',
            'url': 'http://somewhere',
            'priority_name': 'Major',
            'priority_display_name': 'P2'
        }
        self.mock_issues = {
            'issues': [self.mock_issue]
        }
        self.mock_data_issue = DataIssue(issue_key='key',
                                         title='title',
                                         url='http://somewhere',
                                             status='open',
                                             priority=Priority.P2)
        self.expected_issues = IssueResults(issues=[self.mock_data_issue],
                                            total=0,
                                            all_issues_url="http://moredata")

    # ----- Jira API Tests ---- #

    def test_get_issues_not_enabled(self) -> None:
        """
        Test request sends ACCEPTED if not enabled
        :return:
        """
        local_app.config['ISSUE_TRACKER_CLIENT_ENABLED'] = False
        with local_app.test_client() as test:
            response = test.get('/api/issue/issues', query_string=dict(key='table_key'))
            self.assertEqual(response.status_code, HTTPStatus.ACCEPTED)

    @unittest.mock.patch('amundsen_application.api.issue.issue.get_issue_tracker_client')
    def test_get_jira_issues_missing_config(self, mock_issue_tracker_client: unittest.mock.Mock) -> None:
        """
        Test request failure if config settings are missing
        :return:
        """
        local_app.config['ISSUE_TRACKER_URL'] = None
        mock_issue_tracker_client.return_value.get_issues.side_effect = IssueConfigurationException
        with local_app.test_client() as test:
            response = test.get('/api/issue/issues', query_string=dict(key='table_key'))
            self.assertEqual(response.status_code, HTTPStatus.NOT_IMPLEMENTED)

    def test_get_jira_issues_no_key(self) -> None:
        """
        Test request failure if table key is missing
        :return:
        """
        with local_app.test_client() as test:
            response = test.get('/api/issue/issues', query_string=dict(some_key='value'))
            self.assertEqual(response.status_code, HTTPStatus.INTERNAL_SERVER_ERROR)

    @unittest.mock.patch('amundsen_application.api.issue.issue.get_issue_tracker_client')
    def test_get_jira_issues_success(self, mock_issue_tracker_client: unittest.mock.Mock) -> None:
        """
        Tests successful get request
        :return:
        """
        mock_issue_tracker_client.return_value.get_issues.return_value = self.expected_issues

        with local_app.test_client() as test:
            response = test.get('/api/issue/issues', query_string=dict(key='table_key'))
            data = json.loads(response.data)
            self.assertEqual(response.status_code, HTTPStatus.OK)
            self.assertEqual(data['issues']['issues'][0]['issue_key'],
                             self.expected_issues.issues[0].issue_key)
            self.assertEqual(data['issues']['total'],
                             self.expected_issues.total)
            self.assertEqual(data['issues']['all_issues_url'],
                             self.expected_issues.all_issues_url)
            mock_issue_tracker_client.return_value.get_issues.assert_called_with('table_key')

    def test_create_issue_not_enabled(self) -> None:
        """
        Test request sends ACCEPTED if not enabled
        :return:
        """
        local_app.config['ISSUE_TRACKER_CLIENT_ENABLED'] = False
        with local_app.test_client() as test:
            response = test.post('/api/issue/issue', data={
                'description': 'test description',
                'title': 'test title',
                'key': 'key'
            })
            self.assertEqual(response.status_code, HTTPStatus.ACCEPTED)

    @unittest.mock.patch('amundsen_application.api.issue.issue.get_issue_tracker_client')
    def test_create_jira_issue_missing_config(self, mock_issue_tracker_client: unittest.mock.Mock) -> None:
        """
        Test request failure if config settings are missing
        :return:
        """
        mock_issue_tracker_client.side_effect = IssueConfigurationException
        local_app.config['ISSUE_TRACKER_URL'] = None
        with local_app.test_client() as test:
            response = test.post('/api/issue/issue', data={
                'description': 'test description',
                'title': 'test title',
                'key': 'key'
            })
            self.assertEqual(response.status_code, HTTPStatus.NOT_IMPLEMENTED)

    def test_create_jira_issue_no_description(self) -> None:
        """
         Test request failure if table key is missing
         :return:
         """
        with local_app.test_client() as test:
            response = test.post('/api/issue/issue', data={
                'key': 'table_key',
                'title': 'test title',
            })
            self.assertEqual(response.status_code, HTTPStatus.INTERNAL_SERVER_ERROR)

    def test_create_jira_issue_no_key(self) -> None:
        """
         Test request failure if table key is missing
         :return:
         """
        with local_app.test_client() as test:
            response = test.post('/api/issue/issue', data={
                'description': 'test description',
                'title': 'test title'
            })
            self.assertEqual(response.status_code, HTTPStatus.INTERNAL_SERVER_ERROR)

    def test_create_jira_issue_no_title(self) -> None:
        """
         Test request failure if table key is missing
         :return:
         """
        with local_app.test_client() as test:
            response = test.post('/api/issue/issue', data={
                'description': 'test description',
                'key': 'table_key',
            })
            self.assertEqual(response.status_code, HTTPStatus.INTERNAL_SERVER_ERROR)

    @unittest.mock.patch('amundsen_application.api.issue.issue.get_issue_tracker_client')
    def test_create_jira_issue_success(self, mock_issue_tracker_client: unittest.mock.Mock) -> None:
        """
        Test request returns success and expected outcome
        :return:
        """
        mock_issue_tracker_client.return_value.create_issue.return_value = self.mock_data_issue

        with local_app.test_client() as test:
            response = test.post('/api/issue/issue',
                                 content_type='multipart/form-data',
                                 data={
                                     'description': 'test description',
                                     'title': 'title',
                                     'key': 'key'
                                 })
            data = json.loads(response.data)
            self.assertEqual(response.status_code, HTTPStatus.OK)
            mock_issue_tracker_client.assert_called
            mock_issue_tracker_client.return_value.create_issue.assert_called
            self.assertEqual(data['issue'].get('title'), 'title')
            self.assertEqual(data['issue'].get('issue_key'), 'key')
