# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from typing import Dict, Tuple

from flasgger import swag_from
from flask_restful import Resource

from search_service.proxy import get_proxy_client


class HealthcheckAPI(Resource):
    """
    Healthcheck API
    """

    def __init__(self) -> None:
        self.client = get_proxy_client()

    @swag_from('swagger_doc/healthcheck.yml')
    def get(self) -> Tuple[Dict, int]:
        healt_check = self.client.health()
        return healt_check.dict(), healt_check.get_http_status()
