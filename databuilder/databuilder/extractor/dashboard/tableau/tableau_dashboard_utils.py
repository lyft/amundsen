# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import json
import re
from typing import (
    Any, Dict, Iterator, Optional,
)

import requests
from pyhocon import ConfigTree

import databuilder.extractor.dashboard.tableau.tableau_dashboard_constants as const
from databuilder.extractor.base_extractor import Extractor
from databuilder.extractor.restapi.rest_api_extractor import STATIC_RECORD_DICT


class TableauDashboardUtils:
    """
    Provides various utility functions specifc to the Tableau dashboard extractors.
    """

    @staticmethod
    def sanitize_schema_name(schema_name: str) -> str:
        """
        Sanitizes a given string so that it can safely be used as a table's schema.
        Sanitization behaves as follows:
            - all spaces and periods are replaced by underscores
            - any [], (), -, &, and ? characters are deleted
        """
        # this indentation looks a little odd, but otherwise the linter complains
        return re.sub(r' ', '_',
                      re.sub(r'\.', '_',
                             re.sub(r'(\[|\]|\(|\)|\-|\&|\?)', '', schema_name)))

    @staticmethod
    def sanitize_database_name(database_name: str) -> str:
        """
        Sanitizes a given string so that it can safely be used as a table's database.
        Sanitization behaves as follows:
            - all hyphens are deleted
        """
        return re.sub(r'-', '', database_name)

    @staticmethod
    def sanitize_table_name(table_name: str) -> str:
        """
        Sanitizes a given string so that it can safely be used as a table name.
        Replicates the current behavior of sanitize_workbook_name, but this is purely coincidental.
        As more breaking characters/patterns are found, each method should be updated to reflect the specifics.
        Sanitization behaves as follows:
            - all forward slashes and single quotes characters are deleted
        """
        return re.sub(r'(\/|\')', '', table_name)

    @staticmethod
    def sanitize_workbook_name(workbook_name: str) -> str:
        """
        Sanitizes a given string so that it can safely be used as a workbook ID.
        Mimics the current behavior of sanitize_table_name for now, but is purely coincidental.
        As more breaking characters/patterns are found, each method should be updated to reflect the specifics.
        Sanitization behaves as follows:
            - all forward slashes and single quotes characters are deleted
        """
        return re.sub(r'(\/|\')', '', workbook_name)


class TableauGraphQLApiExtractor(Extractor):
    """
    Base class for querying the Tableau Metdata API, which uses a GraphQL schema.
    """

    API_BASE_URL = const.API_BASE_URL
    QUERY = 'query'
    QUERY_VARIABLES = 'query_variables'
    VERIFY_REQUEST = 'verify_request'

    def init(self, conf: ConfigTree) -> None:
        self._conf = conf
        self._auth_token = TableauDashboardAuth(self._conf).token
        self._query = self._conf.get(TableauGraphQLApiExtractor.QUERY)
        self._iterator: Optional[Iterator[Dict[str, Any]]] = None
        self._static_dict = conf.get(STATIC_RECORD_DICT, dict())
        self._metadata_url = '{api_base_url}/api/metadata/graphql'.format(
            api_base_url=self._conf.get_string(TableauGraphQLApiExtractor.API_BASE_URL)
        )
        self._query_variables = self._conf.get(TableauGraphQLApiExtractor.QUERY_VARIABLES, {})
        self._verify_request = self._conf.get(TableauGraphQLApiExtractor.VERIFY_REQUEST, None)

    def execute_query(self) -> Dict[str, Any]:
        """
        Executes the extractor's given query and returns the data from the results.
        """
        query_payload = json.dumps({
            'query': self._query,
            'variables': self._query_variables
        })
        headers = {
            'Content-Type': 'application/json',
            'X-Tableau-Auth': self._auth_token
        }
        params = {
            'headers': headers
        }
        if self._verify_request is not None:
            params['verify'] = self._verify_request

        response = requests.post(url=self._metadata_url, data=query_payload, **params)
        return response.json()['data']

    def execute(self) -> Iterator[Dict[str, Any]]:
        """
        Must be overriden by any extractor using this class. This should parse the result and yield each entity's
        metadata one by one.
        """
        pass

    def extract(self) -> Any:
        """
        Fetch one result at a time from the generator created by self.execute(), updating using the
        static record values if needed.
        """
        if not self._iterator:
            self._iterator = self.execute()

        try:
            record = next(self._iterator)
        except StopIteration:
            return None

        if self._static_dict:
            record.update(self._static_dict)

        return record


class TableauDashboardAuth:
    """
    Attempts to authenticate agains the Tableau REST API using the provided personal access token credentials.
    When successful, it will create a valid token that must be used on all subsequent requests.
    https://help.tableau.com/current/api/rest_api/en-us/REST/rest_api_concepts_auth.htm
    """

    API_BASE_URL = const.API_BASE_URL
    API_VERSION = const.API_VERSION
    SITE_NAME = const.SITE_NAME
    TABLEAU_ACCESS_TOKEN_NAME = const.TABLEAU_ACCESS_TOKEN_NAME
    TABLEAU_ACCESS_TOKEN_SECRET = const.TABLEAU_ACCESS_TOKEN_SECRET
    VERIFY_REQUEST = const.VERIFY_REQUEST

    def __init__(self, conf: ConfigTree) -> None:
        self._token: Optional[str] = None
        self._conf = conf
        self._access_token_name = self._conf.get_string(TableauDashboardAuth.TABLEAU_ACCESS_TOKEN_NAME)
        self._access_token_secret = self._conf.get_string(TableauDashboardAuth.TABLEAU_ACCESS_TOKEN_SECRET)
        self._api_version = self._conf.get_string(TableauDashboardAuth.API_VERSION)
        self._site_name = self._conf.get_string(TableauDashboardAuth.SITE_NAME, '')
        self._api_base_url = self._conf.get_string(TableauDashboardAuth.API_BASE_URL)
        self._verify_request = self._conf.get(TableauDashboardAuth.VERIFY_REQUEST, None)

    @property
    def token(self) -> Optional[str]:
        if not self._token:
            self._token = self._authenticate()
        return self._token

    def _authenticate(self) -> str:
        """
        Queries the auth/signin endpoint for the given Tableau instance using a personal access token.
        The API version differs with your version of Tableau.
        See https://help.tableau.com/current/api/rest_api/en-us/REST/rest_api_concepts_versions.htm
        for details or ask your Tableau server administrator.
        """
        self._auth_url = f"{self._api_base_url}/api/{self._api_version}/auth/signin"

        payload = json.dumps({
            'credentials': {
                'personalAccessTokenName': self._access_token_name,
                'personalAccessTokenSecret': self._access_token_secret,
                'site': {
                    'contentUrl': self._site_name
                }
            }
        })
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        # verify = False is needed bypass occasional (valid) self-signed cert errors. TODO: actually fix it!!
        params = {
            'headers': headers
        }
        if self._verify_request is not None:
            params['verify'] = self._verify_request

        response_json = requests.post(url=self._auth_url, data=payload, **params).json()
        return response_json['credentials']['token']
