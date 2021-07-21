# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from databuilder.models.elasticsearch_document import ElasticsearchDocument


class UserESDocument(ElasticsearchDocument):
    """
    Schema for the Search index document for user
    """

    def __init__(self,
                 email: str,
                 first_name: str,
                 last_name: str,
                 full_name: str,
                 github_username: str,
                 team_name: str,
                 employee_type: str,
                 manager_email: str,
                 slack_id: str,
                 role_name: str,
                 is_active: bool,
                 total_read: int,
                 total_own: int,
                 total_follow: int,
                 ) -> None:
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.full_name = full_name
        self.github_username = github_username
        self.team_name = team_name
        self.employee_type = employee_type
        self.manager_email = manager_email
        self.slack_id = slack_id
        self.role_name = role_name
        self.is_active = is_active
        self.total_read = total_read
        self.total_own = total_own
        self.total_follow = total_follow
