# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from search_service.models.dashboard import Dashboard


def mock_proxy_results() -> Dashboard:
    return Dashboard(id='mode_dashboard',
                     uri='dashboard_uri',
                     cluster='gold',
                     group_name='mode_dashboard_group',
                     group_url='mode_dashboard_group_url',
                     product='mode',
                     name='mode_dashboard',
                     url='mode_dashboard_url',
                     description='test_dashboard',
                     last_successful_run_timestamp=1000)


def mock_json_response() -> dict:
    return {
        "id": 'mode_dashboard',
        "chart_names": [],
        "uri": 'dashboard_uri',
        "cluster": 'gold',
        "group_name": 'mode_dashboard_group',
        "group_url": 'mode_dashboard_group_url',
        "product": 'mode',
        "name": 'mode_dashboard',
        "url": 'mode_dashboard_url',
        "description": 'test_dashboard',
        "last_successful_run_timestamp": 1000,
    }


def default_json_response() -> dict:
    return {
        "chart_names": [],
        "uri": None,
        "cluster": None,
        "group_name": None,
        "group_url": None,
        "product": None,
        "name": None,
        "url": None,
        "description": None,
        "last_successful_run_timestamp": 0,
    }
