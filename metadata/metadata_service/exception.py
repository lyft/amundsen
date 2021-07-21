# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0


class NotFoundException(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
