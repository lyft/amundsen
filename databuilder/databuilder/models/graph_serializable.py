# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import abc
from typing import Union  # noqa: F401

from databuilder.models.graph_node import GraphNode
from databuilder.models.graph_relationship import GraphRelationship

NODE_KEY = 'KEY'
NODE_LABEL = 'LABEL'

RELATION_START_KEY = 'START_KEY'
RELATION_START_LABEL = 'START_LABEL'
RELATION_END_KEY = 'END_KEY'
RELATION_END_LABEL = 'END_LABEL'
RELATION_TYPE = 'TYPE'
RELATION_REVERSE_TYPE = 'REVERSE_TYPE'


class GraphSerializable(object, metaclass=abc.ABCMeta):
    """
    A Serializable abstract class asks subclass to implement next node or
    next relation in dict form so that it can be serialized to CSV file.

    Any model class that needs to be pushed to a graph database should inherit this class.
    """

    def __init__(self) -> None:
        pass

    @abc.abstractmethod
    def create_next_node(self) -> Union[GraphNode, None]:
        """
        Creates GraphNode the process that consumes this class takes the output
        serializes to the desired graph database.

        :return: a GraphNode or None if no more records to serialize
        """
        raise NotImplementedError

    @abc.abstractmethod
    def create_next_relation(self) -> Union[GraphRelationship, None]:
        """
        Creates GraphRelationship the process that consumes this class takes the output
        serializes to the desired graph database.

        :return: a GraphRelationship or None if no more record to serialize
        """
        raise NotImplementedError

    def next_node(self) -> Union[GraphNode, None]:
        node_dict = self.create_next_node()
        if not node_dict:
            return None

        self._validate_node(node_dict)
        return node_dict

    def next_relation(self) -> Union[GraphRelationship, None]:
        relation_dict = self.create_next_relation()
        if not relation_dict:
            return None

        self._validate_relation(relation_dict)
        return relation_dict

    def _validate_node(self, node: GraphNode) -> None:
        node_id, node_label, _ = node

        if node_id is None:
            raise RuntimeError('Required header missing. Required attributes id and label , Missing: id')

        if node_label is None:
            raise RuntimeError('Required header missing. Required attributes id and label , Missing: label')

        self._validate_label_value(node_label)

    def _validate_relation(self, relation: GraphRelationship) -> None:
        self._validate_label_value(relation.start_label)
        self._validate_label_value(relation.end_label)
        self._validate_relation_type_value(relation.type)
        self._validate_relation_type_value(relation.reverse_type)

    def _validate_relation_type_value(self, value: str) -> None:
        if not value.isupper():
            raise RuntimeError(f'TYPE needs to be upper case: {value}')

    def _validate_label_value(self, value: str) -> None:
        if not value.istitle():
            raise RuntimeError(f'LABEL should only have upper case character on its first one: {value}')
