# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from http import HTTPStatus
from typing import Iterable, List, Mapping, Optional, Union

from amundsen_common.models.popular_table import (PopularTable,
                                                  PopularTableSchema)
from flasgger import swag_from
from flask import request
from flask_restful import Resource

from metadata_service.proxy import get_proxy_client


class PopularTablesAPI(Resource):
    """
    PopularTables API
    """

    def __init__(self) -> None:
        self.client = get_proxy_client()

    @swag_from('swagger_doc/popular_tables_get.yml')
    def get(self, user_id: Optional[str] = None) -> Iterable[Union[Mapping, int, None]]:
        limit = request.args.get('limit', 10, type=int)
        popular_tables: List[PopularTable] = self.client.get_popular_tables(num_entries=limit,
                                                                            user_id=user_id)
        popular_tables_json: str = PopularTableSchema().dump(popular_tables, many=True)
        return {'popular_tables': popular_tables_json}, HTTPStatus.OK
