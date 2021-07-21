# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0


from typing import Iterator, Optional
from xml.etree import ElementTree

import requests
from pyhocon import ConfigTree
from requests.auth import HTTPBasicAuth

from databuilder.extractor.base_extractor import Extractor
from databuilder.models.user import User


class BamboohrUserExtractor(Extractor):
    API_KEY = 'api_key'
    SUBDOMAIN = 'subdomain'

    def init(self, conf: ConfigTree) -> None:
        self._extract_iter: Optional[Iterator] = None
        self._extract_iter = None

        self._api_key = conf.get_string(BamboohrUserExtractor.API_KEY)
        self._subdomain = conf.get_string(BamboohrUserExtractor.SUBDOMAIN)

    def extract(self) -> Optional[User]:
        if not self._extract_iter:
            self._extract_iter = self._get_extract_iter()
        try:
            return next(self._extract_iter)
        except StopIteration:
            return None

    def _employee_directory_uri(self) -> str:
        return f'https://api.bamboohr.com/api/gateway.php/{self._subdomain}/v1/employees/directory'

    def _get_extract_iter(self) -> Iterator[User]:
        response = requests.get(
            self._employee_directory_uri(), auth=HTTPBasicAuth(self._api_key, 'x')
        )

        root = ElementTree.fromstring(response.content)

        for user in root.findall('./employees/employee'):

            def get_field(name: str) -> str:
                field = user.find(f"./field[@id='{name}']")
                if field is not None and field.text is not None:
                    return field.text
                else:
                    return ''

            yield User(
                email=get_field('workEmail'),
                first_name=get_field('firstName'),
                last_name=get_field('lastName'),
                name=get_field('displayName'),
                team_name=get_field('department'),
                role_name=get_field('jobTitle'),
            )

    def get_scope(self) -> str:
        return 'extractor.bamboohr_user'
