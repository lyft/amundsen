# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

# flake8: noqa
import unittest
from unittest.mock import patch

import requests
from requests.auth import HTTPBasicAuth
from unittest.mock import MagicMock

from amundsen_application import create_app
from amundsen_application.api.preview.dashboard.dashboard_preview.mode_preview import ModePreview, DEFAULT_REPORT_URL_TEMPLATE
from amundsen_application.api.utils import request_utils

ACCESS_TOKEN = 'token'
PASSWORD = 'password'
ORGANIZATION = 'foo'


class TestModePreview(unittest.TestCase):

    def setUp(self) -> None:
        self.app = create_app(config_module_class='amundsen_application.config.LocalConfig')
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self) -> None:
        self.app_context.pop()

    def test_get_preview_image(self) -> None:
        with patch.object(ModePreview, '_get_preview_image_url') as mock_get_preview_image_url,\
                patch.object(requests, 'get') as mock_get:
            mock_get_preview_image_url.return_value = 'http://foo.bar/image.jpeg'
            mock_get.return_value.content = b'bar'

            preview = ModePreview(access_token='token', password='password', organization='foo')

            mode_dashboard_uri = 'mode_dashboard://gold.dg/d_id'
            actual = preview.get_preview_image(uri=mode_dashboard_uri)

            self.assertEqual(b'bar', actual)
            mock_get.assert_called_with('http://foo.bar/image.jpeg', allow_redirects=True)

    def test_get_preview_image_url_success(self) -> None:
        with patch.object(requests, 'get') as mock_get:
            mock_get.return_value.json.return_value = {'web_preview_image': 'http://foo.bar/image.jpeg'}

            preview = ModePreview(access_token='token', password='password', organization='foo')
            mode_dashboard_uri = 'mode_dashboard://gold.dg/d_id'
            url = preview._get_preview_image_url(uri=mode_dashboard_uri)

            self.assertEqual(url, 'http://foo.bar/image.jpeg')

            expected_url = DEFAULT_REPORT_URL_TEMPLATE.format(organization=ORGANIZATION, dashboard_id='d_id')
            mock_get.assert_called_with(expected_url, auth=HTTPBasicAuth(ACCESS_TOKEN, PASSWORD))

    def test_get_preview_image_url_failure_none_value(self) -> None:
        with patch.object(requests, 'get') as mock_get:
            mock_get.return_value.json.return_value = {'web_preview_image': None}

            preview = ModePreview(access_token='token', password='password', organization='foo')
            mode_dashboard_uri = 'mode_dashboard://gold.dg/d_id'
            self.assertRaises(FileNotFoundError, preview._get_preview_image_url, uri=mode_dashboard_uri)

    def test_get_preview_image_url_failure_missing_key(self) -> None:
        with patch.object(requests, 'get') as mock_get:
            mock_get.return_value.json.return_value = {}

            preview = ModePreview(access_token='token', password='password', organization='foo')
            mode_dashboard_uri = 'mode_dashboard://gold.dg/d_id'
            self.assertRaises(FileNotFoundError, preview._get_preview_image_url, uri=mode_dashboard_uri)

    def test_auth_disabled(self) -> None:
        preview = ModePreview(access_token='token', password='password', organization='foo')
        self.assertFalse(preview._is_auth_enabled)

    def test_auth_disabled_2(self) -> None:
        self.app.config['ACL_ENABLED_DASHBOARD_PREVIEW'] = {'FooPreview'}
        self.app.config['AUTH_USER_METHOD'] = MagicMock()

        preview = ModePreview(access_token='token', password='password', organization='foo')
        self.assertFalse(preview._is_auth_enabled)

    def test_auth_enabled(self) -> None:
        self.app.config['ACL_ENABLED_DASHBOARD_PREVIEW'] = {'ModePreview'}
        self.app.config['AUTH_USER_METHOD'] = MagicMock()

        preview = ModePreview(access_token='token', password='password', organization='foo')
        self.assertTrue(preview._is_auth_enabled)

    def test_authorization(self) -> None:
        self.app.config['ACL_ENABLED_DASHBOARD_PREVIEW'] = {'ModePreview'}
        self.app.config['AUTH_USER_METHOD'] = MagicMock()

        with patch('amundsen_application.api.preview.dashboard.dashboard_preview.mode_preview.request_metadata') as mock_request_metadata:
            mock_request_metadata.return_value.json.return_value = {
                'employee_type': 'teamMember',
                'full_name': 'test_full_name',
                'is_active': 'True',
                'github_username': 'test-github',
                'slack_id': 'test_id',
                'last_name': 'test_last_name',
                'first_name': 'test_first_name',
                'team_name': 'test_team',
                'email': 'test_email',
                'other_key_values': {
                    'mode_user_id': 'foo_mode_user_id'
                }
            }

            preview = ModePreview(access_token='token', password='password', organization='foo')
            preview._authorize_access(user_id='test_email')

        with patch('amundsen_application.api.preview.dashboard.dashboard_preview.mode_preview.request_metadata') as mock_request_metadata:
            mock_request_metadata.return_value.json.return_value = {
                'employee_type': 'teamMember',
                'full_name': 'test_full_name',
                'is_active': 'False',
                'github_username': 'test-github',
                'slack_id': 'test_id',
                'last_name': 'test_last_name',
                'first_name': 'test_first_name',
                'team_name': 'test_team',
                'email': 'test_email',
                'other_key_values': {
                    'mode_user_id': 'foo_mode_user_id'
                }
            }

            preview = ModePreview(access_token='token', password='password', organization='foo')
            self.assertRaises(PermissionError, preview._authorize_access, user_id='test_email')

        with patch('amundsen_application.api.preview.dashboard.dashboard_preview.mode_preview.request_metadata') as mock_request_metadata:
            mock_request_metadata.return_value.json.return_value = {
                'employee_type': 'teamMember',
                'full_name': 'test_full_name',
                'is_active': 'True',
                'github_username': 'test-github',
                'slack_id': 'test_id',
                'last_name': 'test_last_name',
                'first_name': 'test_first_name',
                'team_name': 'test_team',
                'email': 'test_email',
                'other_key_values': {}
            }

            preview = ModePreview(access_token='token', password='password', organization='foo')
            self.assertRaises(PermissionError, preview._authorize_access, user_id='test_email')

        with patch('amundsen_application.api.preview.dashboard.dashboard_preview.mode_preview.request_metadata') as mock_request_metadata:
            mock_request_metadata.return_value.json.return_value = {
                'employee_type': 'teamMember',
                'full_name': 'test_full_name',
                'is_active': 'True',
                'github_username': 'test-github',
                'slack_id': 'test_id',
                'last_name': 'test_last_name',
                'first_name': 'test_first_name',
                'team_name': 'test_team',
                'email': 'test_email',
                'other_key_values': {
                    'foo': 'bar'
                }
            }

            preview = ModePreview(access_token='token', password='password', organization='foo')
            self.assertRaises(PermissionError, preview._authorize_access, user_id='test_email')

        with patch('amundsen_application.api.preview.dashboard.dashboard_preview.mode_preview.request_metadata') as mock_request_metadata:
            mock_request_metadata.return_value.json.return_value = {
                'employee_type': 'teamMember',
                'full_name': 'test_full_name',
                'is_active': 'True',
                'github_username': 'test-github',
                'slack_id': 'test_id',
                'last_name': 'test_last_name',
                'first_name': 'test_first_name',
                'team_name': 'test_team',
                'email': 'test_email',
                'other_key_values': None
            }

            preview = ModePreview(access_token='token', password='password', organization='foo')
            self.assertRaises(PermissionError, preview._authorize_access, user_id='test_email')

        with patch('amundsen_application.api.preview.dashboard.dashboard_preview.mode_preview.request_metadata') as mock_request_metadata:
            mock_request_metadata.return_value.json.return_value = {
                'employee_type': 'teamMember',
                'full_name': 'test_full_name',
                'is_active': 'True',
                'github_username': 'test-github',
                'slack_id': 'test_id',
                'last_name': 'test_last_name',
                'first_name': 'test_first_name',
                'team_name': 'test_team',
                'email': 'test_email',
            }

            preview = ModePreview(access_token='token', password='password', organization='foo')
            self.assertRaises(PermissionError, preview._authorize_access, user_id='test_email')


if __name__ == '__main__':
    unittest.main()
