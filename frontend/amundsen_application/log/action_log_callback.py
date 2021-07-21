# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

"""
An Action Logger module. Singleton pattern has been applied into this module
so that registered callbacks can be used all through the same python process.
"""

import logging
import sys
from typing import Callable, List  # noqa: F401

from pkg_resources import iter_entry_points

from amundsen_application.log.action_log_model import ActionLogParams

LOGGER = logging.getLogger(__name__)

__pre_exec_callbacks = []  # type: List[Callable]
__post_exec_callbacks = []  # type: List[Callable]


def register_pre_exec_callback(action_log_callback: Callable) -> None:
    """
    Registers more action_logger function callback for pre-execution. This function callback is expected to be called
    with keyword args. For more about the arguments that is being passed to the callback, refer to
    amundsen_application.log.action_log_model.ActionLogParams
    :param action_logger: An action logger callback function
    :return: None
    """
    LOGGER.debug("Adding {} to pre execution callback".format(action_log_callback))
    __pre_exec_callbacks.append(action_log_callback)


def register_post_exec_callback(action_log_callback: Callable) -> None:
    """
    Registers more action_logger function callback for post-execution. This function callback is expected to be
    called with keyword args. For more about the arguments that is being passed to the callback,
    amundsen_application.log.action_log_model.ActionLogParams
    :param action_logger: An action logger callback function
    :return: None
    """
    LOGGER.debug("Adding {} to post execution callback".format(action_log_callback))
    __post_exec_callbacks.append(action_log_callback)


def on_pre_execution(action_log_params: ActionLogParams) -> None:
    """
    Calls callbacks before execution.
    Note that any exception from callback will be logged but won't be propagated.
    :param kwargs:
    :return: None
    """
    LOGGER.debug("Calling callbacks: {}".format(__pre_exec_callbacks))
    for call_back_function in __pre_exec_callbacks:
        try:
            call_back_function(action_log_params)
        except Exception:
            logging.exception('Failed on pre-execution callback using {}'.format(call_back_function))


def on_post_execution(action_log_params: ActionLogParams) -> None:
    """
    Calls callbacks after execution. As it's being called after execution, it can capture most of fields in
    amundsen_application.log.action_log_model.ActionLogParams. Note that any exception from callback will be logged
    but won't be propagated.
    :param kwargs:
    :return: None
    """
    LOGGER.debug("Calling callbacks: {}".format(__post_exec_callbacks))
    for call_back_function in __post_exec_callbacks:
        try:
            call_back_function(action_log_params)
        except Exception:
            logging.exception('Failed on post-execution callback using {}'.format(call_back_function))


def logging_action_log(action_log_params: ActionLogParams) -> None:
    """
    An action logger callback that just logs the ActionLogParams that it receives.
    :param **kwargs keyword arguments
    :return: None
    """
    if LOGGER.isEnabledFor(logging.DEBUG):
        LOGGER.debug('logging_action_log: {}'.format(action_log_params))


def register_action_logs() -> None:
    """
    Retrieve declared action log callbacks from entry point where there are two groups that can be registered:
     1. "action_log.post_exec.plugin": callback for pre-execution
     2. "action_log.pre_exec.plugin": callback for post-execution
    :return: None
    """
    for entry_point in iter_entry_points(group='action_log.post_exec.plugin', name=None):
        print('Registering post_exec action_log entry_point: {}'.format(entry_point), file=sys.stderr)
        register_post_exec_callback(entry_point.load())

    for entry_point in iter_entry_points(group='action_log.pre_exec.plugin', name=None):
        print('Registering pre_exec action_log entry_point: {}'.format(entry_point), file=sys.stderr)
        register_pre_exec_callback(entry_point.load())


register_action_logs()
