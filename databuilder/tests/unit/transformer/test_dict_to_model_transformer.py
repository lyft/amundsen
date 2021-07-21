# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import unittest

from pyhocon import ConfigFactory

from databuilder.models.dashboard.dashboard_execution import DashboardExecution
from databuilder.transformer.dict_to_model import MODEL_CLASS, DictToModel


class TestDictToModel(unittest.TestCase):

    def test_conversion(self) -> None:

        transformer = DictToModel()
        config = ConfigFactory.from_dict({
            MODEL_CLASS: 'databuilder.models.dashboard.dashboard_execution.DashboardExecution',
        })
        transformer.init(conf=config)

        actual = transformer.transform(
            {
                'dashboard_group_id': 'foo',
                'dashboard_id': 'bar',
                'execution_timestamp': 123456789,
                'execution_state': 'succeed',
                'product': 'mode',
                'cluster': 'gold'
            }
        )

        self.assertTrue(isinstance(actual, DashboardExecution))
        self.assertEqual(actual.__repr__(), DashboardExecution(
            dashboard_group_id='foo',
            dashboard_id='bar',
            execution_timestamp=123456789,
            execution_state='succeed',
            product='mode',
            cluster='gold'
        ).__repr__())
