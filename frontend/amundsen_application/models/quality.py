# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from marshmallow import Schema, fields


class TableQualityChecks:
    def __init__(self,
                 num_checks_success: int,
                 num_checks_failed: int,
                 num_checks_total: int,
                 external_url: str,
                 last_run_timestamp: int) -> None:
        self.num_checks_success = num_checks_success
        self.num_checks_failed = num_checks_failed
        self.num_checks_total = num_checks_total
        self.external_url = external_url
        self.last_run_timestamp = last_run_timestamp


class TableQualityChecksSchema(Schema):
    num_checks_success = fields.Integer(required=True)
    num_checks_failed = fields.Integer(required=True)
    num_checks_total = fields.Integer(required=True)
    external_url = fields.Str(required=True)
    last_run_timestamp = fields.Integer(required=False)
