# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import json
import unittest

from databuilder.models.user_elasticsearch_document import UserESDocument


class TestUserElasticsearchDocument(unittest.TestCase):

    def test_to_json(self) -> None:
        """
        Test string generated from to_json method
        """
        test_obj = UserESDocument(email='test@email.com',
                                  first_name='test_firstname',
                                  last_name='test_lastname',
                                  full_name='full_name',
                                  github_username='github_user',
                                  team_name='team',
                                  employee_type='fte',
                                  manager_email='test_manager',
                                  slack_id='test_slack',
                                  role_name='role_name',
                                  is_active=True,
                                  total_read=2,
                                  total_own=3,
                                  total_follow=1)

        expected_document_dict = {"first_name": "test_firstname",
                                  "last_name": "test_lastname",
                                  "full_name": "full_name",
                                  "team_name": "team",
                                  "total_follow": 1,
                                  "total_read": 2,
                                  "is_active": True,
                                  "total_own": 3,
                                  "slack_id": 'test_slack',
                                  "role_name": 'role_name',
                                  "manager_email": "test_manager",
                                  'github_username': "github_user",
                                  "employee_type": 'fte',
                                  "email": "test@email.com",
                                  }

        result = test_obj.to_json()
        results = result.split("\n")

        # verify two new line characters in result
        self.assertEqual(len(results), 2, "Result from to_json() function doesn't have a newline!")

        self.assertDictEqual(json.loads(results[0]), expected_document_dict)
