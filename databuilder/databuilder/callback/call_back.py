# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import abc
import logging
from typing import List, Optional

LOGGER = logging.getLogger(__name__)


class Callback(object, metaclass=abc.ABCMeta):
    """
    A callback interface that expected to fire "on_success" if the operation is successful, else "on_failure" if
    operation failed.
    """

    @abc.abstractmethod
    def on_success(self) -> None:
        """
        A call back method that will be called when operation is successful
        :return: None
        """
        pass

    @abc.abstractmethod
    def on_failure(self) -> None:
        """
        A call back method that will be called when operation failed
        :return: None
        """
        pass


def notify_callbacks(callbacks: List[Callback], is_success: bool) -> None:
    """
    A Utility method that notifies callback. If any callback fails it will still go through all the callbacks,
    and raise the last exception it experienced.

    :param callbacks:
    :param is_success:
    :return:
    """

    if not callbacks:
        LOGGER.info('No callbacks to notify')
        return

    LOGGER.info('Notifying callbacks')

    last_exception: Optional[Exception] = None
    for callback in callbacks:
        try:
            if is_success:
                callback.on_success()
            else:
                callback.on_failure()
        except Exception as e:
            LOGGER.exception('Failed while notifying callback')
            last_exception = e

    if last_exception:
        raise last_exception
