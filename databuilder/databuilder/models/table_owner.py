# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from typing import List, Union

from databuilder.models.owner import Owner
from databuilder.models.table_metadata import TableMetadata


class TableOwner(Owner):
    """
    Table owner model.
    """

    def __init__(self,
                 db_name: str,
                 schema: str,
                 table_name: str,
                 owners: Union[List, str],
                 cluster: str = 'gold',
                 ) -> None:
        self.start_label = TableMetadata.TABLE_NODE_LABEL
        self.start_key = f'{db_name}://{cluster}.{schema}/{table_name}'

        Owner.__init__(
            self,
            start_label=self.start_label,
            start_key=self.start_key,
            owner_emails=owners,
        )
