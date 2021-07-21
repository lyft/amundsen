# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import unittest

from flask import current_app
from http import HTTPStatus


from amundsen_application import create_app
from amundsen_application.api.preview.dashboard import v0
from amundsen_application.base.base_preview import BasePreview
from amundsen_application.api.preview.dashboard.dashboard_preview.preview_factory_method import \
    DefaultPreviewMethodFactory, BasePreviewMethodFactory

from unittest.mock import MagicMock


class TestV0(unittest.TestCase):

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

    def test_v0_default_initialize_preview_factory_class(self) -> None:
        v0.initialize_preview_factory_class()
        self.assertTrue(isinstance(v0.PREVIEW_FACTORY, DefaultPreviewMethodFactory))

    def test_v0_initialize_preview_factory_class(self) -> None:
        self.app.config['DASHBOARD_PREVIEW_FACTORY'] = DummyPreviewMethodFactory()

        v0.initialize_preview_factory_class()
        self.assertTrue(isinstance(v0.PREVIEW_FACTORY, DummyPreviewMethodFactory))

    def test_get_preview_image_not_available(self) -> None:
        mock_factory = MagicMock()
        mock_factory.get_instance.return_value.get_preview_image.side_effect = FileNotFoundError('foo')

        self.app.config['DASHBOARD_PREVIEW_FACTORY'] = mock_factory
        v0.initialize_preview_factory_class()

        response = v0.get_preview_image(uri='foo')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_get_preview_image_failure(self) -> None:
        mock_factory = MagicMock()
        mock_factory.get_instance.return_value.get_preview_image.side_effect = Exception()

        self.app.config['DASHBOARD_PREVIEW_FACTORY'] = mock_factory
        v0.initialize_preview_factory_class()

        response = v0.get_preview_image(uri='foo')
        self.assertEqual(response.status_code, HTTPStatus.INTERNAL_SERVER_ERROR)


class DummyPreviewMethodFactory(BasePreviewMethodFactory):
    def get_instance(self, *, uri: str) -> BasePreview:
        pass
