# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from http import HTTPStatus
from typing import Iterable, Mapping, Union

from flasgger import swag_from
from flask_restful import Resource

from metadata_service.proxy import get_proxy_client


class Neo4jDetailAPI(Resource):
    """
    API to fetch system information for neo4j
    """

    def __init__(self) -> None:
        self.client = get_proxy_client()

    @swag_from('swagger_doc/neo4j/detail_get.yml')
    def get(self) -> Iterable[Union[Mapping, int, None]]:
        last_updated_ts = self.client.get_latest_updated_ts()
        if last_updated_ts is not None:
            return {'neo4j_latest_timestamp': int(last_updated_ts)}, HTTPStatus.OK
        else:
            return {'message': 'neo4j / es hasnt been updated / indexed.'}, HTTPStatus.NO_CONTENT


class StatisticsMetricsAPI(Resource):
    """
    API to fetch system statistic metrics from the database
    """

    def __init__(self) -> None:
        self.client = get_proxy_client()

    @swag_from('swagger_doc/system/statistics_get.yml')
    def get(self) -> Iterable[Union[Mapping, int, None]]:
        statistics = self.client.get_statistics()
        if statistics is not {}:
            return {'Statistics': statistics}, HTTPStatus.OK
        else:
            return {'message': 'There was an error with retreiving the metrics of Neo4j'}, HTTPStatus.NO_CONTENT
