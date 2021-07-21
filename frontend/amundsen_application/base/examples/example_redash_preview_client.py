# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import logging
import os

from typing import Dict, Optional

from amundsen_application.base.base_redash_preview_client import BaseRedashPreviewClient


LOGGER = logging.getLogger(__name__)


# Redash natively runs on port 5000, the same port as Amundsen.
# Make sure to update the running port to match your deployment!
DEFAULT_URL = 'http://localhost:5010'


# Update this mapping with your database.cluster and Redash query ID
SOURCE_DB_QUERY_MAP = {
    'snowflake.ca_covid': 1
}

# This example uses a common, system user, for the API key
REDASH_USER_API_KEY = os.environ.get('REDASH_USER_API_KEY', '')


def _build_db_cluster_key(params: Dict) -> str:
    _db = params.get('database')
    _cluster = params.get('cluster')

    db_cluster_key = f'{_db}.{_cluster}'
    return db_cluster_key


class RedashSimplePreviewClient(BaseRedashPreviewClient):
    def __init__(self,
                 *,
                 redash_host: str = DEFAULT_URL,
                 user_api_key: Optional[str] = REDASH_USER_API_KEY) -> None:
        super().__init__(redash_host=redash_host, user_api_key=user_api_key)

    def get_redash_query_id(self, params: Dict) -> Optional[int]:
        """
        Retrieves the query template that should be executed for the given
        source / database / schema / table combination.

        Redash Connections are generally unique to the source and database.
        For example, Snowflake account that has two databases would require two
        separate connections in Redash. This would require at least one query
        template per connection.

        The query ID can be found in the URL of the query when using the Redash GUI.
        """
        db_cluster_key = _build_db_cluster_key(params)
        return SOURCE_DB_QUERY_MAP.get(db_cluster_key)


class RedashComplexPreviewClient(BaseRedashPreviewClient):
    def __init__(self,
                 *,
                 redash_host: str = DEFAULT_URL,
                 user_api_key: Optional[str] = REDASH_USER_API_KEY) -> None:
        super().__init__(redash_host=redash_host, user_api_key=user_api_key)
        self.default_query_limit = 100
        self.max_redash_cache_age = 3600  # One Hour

    def _get_query_api_key(self, params: Dict) -> Optional[str]:
        if params.get('database') in ['redshift']:
            return os.environ.get('REDSHIFT_USER_API_KEY', '')
        return None

    def get_redash_query_id(self, params: Dict) -> Optional[int]:
        db_cluster_key = _build_db_cluster_key(params)
        return SOURCE_DB_QUERY_MAP.get(db_cluster_key)

    def get_select_fields(self, params: Dict) -> str:
        """
        Manually defining the dictionary in this function for readability
        """
        # These are sample values to show how table-level select clauses work
        field_select_vals = {
            'snowflake.ca_covid': {
                'open_data.case_demographics_age': (
                    "date, SUBSTR(age_group, 0, 2) || '******' as age_group, totalpositive, case_percent, ca_percent"
                ),
                'open_data.statewide_testing': 'date, tested'
            }
        }

        db_cluster_key = _build_db_cluster_key(params)
        schema_tbl_key = f"{params.get('schema')}.{params.get('tableName')}"

        # Always returns a value, defaults to '*' if nothing is defined
        return field_select_vals.get(db_cluster_key, {}).get(schema_tbl_key, '*')

    def get_where_clause(self, params: Dict) -> str:
        """
        MUST return the entire where clause, including the word "where"
        """
        where_vals = {
            'snowflake.ca_covid': {
                'open_data.case_demographics_age': "totalpositive < 120",
            }
        }

        db_cluster_key = _build_db_cluster_key(params)
        schema_tbl_key = f"{params.get('schema')}.{params.get('tableName')}"

        # Always returns a value, defaults to an empty string ('') if nothing is defined
        where_clause = where_vals.get(db_cluster_key, {}).get(schema_tbl_key, '')

        # Add the word where if a custom where clause is applied
        if where_clause:
            where_clause = f'WHERE {where_clause}'

        return where_clause
