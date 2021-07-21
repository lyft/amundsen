# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

# flake8: noqa
import unittest

from flask import current_app

from amundsen_application import create_app
from amundsen_application.api.preview.dashboard.dashboard_preview.mode_preview import ModePreview
from amundsen_application.api.preview.dashboard.dashboard_preview.preview_factory_method import DefaultPreviewMethodFactory


class TestDefaultPreviewFactory(unittest.TestCase):

    def setUp(self) -> None:
        self.app = create_app(config_module_class='amundsen_application.config.LocalConfig')
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.app.config['CREDENTIALS_MODE_ADMIN_TOKEN'] = 'CREDENTIALS_MODE_ADMIN_TOKEN'
        self.app.config['CREDENTIALS_MODE_ADMIN_PASSWORD'] = 'CREDENTIALS_MODE_ADMIN_PASSWORD'
        self.app.config['MODE_ORGANIZATION'] = 'foo'

    def tearDown(self) -> None:
        self.app_context.pop()

    def test_app_exists(self) -> None:
        self.assertFalse(current_app is None)

    def test_factory(self) -> None:
        factory = DefaultPreviewMethodFactory()
        actual = factory.get_instance(uri='mode_dashboard://gold.dg_id/d_id')

        self.assertTrue(isinstance(actual, ModePreview))

        try:
            factory.get_instance(uri='tableau_dashboard://foo.bar/baz')
            self.assertTrue(False, 'Should have failed for we currently do not support Tableau')
        except Exception:
            pass
