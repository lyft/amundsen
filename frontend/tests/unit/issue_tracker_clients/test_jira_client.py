# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from unittest.mock import Mock

import flask
import unittest
from amundsen_application.proxy.issue_tracker_clients.issue_exceptions import IssueConfigurationException
from amundsen_application.proxy.issue_tracker_clients.jira_client import JiraClient, SEARCH_STUB_ALL_ISSUES
from amundsen_application.models.data_issue import DataIssue, Priority
from jira import JIRAError
from typing import Dict, List

app = flask.Flask(__name__)
app.config.from_object('amundsen_application.config.TestConfig')


class MockJiraResultList(list):
    def __init__(self, iterable: Dict[str, str], _total: int) -> None:
        if iterable is not None:
            list.__init__(self, iterable)
        else:
            list.__init__(self)
        self.total = _total


class JiraClientTest(unittest.TestCase):

    def setUp(self) -> None:
        self.mock_issue = {
            'issue_key': 'key',
            'title': 'some title',
            'url': 'http://somewhere',
            'status': 'open',
            'priority_name': 'Major',
            'priority_display_name': 'P2'
        }
        result_list = MockJiraResultList(iterable=self.mock_issue, _total=0)
        self.mock_jira_issues = result_list
        self.mock_issue_instance = DataIssue(issue_key='key',
                                             title='some title',
                                             url='http://somewhere',
                                             status='open',
                                             priority=Priority.P2)

    @unittest.mock.patch('amundsen_application.proxy.issue_tracker_clients.jira_client.JIRA')
    def test_create_JiraClient_validates_config(self, mock_JIRA_client: Mock) -> None:
        with app.test_request_context():
            try:

                JiraClient(issue_labels=[],
                           issue_tracker_url='',
                           issue_tracker_user='',
                           issue_tracker_password='',
                           issue_tracker_project_id=-1,
                           issue_tracker_max_results=-1)
            except IssueConfigurationException as e:
                self.assertTrue(type(e), type(IssueConfigurationException))
                self.assertTrue(e, 'The following config settings must be set for Jira: '
                                   'ISSUE_TRACKER_URL, ISSUE_TRACKER_USER, ISSUE_TRACKER_PASSWORD, '
                                   'ISSUE_TRACKER_PROJECT_ID')

    @unittest.mock.patch('amundsen_application.proxy.issue_tracker_clients.jira_client.JIRA')
    @unittest.mock.patch('amundsen_application.proxy.issue_tracker_clients.jira_client.'
                         'JiraClient._generate_all_issues_url')
    def test_get_issues_returns_JIRAError(self, mock_remaining_issues: Mock, mock_JIRA_client: Mock) -> None:
        mock_JIRA_client.return_value.get_issues.side_effect = JIRAError('Some exception')
        mock_remaining_issues.return_value = 0
        with app.test_request_context():
            try:
                jira_client = JiraClient(issue_labels=[],
                                         issue_tracker_url=app.config['ISSUE_TRACKER_URL'],
                                         issue_tracker_user=app.config['ISSUE_TRACKER_USER'],
                                         issue_tracker_password=app.config['ISSUE_TRACKER_PASSWORD'],
                                         issue_tracker_project_id=app.config['ISSUE_TRACKER_PROJECT_ID'],
                                         issue_tracker_max_results=app.config['ISSUE_TRACKER_MAX_RESULTS'])
                jira_client.get_issues('key')
            except JIRAError as e:
                self.assertTrue(type(e), type(JIRAError))
                self.assertTrue(e, 'Some exception')

    @unittest.mock.patch('amundsen_application.proxy.issue_tracker_clients.jira_client.JIRA')
    @unittest.mock.patch('amundsen_application.proxy.issue_tracker_clients.jira_client.'
                         'JiraClient._get_issue_properties')
    @unittest.mock.patch('amundsen_application.proxy.issue_tracker_clients.'
                         'jira_client.JiraClient._generate_all_issues_url')
    @unittest.mock.patch('amundsen_application.proxy.issue_tracker_clients.'
                         'jira_client.JiraClient._sort_issues')
    def test_get_issues_returns_issues(self,
                                       mock_sort_issues: Mock,
                                       mock_get_url: Mock,
                                       mock_get_issue_properties: Mock,
                                       mock_JIRA_client: Mock) -> None:
        mock_JIRA_client.return_value.search_issues.return_value = self.mock_jira_issues
        mock_get_issue_properties.return_value = self.mock_issue
        mock_get_url.return_value = 'url'
        mock_sort_issues.return_value = [self.mock_issue]
        with app.test_request_context():
            jira_client = JiraClient(issue_labels=[],
                                     issue_tracker_url=app.config['ISSUE_TRACKER_URL'],
                                     issue_tracker_user=app.config['ISSUE_TRACKER_USER'],
                                     issue_tracker_password=app.config['ISSUE_TRACKER_PASSWORD'],
                                     issue_tracker_project_id=app.config['ISSUE_TRACKER_PROJECT_ID'],
                                     issue_tracker_max_results=app.config['ISSUE_TRACKER_MAX_RESULTS'])
            results = jira_client.get_issues(table_uri='key')
            mock_JIRA_client.assert_called
            self.assertEqual(results.issues[0], self.mock_issue)
            self.assertEqual(results.total, self.mock_jira_issues.total)
            mock_JIRA_client.return_value.search_issues.assert_called_with(
                SEARCH_STUB_ALL_ISSUES.format(table_key="key"),
                maxResults=3)

    @unittest.mock.patch('amundsen_application.proxy.issue_tracker_clients.jira_client.JIRA')
    @unittest.mock.patch('amundsen_application.proxy.issue_tracker_clients.jira_client.urllib.parse.quote')
    def test__generate_all_issues_url(self, mock_url_lib: Mock, mock_JIRA_client: Mock) -> None:
        mock_url_lib.return_value = 'test'
        with app.test_request_context():
            jira_client = JiraClient(issue_labels=[],
                                     issue_tracker_url=app.config['ISSUE_TRACKER_URL'],
                                     issue_tracker_user=app.config['ISSUE_TRACKER_USER'],
                                     issue_tracker_password=app.config['ISSUE_TRACKER_PASSWORD'],
                                     issue_tracker_project_id=app.config['ISSUE_TRACKER_PROJECT_ID'],
                                     issue_tracker_max_results=app.config['ISSUE_TRACKER_MAX_RESULTS'])
            issues = [DataIssue(issue_key='key', title='title', url='url', status='open', priority=Priority.P2)]
            url = jira_client._generate_all_issues_url(table_uri="table", issues=issues)
            self.assertEqual(url, 'test_url/issues/?jql=test')

    @unittest.mock.patch('amundsen_application.proxy.issue_tracker_clients.jira_client.JIRA')
    def test__generate_all_issues_url_no_issues(self, mock_JIRA_client: Mock) -> None:
        with app.test_request_context():
            jira_client = JiraClient(issue_labels=[],
                                     issue_tracker_url=app.config['ISSUE_TRACKER_URL'],
                                     issue_tracker_user=app.config['ISSUE_TRACKER_USER'],
                                     issue_tracker_password=app.config['ISSUE_TRACKER_PASSWORD'],
                                     issue_tracker_project_id=app.config['ISSUE_TRACKER_PROJECT_ID'],
                                     issue_tracker_max_results=app.config['ISSUE_TRACKER_MAX_RESULTS'])
            issues: List[DataIssue]
            issues = []
            url = jira_client._generate_all_issues_url(table_uri="table", issues=issues)
            self.assertEqual(url, '')

    @unittest.mock.patch('amundsen_application.proxy.issue_tracker_clients.jira_client.JIRA')
    def test_create_returns_JIRAError(self, mock_JIRA_client: Mock) -> None:
        mock_JIRA_client.return_value.create_issue.side_effect = JIRAError('Some exception')
        with app.test_request_context():
            try:
                jira_client = JiraClient(issue_labels=[],
                                         issue_tracker_url=app.config['ISSUE_TRACKER_URL'],
                                         issue_tracker_user=app.config['ISSUE_TRACKER_USER'],
                                         issue_tracker_password=app.config['ISSUE_TRACKER_PASSWORD'],
                                         issue_tracker_project_id=app.config['ISSUE_TRACKER_PROJECT_ID'],
                                         issue_tracker_max_results=app.config['ISSUE_TRACKER_MAX_RESULTS'])
                jira_client.create_issue(description='desc', table_uri='key', title='title')
            except JIRAError as e:
                self.assertTrue(type(e), type(JIRAError))
                self.assertTrue(e, 'Some exception')

    @unittest.mock.patch('amundsen_application.proxy.issue_tracker_clients.jira_client.JIRA')
    @unittest.mock.patch('amundsen_application.proxy.issue_tracker_clients.jira_client.'
                         'JiraClient._get_issue_properties')
    def test_create_issue(self, mock_get_issue_properties: Mock, mock_JIRA_client: Mock) -> None:
        mock_JIRA_client.return_value.create_issue.return_value = self.mock_issue
        mock_get_issue_properties.return_value = self.mock_issue_instance
        mock_labels = ['mock-label']
        with app.test_request_context():
            jira_client = JiraClient(issue_labels=mock_labels,
                                     issue_tracker_url=app.config['ISSUE_TRACKER_URL'],
                                     issue_tracker_user=app.config['ISSUE_TRACKER_USER'],
                                     issue_tracker_password=app.config['ISSUE_TRACKER_PASSWORD'],
                                     issue_tracker_project_id=app.config['ISSUE_TRACKER_PROJECT_ID'],
                                     issue_tracker_max_results=app.config['ISSUE_TRACKER_MAX_RESULTS'])
            results = jira_client.create_issue(description='desc', table_uri='key', title='title')
            mock_JIRA_client.assert_called
            self.assertEqual(results, self.mock_issue_instance)
            mock_JIRA_client.return_value.create_issue.assert_called_with(fields=dict(project={
                'id': app.config["ISSUE_TRACKER_PROJECT_ID"]
            }, issuetype={
                'id': 1,
                'name': 'Bug',
            }, labels=mock_labels,
                summary='title',
                description='desc \n Reported By: test@email.com \n Table Key: key [PLEASE DO NOT REMOVE]',
                reporter={'name': 'test'}))
