# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import logging
from http import HTTPStatus
from typing import Any, Iterable, List, Mapping, Optional, Union

from flask_restful import Resource

from metadata_service.proxy import BaseProxy

LOGGER = logging.getLogger(__name__)


class BaseAPI(Resource):
    def __init__(self, schema: Any, str_type: str, client: BaseProxy) -> None:
        self.schema = schema
        self.client = client
        self.str_type = str_type
        self.allow_empty_upload = False

    def get(self, *, id: Optional[str] = None) -> Iterable[Union[Mapping, int, None]]:
        """
        Gets a single or multiple objects
        """
        return self.get_with_kwargs(id=id)

    def get_with_kwargs(self, *, id: Optional[str] = None, **kwargs: Optional[Any]) \
            -> Iterable[Union[Mapping, int, None]]:
        if id is not None:
            get_object = getattr(self.client, f'get_{self.str_type}')
            try:
                actual_id: Union[str, int] = int(id) if id.isdigit() else id
                object = get_object(id=actual_id, **kwargs)
                if object is not None:
                    return self.schema().dump(object), HTTPStatus.OK
                return None, HTTPStatus.NOT_FOUND
            except ValueError as e:
                return {'message': f'exception:{e}'}, HTTPStatus.BAD_REQUEST
        else:
            get_objects = getattr(self.client, f'get_{self.str_type}s')
            objects: List[Any] = get_objects()
            return self.schema().dump(objects, many=True), HTTPStatus.OK
