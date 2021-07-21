# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from typing import (
    Iterator, List, Tuple, Union,
)

from amundsen_rds.models import RDSModel
from amundsen_rds.models.table import TableWatermark as RDSTableWatermark

from databuilder.models.graph_node import GraphNode
from databuilder.models.graph_relationship import GraphRelationship
from databuilder.models.graph_serializable import GraphSerializable
from databuilder.models.table_serializable import TableSerializable


class Watermark(GraphSerializable, TableSerializable):
    """
    Table watermark result model.
    Each instance represents one row of table watermark result.
    """
    LABEL = 'Watermark'
    KEY_FORMAT = '{database}://{cluster}.{schema}' \
                 '/{table}/{part_type}/'
    WATERMARK_TABLE_RELATION_TYPE = 'BELONG_TO_TABLE'
    TABLE_WATERMARK_RELATION_TYPE = 'WATERMARK'

    def __init__(self,
                 create_time: str,
                 database: str,
                 schema: str,
                 table_name: str,
                 part_name: str,
                 part_type: str = 'high_watermark',
                 cluster: str = 'gold',
                 ) -> None:
        self.create_time = create_time
        self.database = database
        self.schema = schema
        self.table = table_name
        self.parts: List[Tuple[str, str]] = []

        if '=' not in part_name:
            raise Exception('Only partition table has high watermark')

        # currently we don't consider nested partitions
        idx = part_name.find('=')
        name, value = part_name[:idx], part_name[idx + 1:]
        self.parts = [(name, value)]
        self.part_type = part_type
        self.cluster = cluster
        self._node_iter = self._create_node_iterator()
        self._relation_iter = self._create_relation_iterator()
        self._record_iter = self._create_next_record()

    def create_next_node(self) -> Union[GraphNode, None]:
        # return the string representation of the data
        try:
            return next(self._node_iter)
        except StopIteration:
            return None

    def create_next_relation(self) -> Union[GraphRelationship, None]:
        try:
            return next(self._relation_iter)
        except StopIteration:
            return None

    def create_next_record(self) -> Union[RDSModel, None]:
        try:
            return next(self._record_iter)
        except StopIteration:
            return None

    def get_watermark_model_key(self) -> str:
        return Watermark.KEY_FORMAT.format(database=self.database,
                                           cluster=self.cluster,
                                           schema=self.schema,
                                           table=self.table,
                                           part_type=self.part_type)

    def get_metadata_model_key(self) -> str:
        return f'{self.database}://{self.cluster}.{self.schema}/{self.table}'

    def _create_node_iterator(self) -> Iterator[GraphNode]:
        """
        Create watermark nodes
        :return:
        """
        for part in self.parts:
            part_node = GraphNode(
                key=self.get_watermark_model_key(),
                label=Watermark.LABEL,
                attributes={
                    'partition_key': part[0],
                    'partition_value': part[1],
                    'create_time': self.create_time
                }
            )
            yield part_node

    def _create_relation_iterator(self) -> Iterator[GraphRelationship]:
        """
        Create relation map between watermark record with original table
        :return:
        """
        relation = GraphRelationship(
            start_key=self.get_watermark_model_key(),
            start_label=Watermark.LABEL,
            end_key=self.get_metadata_model_key(),
            end_label='Table',
            type=Watermark.WATERMARK_TABLE_RELATION_TYPE,
            reverse_type=Watermark.TABLE_WATERMARK_RELATION_TYPE,
            attributes={}
        )
        yield relation

    def _create_next_record(self) -> Iterator[RDSModel]:
        """
        Create watermark records
        """
        for part in self.parts:
            part_record = RDSTableWatermark(
                rk=self.get_watermark_model_key(),
                partition_key=part[0],
                partition_value=part[1],
                create_time=self.create_time,
                table_rk=self.get_metadata_model_key()
            )
            yield part_record
