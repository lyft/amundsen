# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from datetime import datetime


class FileMetadata(object):

    def __init__(self,
                 path: str,
                 last_updated: datetime,
                 size: int
                 ) -> None:
        self.path = path
        self.last_updated = last_updated
        self.size = size

    def __repr__(self) -> str:
        return f'FileMetadata(path={self.path!r}, last_updated={self.last_updated!r}, size={self.size!r})'
