# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import logging
import textwrap
import time
from typing import (
    Any, Dict, Iterable,
)

import neo4j
from neo4j import GraphDatabase
from pyhocon import ConfigFactory, ConfigTree

from databuilder import Scoped
from databuilder.publisher.neo4j_csv_publisher import JOB_PUBLISH_TAG
from databuilder.task.base_task import Task

# A end point for Neo4j e.g: bolt://localhost:9999
NEO4J_END_POINT_KEY = 'neo4j_endpoint'
NEO4J_MAX_CONN_LIFE_TIME_SEC = 'neo4j_max_conn_life_time_sec'
NEO4J_USER = 'neo4j_user'
NEO4J_PASSWORD = 'neo4j_password'
NEO4J_ENCRYPTED = 'neo4j_encrypted'
"""NEO4J_ENCRYPTED is a boolean indicating whether to use SSL/TLS when connecting."""
NEO4J_VALIDATE_SSL = 'neo4j_validate_ssl'
"""NEO4J_VALIDATE_SSL is a boolean indicating whether to validate the server's SSL/TLS cert against system CAs."""

TARGET_NODES = "target_nodes"
TARGET_RELATIONS = "target_relations"
BATCH_SIZE = "batch_size"
DRY_RUN = "dry_run"
# Staleness max percentage. Safety net to prevent majority of data being deleted.
STALENESS_MAX_PCT = "staleness_max_pct"
# Staleness max percentage per LABEL/TYPE. Safety net to prevent majority of data being deleted.
STALENESS_PCT_MAX_DICT = "staleness_max_pct_dict"
# Using this milliseconds and published timestamp to determine staleness
MS_TO_EXPIRE = "milliseconds_to_expire"
MIN_MS_TO_EXPIRE = "minimum_milliseconds_to_expire"

DEFAULT_CONFIG = ConfigFactory.from_dict({BATCH_SIZE: 100,
                                          NEO4J_MAX_CONN_LIFE_TIME_SEC: 50,
                                          NEO4J_ENCRYPTED: True,
                                          NEO4J_VALIDATE_SSL: False,
                                          STALENESS_MAX_PCT: 5,
                                          TARGET_NODES: [],
                                          TARGET_RELATIONS: [],
                                          STALENESS_PCT_MAX_DICT: {},
                                          MIN_MS_TO_EXPIRE: 86400000,
                                          DRY_RUN: False})

LOGGER = logging.getLogger(__name__)

MARKER_VAR_NAME = 'marker'


