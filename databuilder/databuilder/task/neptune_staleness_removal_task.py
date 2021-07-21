# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import logging
from datetime import datetime, timedelta
from typing import (
    Any, Callable, Dict, List, Optional, Tuple,
)

from gremlin_python.process import traversal
from gremlin_python.process.traversal import Column, T
from pyhocon import ConfigFactory, ConfigTree  # noqa: F401

from databuilder import Scoped
from databuilder.clients.neptune_client import NeptuneSessionClient
from databuilder.serializers.neptune_serializer import (
    NEPTUNE_CREATION_TYPE_JOB, NEPTUNE_CREATION_TYPE_NODE_PROPERTY_NAME,
    NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME, NEPTUNE_LAST_EXTRACTED_AT_NODE_PROPERTY_NAME,
    NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME,
)
from databuilder.task.base_task import Task  # noqa: F401

LOGGER = logging.getLogger(__name__)


class NeptuneStalenessRemovalTask(Task):
    """
    A Specific task that is to remove stale nodes and relations in Neptune.
    It will use "last_extracted_datetime" attribute assigned from FSNeptuneCSVLoader and if "creation_type" is type job
    the one it is getting it from the config, it will regard the node/relation as stale.
    Not all resources are being published by NeptuneCSVPublisher and you can only set specific LABEL of the node or TYPE
    of relation to perform this deletion.
    """

    NEPTUNE_HOST = 'neptune_host'
    AWS_REGION = 'aws_region'
    AWS_ACCESS_KEY = 'aws_access_key'
    AWS_SECRET_ACCESS_KEY = 'aws_secret_access_key'
    AWS_SESSION_TOKEN = 'aws_session_token'
    AWS_ARN = 'aws_arn'

    # Config keys
    TARGET_NODES = "target_nodes"
    TARGET_RELATIONS = "target_relations"
    DRY_RUN = "dry_run"
    # What is the property name that uniquely identifies each node and edge. Typically is T.id for neptune
    GRAPH_LABEL_ID_PROPERTY_NAME = "graph_label_id_property_name"
    # Staleness max percentage. Safety net to prevent majority of data being deleted.
    STALENESS_MAX_PCT = "staleness_max_pct"
    # Staleness max percentage per LABEL/TYPE. Safety net to prevent majority of data being deleted.
    STALENESS_PCT_MAX_DICT = "staleness_max_pct_dict"
    # Sets how old the nodes and relationships can be
    STALENESS_CUT_OFF_IN_SECONDS = "staleness_cut_off_in_seconds"
    DEFAULT_CONFIG = ConfigFactory.from_dict({
        GRAPH_LABEL_ID_PROPERTY_NAME: T.label,
        STALENESS_MAX_PCT: 5,
        TARGET_NODES: [],
        TARGET_RELATIONS: [],
        STALENESS_PCT_MAX_DICT: {},
        DRY_RUN: False
    })

    def get_scope(self) -> str:
        return 'task.remove_stale_data'

    def init(self, conf: ConfigTree) -> None:
        conf = Scoped.get_scoped_conf(conf, self.get_scope()) \
            .with_fallback(conf) \
            .with_fallback(NeptuneStalenessRemovalTask.DEFAULT_CONFIG)
        self.target_nodes = list(set(conf.get_list(NeptuneStalenessRemovalTask.TARGET_NODES)))
        self.target_relations = list(set(conf.get_list(NeptuneStalenessRemovalTask.TARGET_RELATIONS)))
        self.dry_run = conf.get_bool(NeptuneStalenessRemovalTask.DRY_RUN)
        self.staleness_pct = conf.get_int(NeptuneStalenessRemovalTask.STALENESS_MAX_PCT)
        self.staleness_pct_dict = conf.get(NeptuneStalenessRemovalTask.STALENESS_PCT_MAX_DICT)
        self.graph_label_id = conf.get(NeptuneStalenessRemovalTask.GRAPH_LABEL_ID_PROPERTY_NAME)
        self.staleness_cut_off_in_seconds = conf.get_int(NeptuneStalenessRemovalTask.STALENESS_CUT_OFF_IN_SECONDS)
        self.cutoff_datetime = datetime.utcnow() - timedelta(seconds=self.staleness_cut_off_in_seconds)
        self.gremlin_client = NeptuneSessionClient()
        gremlin_client_conf = Scoped.get_scoped_conf(conf, self.gremlin_client.get_scope())
        self.gremlin_client.init(gremlin_client_conf)

    def run(self) -> None:
        """
        First, performs a safety check to make sure this operation would not delete more than a threshold where
        default threshold is 5%. Once it passes a safety check, it will first delete stale nodes, and then stale
        relations.
        :return:
        """
        self.validate()
        if self.dry_run:
            return
        self._delete_stale_relations()
        self._delete_stale_nodes()

    def validate(self) -> None:
        """
        Validation method. Focused on limit the risk on deleting nodes and relations.
         - Check if deleted nodes will be within 5% of total nodes.
        """
        self._validate_node_staleness_pct()
        self._validate_relation_staleness_pct()

    def _delete_stale_nodes(self) -> None:
        filter_properties = [
            (NEPTUNE_CREATION_TYPE_NODE_PROPERTY_NAME, NEPTUNE_CREATION_TYPE_JOB, traversal.eq),
            (NEPTUNE_LAST_EXTRACTED_AT_NODE_PROPERTY_NAME, self.cutoff_datetime, traversal.lt)
        ]
        self.gremlin_client.delete_nodes(
            filter_properties=filter_properties,
            node_labels=list(self.target_nodes)
        )

    def _delete_stale_relations(self) -> None:
        filter_properties = [
            (NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME, NEPTUNE_CREATION_TYPE_JOB, traversal.eq),
            (NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME, self.cutoff_datetime, traversal.lt),
        ]

        self.gremlin_client.delete_edges(
            filter_properties=filter_properties,
            edge_labels=list(self.target_relations)
        )

    def _validate_staleness_pct(
            self,
            total_records: List[Dict[str, Any]],
            stale_records: List[Dict[str, Any]],
            types: List[str]
    ) -> None:
        total_count_dict = {record['type']: int(record['count']) for record in total_records}

        for record in stale_records:
            type_str = record['type']
            if type_str not in types:
                continue

            stale_count = record['count']
            if stale_count == 0:
                continue

            node_count = total_count_dict[type_str]
            stale_pct = stale_count * 100 / node_count

            threshold = self.staleness_pct_dict.get(type_str, self.staleness_pct)
            if stale_pct >= threshold:
                raise Exception('Staleness percentage of {} is {} %. Stopping due to over threshold {} %'
                                .format(type_str, stale_pct, threshold))

            LOGGER.info(
                'Will be dropping {stale_count} {record_type} records or {stale_pct}% of {record_type} data'.format(
                    stale_count=stale_count,
                    record_type=type_str,
                    stale_pct=stale_pct
                )
            )

    def _validate_node_staleness_pct(self) -> None:
        total_records = self.get_number_of_nodes_grouped_by_label()
        filter_properties = [
            (NEPTUNE_CREATION_TYPE_NODE_PROPERTY_NAME, NEPTUNE_CREATION_TYPE_JOB, traversal.eq),
            (NEPTUNE_LAST_EXTRACTED_AT_NODE_PROPERTY_NAME, self.cutoff_datetime, traversal.lt)
        ]
        stale_records = self.get_number_of_nodes_grouped_by_label(
            filter_properties=filter_properties
        )
        self._validate_staleness_pct(
            total_records=total_records,
            stale_records=stale_records,
            types=self.target_nodes
        )

    def get_number_of_nodes_grouped_by_label(
            self,
            filter_properties: Optional[List[Tuple[str, Any, Callable]]] = None
    ) -> List[Dict[str, Any]]:
        if filter_properties is None:
            filter_properties = []
        tx = self.gremlin_client.get_graph().V()
        tx = NeptuneSessionClient.filter_traversal(tx, filter_properties)
        tx = tx.groupCount().by(self.graph_label_id).unfold()
        tx = tx.project('type', 'count')
        tx = tx.by(Column.keys)
        tx = tx.by(Column.values)
        return tx.toList()

    def get_number_of_edges_grouped_by_label(
            self,
            filter_properties: Optional[List[Tuple[str, Any, Callable]]] = None
    ) -> List[Dict]:
        if filter_properties is None:
            filter_properties = []
        tx = self.gremlin_client.get_graph().E()
        tx = NeptuneSessionClient.filter_traversal(tx, filter_properties)
        tx = tx.groupCount().by(self.graph_label_id).unfold()
        tx = tx.project('type', 'count')
        tx = tx.by(Column.keys)
        tx = tx.by(Column.values)
        return tx.toList()

    def _validate_relation_staleness_pct(self) -> None:
        total_records = self.get_number_of_edges_grouped_by_label()
        filter_properties = [
            (NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME, NEPTUNE_CREATION_TYPE_JOB, traversal.eq),
            (NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME, self.cutoff_datetime, traversal.lt)
        ]
        stale_records = self.get_number_of_edges_grouped_by_label(
            filter_properties=filter_properties
        )
        self._validate_staleness_pct(
            total_records=total_records,
            stale_records=stale_records,
            types=self.target_relations
        )
