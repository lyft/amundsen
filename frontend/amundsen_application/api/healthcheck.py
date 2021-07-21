# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0
import json
from typing import Dict, Tuple, Union

from amundsen_common.models.api import health_check
from flask import current_app as app

from amundsen_application.api.utils.request_utils import request_metadata, request_search


def run_healthcheck() -> Tuple[str, int]:
    search_url = app.config['SEARCHSERVICE_BASE'] + '/healthcheck'
    metadata_url = app.config['METADATASERVICE_BASE'] + '/healthcheck'
    health_services = {
        'search_service': {'url': search_url, 'request_func': request_search},
        'metadata_service': {'url': metadata_url, 'request_func': request_metadata},
    }

    all_health_checks: Dict[str, Union[str, Dict]] = {}
    health_status = health_check.OK
    for health_service, invoke_info in health_services.items():
        try:
            health_resp = invoke_info['request_func'](url=invoke_info['url'], method='GET')
            health = health_check.HealthCheck(**health_resp.json())
        except Exception:
            checks = {'status': 'Unable to connect.'}
            health = health_check.HealthCheck(status=health_check.FAIL, checks=checks)

        if health_status == health_check.FAIL or health.status == health_check.FAIL:
            health_status = health_check.FAIL

        all_health_checks[health_service] = health.checks

    frontend_health = health_check.HealthCheck(status=health_status, checks=all_health_checks)
    return json.dumps(frontend_health.dict()), frontend_health.get_http_status()