class Neo4jStalenessRemovalTask(Task):
    """
    A Specific task that is to remove stale nodes and relations in Neo4j.
    It will use "published_tag" attribute assigned from Neo4jCsvPublisher and if "published_tag" is different from
    the one it is getting it from the config, it will regard the node/relation as stale.
    Not all resource is being published by Neo4jCsvPublisher and you can only set specific LABEL of the node or TYPE
    of relation to perform this deletion.

    """

    def __init__(self) -> None:
        pass

    def get_scope(self) -> str:
        return 'task.remove_stale_data'

    def init(self, conf: ConfigTree) -> None:
        conf = Scoped.get_scoped_conf(conf, self.get_scope()) \
            .with_fallback(conf) \
            .with_fallback(DEFAULT_CONFIG)
        self.target_nodes = set(conf.get_list(TARGET_NODES))
        self.target_relations = set(conf.get_list(TARGET_RELATIONS))
        self.batch_size = conf.get_int(BATCH_SIZE)
        self.dry_run = conf.get_bool(DRY_RUN)
        self.staleness_pct = conf.get_int(STALENESS_MAX_PCT)
        self.staleness_pct_dict = conf.get(STALENESS_PCT_MAX_DICT)

        if JOB_PUBLISH_TAG in conf and MS_TO_EXPIRE in conf:
            raise Exception(f'Cannot have both {JOB_PUBLISH_TAG} and {MS_TO_EXPIRE} in job config')

        self.ms_to_expire = None
        if MS_TO_EXPIRE in conf:
            self.ms_to_expire = conf.get_int(MS_TO_EXPIRE)
            if self.ms_to_expire < conf.get_int(MIN_MS_TO_EXPIRE):
                raise Exception(f'{MS_TO_EXPIRE} is too small')
            self.marker = self.ms_to_expire
        else:
            self.marker = conf.get_string(JOB_PUBLISH_TAG)

        trust = neo4j.TRUST_SYSTEM_CA_SIGNED_CERTIFICATES if conf.get_bool(NEO4J_VALIDATE_SSL) \
            else neo4j.TRUST_ALL_CERTIFICATES
        self._driver = \
            GraphDatabase.driver(conf.get_string(NEO4J_END_POINT_KEY),
                                 max_connection_life_time=conf.get_int(NEO4J_MAX_CONN_LIFE_TIME_SEC),
                                 auth=(conf.get_string(NEO4J_USER), conf.get_string(NEO4J_PASSWORD)),
                                 encrypted=conf.get_bool(NEO4J_ENCRYPTED),
                                 trust=trust)

    def run(self) -> None:
        """
        First, performs a safety check to make sure this operation would not delete more than a threshold where
        default threshold is 5%. Once it passes a safety check, it will first delete stale nodes, and then stale
        relations.
        :return:
        """
        self.validate()
        self._delete_stale_nodes()
        self._delete_stale_relations()

    def validate(self) -> None:
        """
        Validation method. Focused on limit the risk on deleting nodes and relations.
         - Check if deleted nodes will be within 10% of total nodes.
        :return:
        """
        self._validate_node_staleness_pct()
        self._validate_relation_staleness_pct()

    def _delete_stale_nodes(self) -> None:
        statement = textwrap.dedent("""
        MATCH (n:{{type}})
        WHERE {}
        WITH n LIMIT $batch_size
        DETACH DELETE (n)
        RETURN COUNT(*) as count;
        """)
        self._batch_delete(statement=self._decorate_staleness(statement), targets=self.target_nodes)

    def _decorate_staleness(self,
                            statement: str
                            ) -> str:
        """
        Append where clause to the Cypher statement depends on which field to be used to expire stale data.
        :param statement:
        :return:
        """
        if self.ms_to_expire:
            return statement.format(textwrap.dedent(f"""
            n.publisher_last_updated_epoch_ms < (timestamp() - ${MARKER_VAR_NAME})
            OR NOT EXISTS(n.publisher_last_updated_epoch_ms)"""))

        return statement.format(textwrap.dedent(f"""
        n.published_tag <> ${MARKER_VAR_NAME}
        OR NOT EXISTS(n.published_tag)"""))

    def _delete_stale_relations(self) -> None:
        statement = textwrap.dedent("""
        MATCH ()-[n:{{type}}]-()
        WHERE {}
        WITH n LIMIT $batch_size
        DELETE n
        RETURN count(*) as count;
        """)
        self._batch_delete(statement=self._decorate_staleness(statement), targets=self.target_relations)

    def _batch_delete(self,
                      statement: str,
                      targets: Iterable[str]
                      ) -> None:
        """
        Performing huge amount of deletion could degrade Neo4j performance. Therefore, it's taking batch deletion here.
        :param statement:
        :param targets:
        :return:
        """
        for t in targets:
            LOGGER.info('Deleting stale data of %s with batch size %i', t, self.batch_size)
            total_count = 0
            while True:
                results = self._execute_cypher_query(statement=statement.format(type=t),
                                                     param_dict={'batch_size': self.batch_size,
                                                                 MARKER_VAR_NAME: self.marker},
                                                     dry_run=self.dry_run)
                record = next(iter(results), None)
                count = record['count'] if record else 0
                total_count = total_count + count
                if count == 0:
                    break
            LOGGER.info('Deleted %i stale data of %s', total_count, t)

    def _validate_staleness_pct(self,
                                total_records: Iterable[Dict[str, Any]],
                                stale_records: Iterable[Dict[str, Any]],
                                types: Iterable[str]
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
                raise Exception(f'Staleness percentage of {type_str} is {stale_pct} %. '
                                f'Stopping due to over threshold {threshold} %')

    def _validate_node_staleness_pct(self) -> None:
        total_nodes_statement = textwrap.dedent("""
        MATCH (n)
        WITH DISTINCT labels(n) as node, count(*) as count
        RETURN head(node) as type, count
        """)

        stale_nodes_statement = textwrap.dedent("""
        MATCH (n)
        WHERE {}
        WITH DISTINCT labels(n) as node, count(*) as count
        RETURN head(node) as type, count
        """)

        stale_nodes_statement = textwrap.dedent(self._decorate_staleness(stale_nodes_statement))

        total_records = self._execute_cypher_query(statement=total_nodes_statement)
        stale_records = self._execute_cypher_query(statement=stale_nodes_statement,
                                                   param_dict={MARKER_VAR_NAME: self.marker})
        self._validate_staleness_pct(total_records=total_records,
                                     stale_records=stale_records,
                                     types=self.target_nodes)

    def _validate_relation_staleness_pct(self) -> None:
        total_relations_statement = textwrap.dedent("""
        MATCH ()-[r]-()
        RETURN type(r) as type, count(*) as count;
        """)

        stale_relations_statement = textwrap.dedent("""
        MATCH ()-[n]-()
        WHERE {}
        RETURN type(n) as type, count(*) as count
        """)

        stale_relations_statement = textwrap.dedent(self._decorate_staleness(stale_relations_statement))

        total_records = self._execute_cypher_query(statement=total_relations_statement)
        stale_records = self._execute_cypher_query(statement=stale_relations_statement,
                                                   param_dict={MARKER_VAR_NAME: self.marker})
        self._validate_staleness_pct(total_records=total_records,
                                     stale_records=stale_records,
                                     types=self.target_relations)

    def _execute_cypher_query(self,
                              statement: str,
                              param_dict: Dict[str, Any] = {},
                              dry_run: bool = False
                              ) -> Iterable[Dict[str, Any]]:
        LOGGER.info('Executing Cypher query: %s with params %s: ', statement, param_dict)

        if dry_run:
            LOGGER.info('Skipping for it is a dryrun')
            return []

        start = time.time()
        try:
            with self._driver.session() as session:
                return session.run(statement, **param_dict)

        finally:
            LOGGER.debug('Cypher query execution elapsed for %i seconds', time.time() - start)
