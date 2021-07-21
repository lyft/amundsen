# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from search_service.models.feature import Feature


def mock_json_response() -> dict:
    return {
        'id': '123aaabbb',
        'feature_group': 'group1',
        'feature_name': 'name1',
        'version': 'v2',
        'key': 'group1/name1/v2',
        'total_usage': 42,
        'status': 'active',
        'entity': 'listing',
        'description': 'some description',
        'availability': ['hive', 'postgres'],
        'badges': [{'tag_name': 'badge1'}, {'tag_name': 'badge2'}],
        'tags': [{'tag_name': 'tag1'}, {'tag_name': 'tag2'}],
        'last_updated_timestamp': 1568324871,
    }


def mock_proxy_results() -> Feature:
    return Feature(**mock_json_response())
