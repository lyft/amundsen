# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import logging
from typing import (
    Any, Dict, Iterator, List, Union,
)

from pyhocon import ConfigTree
from simple_salesforce import Salesforce

from databuilder.extractor.base_extractor import Extractor
from databuilder.models.table_metadata import ColumnMetadata, TableMetadata

LOGGER = logging.getLogger(__name__)


class SalesForceExtractor(Extractor):
    """
    Extracts SalesForce objects
    """

    # CONFIG KEYS
    CLUSTER_KEY = 'cluster_key'
    SCHEMA_KEY = 'schema_key'
    DATABASE_KEY = 'database_key'
    OBJECT_NAMES_KEY = "object_names"
    USERNAME_KEY = "username"
    PASSWORD_KEY = "password"
    SECURITY_TOKEN_KEY = "security_token"

    def init(self, conf: ConfigTree) -> None:

        self._cluster: str = conf.get_string(SalesForceExtractor.CLUSTER_KEY, "gold")
        self._database: str = conf.get_string(SalesForceExtractor.DATABASE_KEY)
        self._schema: str = conf.get_string(SalesForceExtractor.SCHEMA_KEY)
        self._object_names: List[str] = conf.get_list(SalesForceExtractor.OBJECT_NAMES_KEY, [])

        self._client: Salesforce = Salesforce(
            username=conf.get_string(SalesForceExtractor.USERNAME_KEY),
            password=conf.get_string(SalesForceExtractor.PASSWORD_KEY),
            security_token=conf.get_string(SalesForceExtractor.SECURITY_TOKEN_KEY),
        )

        self._extract_iter: Union[None, Iterator] = None

    def extract(self) -> Union[TableMetadata, None]:
        if not self._extract_iter:
            self._extract_iter = self._get_extract_iter()
        try:
            return next(self._extract_iter)
        except StopIteration:
            return None

    def _get_extract_iter(self) -> Iterator[TableMetadata]:
        """
        Extract the TableMetaData for each SalesForce Object
        :return:
        """

        # Filter the sobjects if `OBJECT_NAMES_KEY` is set otherwise return all
        sobjects = [
            sobject
            for sobject in self._client.describe()["sobjects"]
            if (len(self._object_names) == 0 or sobject["name"] in self._object_names)
        ]

        for i, sobject in enumerate(sobjects):
            object_name = sobject["name"]
            logging.info(
                f"({i+1}/{len(sobjects)}) Extracting SalesForce object ({object_name})"
            )
            data = self._client.restful(path=f"sobjects/{object_name}/describe")
            yield self._extract_table_metadata(object_name=object_name, data=data)

    def _extract_table_metadata(
        self, object_name: str, data: Dict[str, Any]
    ) -> TableMetadata:
        # sort the fields by name because Amundsen requires a sort order for the columns and I did
        # not see one in the response
        fields = sorted(data["fields"], key=lambda x: x["name"])
        columns = [
            ColumnMetadata(
                name=f["name"],
                description=f["inlineHelpText"],
                col_type=f["type"],
                sort_order=i,
            )
            for i, f in enumerate(fields)
        ]
        return TableMetadata(
            database=self._database,
            cluster=self._cluster,
            schema=self._schema,
            name=object_name,
            # TODO: Can we extract table description / does it exist?
            description=None,
            columns=columns,
        )

    def get_scope(self) -> str:
        return 'extractor.salesforce_metadata'
