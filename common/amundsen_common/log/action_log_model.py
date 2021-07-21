# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from typing import Any, Optional


class ActionLogParams(object):
    """
    Holds parameters for Action log
    """
    def __init__(
        self, *,
        command: str,
        start_epoch_ms: int,
        end_epoch_ms: Optional[int] = 0,
        user: str,
        host_name: str,
        pos_args_json: str,
        keyword_args_json: str,
        output: Any = None,
        error: Optional[Exception] = None
    ) -> None:
        self.command = command
        self.start_epoch_ms = start_epoch_ms
        self.end_epoch_ms = end_epoch_ms
        self.user = user
        self.host_name = host_name
        self.pos_args_json = pos_args_json
        self.keyword_args_json = keyword_args_json
        self.output = output
        self.error = error

    def __repr__(self) -> str:
        return 'ActionLogParams(command={!r}, start_epoch_ms={!r}, end_epoch_ms={!r}, user={!r}, ' \
               'host_name={!r}, pos_args_json={!r}, keyword_args_json={!r}, output={!r}, error={!r})'\
            .format(
                self.command,
                self.start_epoch_ms,
                self.end_epoch_ms,
                self.user,
                self.host_name,
                self.pos_args_json,
                self.keyword_args_json,
                self.output,
                self.error,
            )
