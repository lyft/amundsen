# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import logging
from abc import ABCMeta, abstractmethod

from amundsen_application.base.base_preview import BasePreview
from amundsen_application.api.preview.dashboard.dashboard_preview.mode_preview import ModePreview

LOGGER = logging.getLogger(__name__)


class BasePreviewMethodFactory(metaclass=ABCMeta):

    @abstractmethod
    def get_instance(self, *, uri: str) -> BasePreview:
        """
        Provides an instance of BasePreview based on uri
        :param uri:
        :return:
        """
        pass


class DefaultPreviewMethodFactory(BasePreviewMethodFactory):

    def __init__(self) -> None:
        # Register preview clients here. Key: product, Value: BasePreview implementation
        self._object_map = {
            'mode': ModePreview()
        }
        LOGGER.info('Supported products: {}'.format(list(self._object_map.keys())))

    def get_instance(self, *, uri: str) -> BasePreview:
        product = self.get_product(uri=uri)

        if product in self._object_map:
            return self._object_map[product]

        raise NotImplementedError('Product {} is not supported'.format(product))

    def get_product(self, *, uri: str) -> str:
        return uri.split('_')[0]
