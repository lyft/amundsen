# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import functools

import json
import logging
import socket
from datetime import datetime, timezone, timedelta

from typing import Any, Dict, Callable
from flask import current_app as flask_app
from amundsen_common.log import action_log_callback
from amundsen_common.log.action_log_model import ActionLogParams

LOGGER = logging.getLogger(__name__)
EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)  # use POSIX epoch

# CONFIG KEY FOR caller_retrieval instance
CALLER_RETRIEVAL_INSTANCE_KEY = 'CALLER_RETRIEVAL_INSTANCE'


def action_logging(f: Callable[..., Any]) -> Any:
    """
    Decorates function to execute function at the same time triggering action logger callbacks.
    It will call action logger callbacks twice, one for pre-execution and the other one for post-execution.
    Action logger will be called with ActionLogParams

    :param f: function instance
    :return: wrapped function
    """
    @functools.wraps(f)
    def wrapper(
        *args: Any,
        **kwargs: Any
    ) -> Any:
        """
        An wrapper for api functions. It creates ActionLogParams based on the function name, positional arguments,
        and keyword arguments.

        :param args: A passthrough positional arguments.
        :param kwargs: A passthrough keyword argument
        """
        metrics = _build_metrics(f.__name__, *args, **kwargs)
        action_log_callback.on_pre_execution(ActionLogParams(**metrics))
        output = None
        try:
            output = f(*args, **kwargs)
            return output
        except Exception as e:
            metrics['error'] = e
            raise
        finally:
            metrics['end_epoch_ms'] = get_epoch_millisec()
            try:
                metrics['output'] = json.dumps(output)
            except Exception:
                metrics['output'] = output

            action_log_callback.on_post_execution(ActionLogParams(**metrics))

    if LOGGER.isEnabledFor(logging.DEBUG):
        LOGGER.debug('action has been logged')

    return wrapper


def get_epoch_millisec() -> int:
    return (datetime.now(timezone.utc) - EPOCH) // timedelta(milliseconds=1)


def _build_metrics(
    func_name: str,
    *args: Any,
    **kwargs: Any
) -> Dict[str, Any]:
    """
    Builds metrics dict from function args
    :param func_name:
    :param args:
    :param kwargs:
    :return: Dict that matches ActionLogParams variable
    """

    metrics = {
        'command': kwargs.get('command', func_name),
        'start_epoch_ms': get_epoch_millisec(),
        'host_name': socket.gethostname(),
        'pos_args_json': json.dumps(args),
        'keyword_args_json': json.dumps(kwargs),
    }  # type: Dict[str, Any]

    caller_retriever = flask_app.config.get(CALLER_RETRIEVAL_INSTANCE_KEY, '')
    if caller_retriever:
        metrics['user'] = caller_retriever.get_caller()
    else:
        metrics['user'] = 'UNKNOWN'

    return metrics
