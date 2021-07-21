# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import unittest
import flask

from amundsen_application.base.base_preview_client import BasePreviewClient

app = flask.Flask(__name__)
app.config.from_object('amundsen_application.config.LocalConfig')


class PreviewClientTest(unittest.TestCase):

    def test_cover_abtract_methods(self) -> None:
        abstract_methods_set = {
            '__init__',
            'get_preview_data',
            'get_feature_preview_data'
        }
        # Use getattr to prevent mypy warning
        cls_abstrct_methods = getattr(BasePreviewClient, '__abstractmethods__')
        self.assertEquals(cls_abstrct_methods, abstract_methods_set)
