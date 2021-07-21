# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import logging
from threading import Lock
from typing import (  # noqa: F401
    Any, Callable, Dict,
)

from flask import current_app
from statsd import StatsClient

from search_service import config

LOGGER = logging.getLogger(__name__)

_STATSD_POOL = {}  # type: Dict[str, StatsClient]
_STATSD_POOL_LOCK = Lock()


def timer_with_counter(f: Callable) -> Any:
    """
    A function decorator that adds statsd timer and statsd counter on success or fail
    statsd prefix will is from the fuction's module and metric name is from function name itself.
    Note that config.STATS needs to be True to emit metrics

    e.g: decorating function neo4j_proxy,get_table will emit:
      - metadata_service.proxy.neo4j_proxy.get_table.success.count
      - metadata_service.proxy.neo4j_proxy.get_table.fail.count
      - metadata_service.proxy.neo4j_proxy.get_table.timer

    More information on statsd: https://statsd.readthedocs.io/en/v3.2.1/index.html
    For statsd daemon not following default settings, refer to doc above to configure environment variables

    :param f:
    """
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        statsd_client = _get_statsd_client(prefix=f.__module__)
        if not statsd_client:
            return f(*args, **kwargs)

        with statsd_client.timer(f.__name__):
            if LOGGER.isEnabledFor(logging.DEBUG):
                LOGGER.debug('Calling function with emitting statsd metrics on prefix {}'.format(f.__name__))
            try:
                result = f(*args, **kwargs)
                statsd_client.incr('{}.success'.format(f.__name__))
                return result
            except Exception as e:
                statsd_client.incr('{}.fail'.format(f.__name__))
                raise e

    return wrapper


def _get_statsd_client(*, prefix: str) -> StatsClient:
    """
    Object pool method that reuse already created StatsClient based on prefix
    :param prefix:
    """
    if not current_app.config[config.STATS_FEATURE_KEY]:
        # return if stats feature is not enabled
        return None
    else:
        if prefix not in _STATSD_POOL:
            with _STATSD_POOL_LOCK:
                if prefix not in _STATSD_POOL:
                    LOGGER.info('Instantiate StatsClient with prefix {}'.format(prefix))
                    statsd_client = StatsClient(prefix=prefix)
                    _STATSD_POOL[prefix] = statsd_client
                    return statsd_client

        if LOGGER.isEnabledFor(logging.DEBUG):
            LOGGER.debug('Reuse StatsClient with prefix {}'.format(prefix))
        return _STATSD_POOL[prefix]
