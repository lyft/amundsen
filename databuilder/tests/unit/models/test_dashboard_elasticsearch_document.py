# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import json
import unittest

from databuilder.models.dashboard_elasticsearch_document import DashboardESDocument


class TestDashboardElasticsearchDocument(unittest.TestCase):

    def test_to_json(self) -> None:
        """
        Test string generated from to_json method
        """
        test_obj = DashboardESDocument(group_name='test_dashboard_group',
                                       name='test_dashboard_name',
                                       description='test_description',
                                       product='mode',
                                       cluster='gold',
                                       group_description='work space group',
                                       query_names=['query1'],
                                       chart_names=['chart1'],
                                       group_url='mode_group_url',
                                       url='mode_report_url',
                                       uri='mode_dashboard://gold.cluster/dashboard_group/dashboard',
                                       last_successful_run_timestamp=10,
                                       total_usage=10,
                                       tags=['test'],
                                       badges=['test_badge'])

        expected_document_dict = {"group_name": "test_dashboard_group",
                                  "name": "test_dashboard_name",
                                  "description": "test_description",
                                  "product": "mode",
                                  "cluster": "gold",
                                  "group_url": "mode_group_url",
                                  "url": "mode_report_url",
                                  "uri": "mode_dashboard://gold.cluster/dashboard_group/dashboard",
                                  "query_names": ['query1'],
                                  "chart_names": ['chart1'],
                                  "last_successful_run_timestamp": 10,
                                  "group_description": "work space group",
                                  "total_usage": 10,
                                  "tags": ["test"],
                                  "badges": ["test_badge"],

                                  }

        result = test_obj.to_json()
        results = result.split("\n")

        # verify two new line characters in result
        self.assertEqual(len(results), 2, "Result from to_json() function doesn't have a newline!")
        self.assertDictEqual(json.loads(results[0]), expected_document_dict)
