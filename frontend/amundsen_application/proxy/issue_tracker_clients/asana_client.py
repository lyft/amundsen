# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import asana
import logging
from typing import Dict, List

from amundsen_application.base.base_issue_tracker_client import BaseIssueTrackerClient
from amundsen_application.models.data_issue import DataIssue, Priority
from amundsen_application.models.issue_results import IssueResults


class AsanaClient(BaseIssueTrackerClient):

    def __init__(self, issue_labels: List[str],
                 issue_tracker_url: str,
                 issue_tracker_user: str,
                 issue_tracker_password: str,
                 issue_tracker_project_id: int,
                 issue_tracker_max_results: int) -> None:
        self.issue_labels = issue_labels
        self.asana_url = issue_tracker_url
        self.asana_user = issue_tracker_user
        self.asana_password = issue_tracker_password
        self.asana_max_results = issue_tracker_max_results

        self.asana_project_gid = issue_tracker_project_id
        self.asana_client = asana.Client.access_token(issue_tracker_password)

        asana_project = self.asana_client.projects.get_project(self.asana_project_gid)
        self.asana_workspace_gid = asana_project['workspace']['gid']

        self._setup_custom_fields()

    def get_issues(self, table_uri: str) -> IssueResults:
        """
        :param table_uri: Table Uri ie databasetype://database/table
        :return: Metadata of matching issues
        """

        table_parent_task_gid = self._get_parent_task_gid_for_table_uri(table_uri)

        tasks = list(self.asana_client.tasks.get_subtasks_for_task(
            table_parent_task_gid,
            {
                'opt_fields': [
                    'name', 'completed', 'notes', 'custom_fields',
                ]
            }
        ))

        return IssueResults(
            issues=[
                self._asana_task_to_amundsen_data_issue(task) for task in tasks
            ],
            total=len(tasks),
            all_issues_url=self._task_url(table_parent_task_gid),
        )

    def create_issue(self, table_uri: str, title: str, description: str) -> DataIssue:
        """
        Creates an issue in Jira
        :param description: Description of the Jira issue
        :param table_uri: Table Uri ie databasetype://database/table
        :param title: Title of the Jira ticket
        :return: Metadata about the newly created issue
        """

        table_parent_task_gid = self._get_parent_task_gid_for_table_uri(table_uri)

        return self._asana_task_to_amundsen_data_issue(
            self.asana_client.tasks.create_subtask_for_task(
                table_parent_task_gid,
                {
                    'name': title,
                    'notes': description,
                }
            )
        )

    def _setup_custom_fields(self) -> None:
        TABLE_URI_FIELD_NAME = 'Table URI (Amundsen)'
        PRIORITY_FIELD_NAME = 'Priority (Amundsen)'

        custom_fields = \
            self.asana_client.custom_field_settings.get_custom_field_settings_for_project(
                self.asana_project_gid
            )

        custom_fields = {f['custom_field']['name']: f['custom_field'] for f in custom_fields}

        if TABLE_URI_FIELD_NAME in custom_fields:
            table_uri_field = custom_fields[TABLE_URI_FIELD_NAME]
        else:
            table_uri_field = self.asana_client.custom_fields.create_custom_field({
                'workspace': self.asana_workspace_gid,
                'name': TABLE_URI_FIELD_NAME,
                'format': 'custom',
                'resource_subtype': 'text',
            })

            self.asana_client.projects.add_custom_field_setting_for_project(
                self.asana_project_gid,
                {
                    'custom_field': table_uri_field['gid'],
                    'is_important': True,
                }
            )

        if PRIORITY_FIELD_NAME in custom_fields:
            priority_field = custom_fields[PRIORITY_FIELD_NAME]
        else:
            priority_field = self.asana_client.custom_fields.create_custom_field({
                'workspace': self.asana_workspace_gid,
                'name': PRIORITY_FIELD_NAME,
                'format': 'custom',
                'resource_subtype': 'enum',
                'enum_options': [
                    {
                        'name': p.level
                    } for p in Priority
                ]
            })

            self.asana_client.projects.add_custom_field_setting_for_project(
                self.asana_project_gid,
                {
                    'custom_field': priority_field['gid'],
                    'is_important': True,
                }
            )

        self.table_uri_field_gid = table_uri_field['gid']
        self.priority_field_gid = priority_field['gid']

    def _get_parent_task_gid_for_table_uri(self, table_uri: str) -> str:
        table_parent_tasks = list(self.asana_client.tasks.search_tasks_for_workspace(
            self.asana_workspace_gid,
            {
                'projects.any': [self.asana_project_gid],
                'custom_fields.{}.value'.format(self.table_uri_field_gid): table_uri,
            }
        ))

        # Create the parent task if it doesn't exist.
        if len(table_parent_tasks) == 0:
            table_parent_task = self.asana_client.tasks.create_task({
                'name': table_uri,
                'custom_fields': {
                    self.table_uri_field_gid: table_uri,
                },
                'projects': [self.asana_project_gid],
            })

            return table_parent_task['gid']
        else:
            if len(table_parent_tasks) > 1:
                logging.warn('There are currently two tasks with the name "{}"'.format(table_uri))

            return table_parent_tasks[0]['gid']

    def _task_url(self, task_gid: str) -> str:
        return 'https://app.asana.com/0/{project_gid}/{task_gid}'.format(
            project_gid=self.asana_project_gid, task_gid=task_gid
        )

    def _asana_task_to_amundsen_data_issue(self, task: Dict) -> DataIssue:
        custom_fields = {f['gid']: f for f in task['custom_fields']}
        priority_field = custom_fields[self.priority_field_gid]

        priority = None
        if priority_field.get('enum_value'):
            priority = Priority.from_level(priority_field['enum_value']['name'])
        else:
            priority = Priority.P3

        return DataIssue(
            issue_key=task['gid'],
            title=task['name'],
            url=self._task_url(task['gid']),
            status='closed' if task['completed'] else 'open',
            priority=priority,
        )
