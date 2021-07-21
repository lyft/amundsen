# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import abc
from typing import Dict

from flask import Response


class BasePreviewClient(abc.ABC):
    @abc.abstractmethod
    def __init__(self) -> None:
        pass  # pragma: no cover

    @abc.abstractmethod
    def get_preview_data(self, params: Dict, optionalHeaders: Dict = None) -> Response:
        """
        Returns a Response object, where the response data represents a json object
        with the preview data accessible on 'preview_data' key. The preview data should
        match amundsen_application.models.preview_data.PreviewDataSchema
        """
        raise NotImplementedError  # pragma: no cover

    @abc.abstractmethod
    def get_feature_preview_data(self, params: Dict, optionalHeaders: Dict = None) -> Response:
        """
        Returns a Response object, where the response data represents a json object
        with the preview data accessible on 'preview_data' key. The preview data should
        match amundsen_application.models.preview_data.PreviewDataSchema
        """
        raise NotImplementedError  # pragma: no cover
