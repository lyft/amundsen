# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0
from typing import (
    Iterator, Optional, Union,
)

from amundsen_rds.models import RDSModel
from amundsen_rds.models.column import ColumnStat as RDSColumnStat

from databuilder.models.graph_node import GraphNode
from databuilder.models.graph_relationship import GraphRelationship
from databuilder.models.graph_serializable import GraphSerializable
from databuilder.models.table_metadata import ColumnMetadata
from databuilder.models.table_serializable import TableSerializable


class TableColumnStats(GraphSerializable, TableSerializable):
    """
    Hive table stats model.
    Each instance represents one row of hive watermark result.
    """
    LABEL = 'Stat'
    KEY_FORMAT = '{db}://{cluster}.{schema}' \
                 '/{table}/{col}/{stat_type}/'
    STAT_Column_RELATION_TYPE = 'STAT_OF'
    Column_STAT_RELATION_TYPE = 'STAT'

    def __init__(self,
                 table_name: str,
                 col_name: str,
                 stat_name: str,
                 stat_val: str,
                 start_epoch: str,
                 end_epoch: str,
                 db: str = 'hive',
                 cluster: str = 'gold',
                 schema: str = None
                 ) -> None:
        if schema is None:
            self.schema, self.table = table_name.split('.')
        else:
            self.table = table_name
            self.schema = schema
        self.db = db
        self.col_name = col_name
        self.start_epoch = start_epoch
        self.end_epoch = end_epoch
        self.cluster = cluster
        self.stat_type = stat_name
        self.stat_val = str(stat_val)
        self._node_iter = self._create_node_iterator()
        self._relation_iter = self._create_relation_iterator()
        self._record_iter = self._create_record_iterator()

    def create_next_node(self) -> Optional[GraphNode]:
        # return the string representation of the data
        try:
            return next(self._node_iter)
        except StopIteration:
            return None

    def create_next_relation(self) -> Optional[GraphRelationship]:
        try:
            return next(self._relation_iter)
        except StopIteration:
            return None

    def create_next_record(self) -> Union[RDSModel, None]:
        try:
            return next(self._record_iter)
        except StopIteration:
            return None

    def get_table_stat_model_key(self) -> str:
        return TableColumnStats.KEY_FORMAT.format(db=self.db,
                                                  cluster=self.cluster,
                                                  schema=self.schema,
                                                  table=self.table,
                                                  col=self.col_name,
                                                  stat_type=self.stat_type)

    def get_col_key(self) -> str:
        # no cluster, schema info from the input
        return ColumnMetadata.COLUMN_KEY_FORMAT.format(db=self.db,
                                                       cluster=self.cluster,
                                                       schema=self.schema,
                                                       tbl=self.table,
                                                       col=self.col_name)

    def _create_node_iterator(self) -> Iterator[GraphNode]:
        """
        Create a table stat node
        :return:
        """
        node = GraphNode(
            key=self.get_table_stat_model_key(),
            label=TableColumnStats.LABEL,
            attributes={
                'stat_val': self.stat_val,
                'stat_type': self.stat_type,
                'start_epoch': self.start_epoch,
                'end_epoch': self.end_epoch,
            }
        )
        yield node

    def _create_relation_iterator(self) -> Iterator[GraphRelationship]:
        """
        Create relation map between table stat record with original hive table
        :return:
        """
        relationship = GraphRelationship(
            start_key=self.get_table_stat_model_key(),
            start_label=TableColumnStats.LABEL,
            end_key=self.get_col_key(),
            end_label=ColumnMetadata.COLUMN_NODE_LABEL,
            type=TableColumnStats.STAT_Column_RELATION_TYPE,
            reverse_type=TableColumnStats.Column_STAT_RELATION_TYPE,
            attributes={}
        )
        yield relationship

    def _create_record_iterator(self) -> Iterator[RDSModel]:
        record = RDSColumnStat(
            rk=self.get_table_stat_model_key(),
            stat_val=self.stat_val,
            stat_type=self.stat_type,
            start_epoch=self.start_epoch,
            end_epoch=self.end_epoch,
            column_rk=self.get_col_key()
        )
        yield record
