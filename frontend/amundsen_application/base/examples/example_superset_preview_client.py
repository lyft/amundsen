# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import logging
import requests
import uuid

from requests import Response
from typing import Any, Dict  # noqa: F401

from amundsen_application.base.base_superset_preview_client import BaseSupersetPreviewClient

# 'main' is an existing default Superset database which serves for demo purposes
DEFAULT_DATABASE_MAP = {
    'main': 1,
}
DEFAULT_URL = 'http://localhost:8088/superset/sql_json/'


class SupersetPreviewClient(BaseSupersetPreviewClient):
    def __init__(self,
                 *,
                 database_map: Dict[str, int] = DEFAULT_DATABASE_MAP,
                 url: str = DEFAULT_URL) -> None:
        self.database_map = database_map
        self.headers = {}
        self.url = url

    def post_to_sql_json(self, *, params: Dict, headers: Dict) -> Response:
        """
        Returns the post response from Superset's `sql_json` endpoint
        """
        # Create the appropriate request data
        try:
            request_data = {}  # type: Dict[str, Any]

            # Superset's sql_json endpoint requires a unique client_id
            request_data['client_id'] = uuid.uuid4()

            # Superset's sql_json endpoint requires the id of the database that it will execute the query on
            database_name = 'main'  # OR params.get('database') in a real use case
            request_data['database_id'] = self.database_map.get(database_name, '')

            # Generate the sql query for the desired data preview content
            try:
                # 'main' is an existing default Superset schema which serves for demo purposes
                schema = 'main'  # OR params.get('schema') in a real use case

                # 'ab_role' is an existing default Superset table which serves for demo purposes
                table_name = 'ab_role'  # OR params.get('tableName') in a real use case

                request_data['sql'] = 'SELECT * FROM {schema}.{table} LIMIT 50'.format(schema=schema, table=table_name)
            except Exception as e:
                logging.error('Encountered error generating request sql: ' + str(e))
        except Exception as e:
            logging.error('Encountered error generating request data: ' + str(e))

        # Post request to Superset's `sql_json` endpoint
        return requests.post(self.url, data=request_data, headers=headers)
