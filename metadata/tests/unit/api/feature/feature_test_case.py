# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from unittest.mock import Mock, patch

from tests.unit.test_basics import BasicTestCase


class FeatureTestCase(BasicTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.mock_client = patch('metadata_service.api.feature.get_proxy_client')
        self.mock_proxy = self.mock_client.start().return_value = Mock()

    def tearDown(self) -> None:
        super().tearDown()
        self.mock_client.stop()
