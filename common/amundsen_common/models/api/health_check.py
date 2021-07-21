# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import attr
from http import HTTPStatus
from typing import Any, Dict

from marshmallow3_annotations.ext.attrs import AttrsSchema

OK = 'ok'
FAIL = 'fail'
_ELIGIBLE_HEALTH_CHECKS = [OK, FAIL]
_HEALTH_CHECK_HTTP_STATUS_MAP = {
    OK: HTTPStatus.OK,
    FAIL: HTTPStatus.SERVICE_UNAVAILABLE
}


@attr.s(auto_attribs=True, kw_only=True)
class HealthCheck:
    status: str = attr.ib()
    checks: Dict[str, Any] = dict()

    @status.validator
    def vaildate_status(self, attribute: str, value: Any) -> None:
        if value not in _ELIGIBLE_HEALTH_CHECKS:
            raise ValueError(f"status must be one of {_ELIGIBLE_HEALTH_CHECKS}")

    def get_http_status(self) -> int:
        return _HEALTH_CHECK_HTTP_STATUS_MAP[self.status]

    def dict(self) -> Dict[str, Any]:
        return attr.asdict(self)


class HealthCheckSchema(AttrsSchema):
    class Meta:
        target = HealthCheck
        register_as_scheme = True
