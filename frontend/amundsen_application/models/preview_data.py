# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from marshmallow import Schema, fields, EXCLUDE
from typing import List


class ColumnItem:
    def __init__(self, column_name: str = None, column_type: str = None) -> None:
        self.column_name = column_name
        self.column_type = column_type


class ColumnItemSchema(Schema):
    column_name = fields.Str()
    column_type = fields.Str()


class PreviewData:
    def __init__(self, columns: List = [], data: List = [], error_text: str = '') -> None:
        self.columns = columns
        self.data = data
        self.error_text = error_text


class PreviewDataSchema(Schema):
    columns = fields.Nested(ColumnItemSchema, many=True, unknown=EXCLUDE)
    data = fields.List(fields.Dict, many=True)
    error_text = fields.Str()
