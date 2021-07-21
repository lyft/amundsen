# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import abc
import logging
import textwrap
from typing import (
    Dict, List, Optional, Tuple,
)

LOGGER = logging.getLogger(__name__)


class RelationPreprocessor(object, metaclass=abc.ABCMeta):
    """
    A Preprocessor for relations. Prior to publish Neo4j relations, RelationPreprocessor will be used for
    pre-processing.
    Neo4j Publisher will iterate through relation file and call preprocess_cypher to perform any pre-process requested.

    For example, if you need current job's relation data to be desired state, you can add delete statement in
    pre-process_cypher method. With preprocess_cypher defined, and with long transaction size, Neo4j publisher will
    atomically apply desired state.


    """

    def preprocess_cypher(self,
                          start_label: str,
                          end_label: str,
                          start_key: str,
                          end_key: str,
                          relation: str,
                          reverse_relation: str) -> Optional[Tuple[str, Dict[str, str]]]:
        """
        Provides a Cypher statement that will be executed before publishing relations.
        :param start_label:
        :param end_label:
        :param start_key:
        :param end_key:
        :param relation:
        :param reverse_relation:
        :return:
        """
        if self.filter(start_label=start_label,
                       end_label=end_label,
                       start_key=start_key,
                       end_key=end_key,
                       relation=relation,
                       reverse_relation=reverse_relation):
            return self.preprocess_cypher_impl(start_label=start_label,
                                               end_label=end_label,
                                               start_key=start_key,
                                               end_key=end_key,
                                               relation=relation,
                                               reverse_relation=reverse_relation)
        return None

    @abc.abstractmethod
    def preprocess_cypher_impl(self,
                               start_label: str,
                               end_label: str,
                               start_key: str,
                               end_key: str,
                               relation: str,
                               reverse_relation: str) -> Tuple[str, Dict[str, str]]:
        """
        Provides a Cypher statement that will be executed before publishing relations.
        :param start_label:
        :param end_label:
        :param relation:
        :param reverse_relation:
        :return: A Cypher statement
        """
        pass

    def filter(self,
               start_label: str,
               end_label: str,
               start_key: str,
               end_key: str,
               relation: str,
               reverse_relation: str) -> bool:
        """
        A method that filters pre-processing in record level. Returns True if it needs preprocessing, otherwise False.
        :param start_label:
        :param end_label:
        :param start_key:
        :param end_key:
        :param relation:
        :param reverse_relation:
        :return: bool. True if it needs preprocessing, otherwise False.
        """
        return True

    @abc.abstractmethod
    def is_perform_preprocess(self) -> bool:
        """
        A method for Neo4j Publisher to determine whether to perform pre-processing or not. Regard this method as a
        global filter.
        :return: True if you want to enable the pre-processing.
        """
        pass


class NoopRelationPreprocessor(RelationPreprocessor):

    def preprocess_cypher_impl(self,
                               start_label: str,
                               end_label: str,
                               start_key: str,
                               end_key: str,
                               relation: str,
                               reverse_relation: str) -> Tuple[str, Dict[str, str]]:
        pass

    def is_perform_preprocess(self) -> bool:
        return False


class DeleteRelationPreprocessor(RelationPreprocessor):
    """
    A Relation Pre-processor that delete relationship before Neo4jPublisher publishes relations.

    Example use case: Take an example of an external privacy service trying to push personal identifiable
    identification (PII) tag into Amundsen. It is fine to push set of PII tags for the first push, but it becomes a
    challenge when it comes to following update as external service does not know current PII state in Amundsen.

    The easy solution is for external service to know desired state (certain columns should have certain PII tags),
    and push that information.
    Now the challenge is how Amundsen apply desired state. This is where DeleteRelationPreprocessor comes into the
    picture. We can utilize DeleteRelationPreprocessor to let it delete certain relations in the job,
    and let Neo4jPublisher update to desired state. Should there be a small window (between delete and update) that
    Amundsen data is not complete, you can increase Neo4jPublisher's transaction size to make it atomic. However,
    note that you should not set transaction size too big as Neo4j uses memory to store transaction and this use case
    is proper for small size of batch job.
    """
    RELATION_MERGE_TEMPLATE = textwrap.dedent("""
    MATCH (n1:{start_label} {{key: $start_key }})-[r]-(n2:{end_label} {{key: $end_key }})
    {where_clause}
    WITH r LIMIT 2
    DELETE r
    RETURN count(*) as count;
    """)

    def __init__(self,
                 label_tuples: List[Tuple[str, str]] = None,
                 where_clause: str = '') -> None:
        super(DeleteRelationPreprocessor, self).__init__()
        self._label_tuples = set(label_tuples) if label_tuples else set()

        reversed_label_tuples = [(t2, t1) for t1, t2 in self._label_tuples]
        self._label_tuples.update(reversed_label_tuples)
        self._where_clause = where_clause

    def preprocess_cypher_impl(self,
                               start_label: str,
                               end_label: str,
                               start_key: str,
                               end_key: str,
                               relation: str,
                               reverse_relation: str) -> Tuple[str, Dict[str, str]]:
        """
        Provides DELETE Relation Cypher query on specific relation.
        :param start_label:
        :param end_label:
        :param start_key:
        :param end_key:
        :param relation:
        :param reverse_relation:
        :return:
        """

        if not (start_label or end_label or start_key or end_key):
            raise Exception(f'all labels and keys are required: {locals()}')

        params = {'start_key': start_key, 'end_key': end_key}
        return DeleteRelationPreprocessor.RELATION_MERGE_TEMPLATE.format(start_label=start_label,
                                                                         end_label=end_label,
                                                                         where_clause=self._where_clause), params

    def is_perform_preprocess(self) -> bool:
        return True

    def filter(self,
               start_label: str,
               end_label: str,
               start_key: str,
               end_key: str,
               relation: str,
               reverse_relation: str) -> bool:
        """
        If pair of labels is what client requested passed through label_tuples, filter will return True meaning that
        it needs to be pre-processed.
        :param start_label:
        :param end_label:
        :param start_key:
        :param end_key:
        :param relation:
        :param reverse_relation:
        :return: bool. True if it needs preprocessing, otherwise False.
        """
        if self._label_tuples and (start_label, end_label) not in self._label_tuples:
            return False

        return True
