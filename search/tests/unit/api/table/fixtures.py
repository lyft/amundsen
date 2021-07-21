# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from search_service.models.table import Table
from search_service.models.tag import Tag


def mock_proxy_results() -> Table:
    return Table(id='world',
                 name='hello',
                 key='world',
                 description='des1',
                 cluster='clust',
                 database='db',
                 display_name=None,
                 schema='schema',
                 column_names=['col1', 'col2'],
                 tags=[Tag(tag_name='tag')],
                 badges=[Tag(tag_name='badge1')],
                 last_updated_timestamp=1568324871,
                 schema_description='schema description',
                 programmatic_descriptions=[])


def mock_default_proxy_results() -> Table:
    return Table(id='',
                 name='',
                 key='',
                 description='',
                 cluster='',
                 database='',
                 display_name='',
                 schema='',
                 column_names=[],
                 tags=[],
                 badges=[],
                 last_updated_timestamp=0,
                 schema_description='',
                 programmatic_descriptions=[])


def mock_json_response() -> dict:
    return {
        "id": "world",
        "name": "hello",
        "key": "world",
        "description": "des1",
        "display_name": None,
        "cluster": "clust",
        "database": "db",
        "schema": "schema",
        "column_names": ["col1", "col2"],
        "tags": [{'tag_name': 'tag'}],
        "badges": [{'tag_name': 'badge1'}],
        "last_updated_timestamp": 1568324871,
        "schema_description": 'schema description',
        'programmatic_descriptions': [],
        'total_usage': 0,
        'column_descriptions': None
    }


def default_json_response() -> dict:
    return {
        "id": '',
        "name": '',
        "key": '',
        "description": '',
        "cluster": '',
        "database": '',
        "display_name": '',
        "schema": '',
        "column_names": [],
        "tags": [],
        "badges": [],
        "last_updated_timestamp": 0,
        "schema_description": '',
        'programmatic_descriptions': [],
        'total_usage': 0,
        'column_descriptions': None
    }
