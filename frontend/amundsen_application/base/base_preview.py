# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from abc import ABCMeta, abstractmethod


class BasePreview(metaclass=ABCMeta):
    """
    A Preview interface for other product to implement. For example, see ModePreview.
    """

    @abstractmethod
    def get_preview_image(self, *, uri: str) -> bytes:
        """
        Returns image bytes given URI
        :param uri:
        :return:
        :raises: FileNotFound when either Report is not available or Preview image is not available
        """
        pass
