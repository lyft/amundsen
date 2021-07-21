# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import logging
from random import randint
from time import sleep
from typing import Callable, Optional, TypeVar

LOGGER = logging.getLogger(__name__)

X = TypeVar('X')


def checkNotNone(x: Optional[X], *, message: str = 'is None') -> X:
    """
    >>> checkNotNone('a string')
    'a string'
    >>> checkNotNone(31337)
    31337
    >>> checkNotNone('')
    ''
    >>> checkNotNone(False)
    False
    >>> checkNotNone({})
    {}
    >>> checkNotNone(None)
    ....
    >>> checkNotNone(None, message='thing is None')
    ...
    """
    if x is None:
        raise RuntimeError(message)
    return x


V = TypeVar('V')
K = TypeVar('K')


def make_wait_exponential_with_jitter(base: int, jitter: int) -> Callable[[int], int]:
    def wait(retry: int) -> int:
        assert retry > 0
        return 10**retry + randint(0, jitter)
    return wait


CallableV = TypeVar('CallableV')


def retrying(callable: Callable[[], CallableV], *,
             is_retryable: Callable[[Exception], bool],
             maximum_number_of_retries: int = 4,
             wait_millis: Callable[[int], int] = make_wait_exponential_with_jitter(10, 20)) -> CallableV:
    assert maximum_number_of_retries >= 0, f'maximum_number_of_retries ({maximum_number_of_retries}) must be >= 0!'
    retry = 0
    while True:
        try:
            return callable()
        except Exception as e:
            retry += 1
            try:
                if not is_retryable(e):
                    LOGGER.info(f'exception {e} is not retryable')
                elif retry > maximum_number_of_retries:
                    LOGGER.info(f'retry = {retry} exceeds {maximum_number_of_retries}')
                else:
                    millis = wait_millis(retry)
                    LOGGER.info(f'waiting {millis}ms on retry {retry} of {maximum_number_of_retries}')
                    sleep(millis / 1000)
                    continue
            except Exception as e2:
                # ignore this, assume our exception is not retryable
                LOGGER.warning(f'got exception {e2} while handling original exception {e}')
            raise  # the original exception
    raise RuntimeError(f'we should never get here')
