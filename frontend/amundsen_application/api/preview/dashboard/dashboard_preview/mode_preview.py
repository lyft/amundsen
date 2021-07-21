# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import logging
from typing import Optional, Any

import requests
from flask import has_app_context, current_app as app
from requests.auth import HTTPBasicAuth
from retrying import retry

from amundsen_application.api.metadata.v0 import USER_ENDPOINT
from amundsen_application.api.utils.request_utils import request_metadata
from amundsen_application.base.base_preview import BasePreview
from amundsen_application.models.user import load_user

LOGGER = logging.getLogger(__name__)
DEFAULT_REPORT_URL_TEMPLATE = 'https://app.mode.com/api/{organization}/reports/{dashboard_id}'


def _validate_not_none(var: Any, var_name: str) -> Any:
    if not var:
        raise ValueError('{} is missing'.format(var_name))
    return var


def _retry_on_retriable_error(exception: Exception) -> bool:
    return not isinstance(exception, PermissionError)


class ModePreview(BasePreview):
    """
    A class to get Mode Dashboard preview image
    """

    def __init__(self, *,
                 access_token: Optional[str] = None,
                 password: Optional[str] = None,
                 organization: Optional[str] = None,
                 report_url_template: Optional[str] = None):
        self._access_token = access_token if access_token else app.config['CREDENTIALS_MODE_ADMIN_TOKEN']
        _validate_not_none(self._access_token, 'access_token')
        self._password = password if password else app.config['CREDENTIALS_MODE_ADMIN_PASSWORD']
        _validate_not_none(self._password, 'password')
        self._organization = organization if organization else app.config['MODE_ORGANIZATION']
        _validate_not_none(self._organization, 'organization')

        self._report_url_template = report_url_template if report_url_template else DEFAULT_REPORT_URL_TEMPLATE

        if has_app_context() and app.config['MODE_REPORT_URL_TEMPLATE'] is not None:
            self._report_url_template = app.config['MODE_REPORT_URL_TEMPLATE']

        self._is_auth_enabled = False
        if has_app_context() and app.config['ACL_ENABLED_DASHBOARD_PREVIEW']:
            if not app.config['AUTH_USER_METHOD']:
                raise Exception('AUTH_USER_METHOD must be configured to enable ACL_ENABLED_DASHBOARD_PREVIEW')
            self._is_auth_enabled = self.__class__.__name__ in app.config['ACL_ENABLED_DASHBOARD_PREVIEW']
            self._auth_user_method = app.config['AUTH_USER_METHOD']

    @retry(stop_max_attempt_number=3, wait_random_min=500, wait_random_max=1000,
           retry_on_exception=_retry_on_retriable_error)
    def get_preview_image(self, *, uri: str) -> bytes:
        """
        Retrieves short lived URL that provides Mode report preview, downloads it and returns it's bytes
        :param uri:
        :return: image bytes
        :raise: PermissionError when user is not allowed to access the dashboard
        """
        if self._is_auth_enabled:
            self._authorize_access(user_id=self._auth_user_method(app).user_id)

        url = self._get_preview_image_url(uri=uri)
        r = requests.get(url, allow_redirects=True)
        r.raise_for_status()

        return r.content

    def _get_preview_image_url(self, *, uri: str) -> str:
        url = self._report_url_template.format(organization=self._organization, dashboard_id=uri.split('/')[-1])

        LOGGER.info('Calling URL {} to fetch preview image URL'.format(url))
        response = requests.get(url, auth=HTTPBasicAuth(self._access_token, self._password))
        if response.status_code == 404:
            raise FileNotFoundError('Dashboard {} not found. Possibly has been deleted.'.format(uri))

        response.raise_for_status()

        web_preview_image_key = 'web_preview_image'
        result = response.json()

        if web_preview_image_key not in result:
            raise FileNotFoundError('No preview image available on {}'.format(uri))

        image_url = result[web_preview_image_key]
        if image_url is None:
            raise FileNotFoundError('No preview image available on {}'.format(uri))

        return image_url

    def _authorize_access(self, user_id: str) -> None:
        """
        Get Mode user ID via metadata service. Note that metadata service needs to be at least v2.5.2 and
        Databuilder should also have ingested Mode user.
        https://github.com/lyft/amundsendatabuilder#modedashboarduserextractor

        :param user_id:
        :return:
        :raise: PermissionError when user is not allowed to access the dashboard
        """

        metadata_svc_url = '{0}{1}/{2}'.format(app.config['METADATASERVICE_BASE'], USER_ENDPOINT, user_id)
        response = request_metadata(url=metadata_svc_url)
        response.raise_for_status()

        user = load_user(response.json())
        if user.is_active and user.other_key_values and user.other_key_values.get('mode_user_id'):
            return

        raise PermissionError('User {} is not authorized to preview Mode Dashboard'.format(user_id))
