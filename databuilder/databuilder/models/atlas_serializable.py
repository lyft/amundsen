# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import abc
from typing import Union

from databuilder.models.atlas_entity import AtlasEntity
from databuilder.models.atlas_relationship import AtlasRelationship


class AtlasSerializable(object, metaclass=abc.ABCMeta):
    """
    A Serializable abstract class asks subclass to implement next node or
    next relation in dict form so that it can be serialized to CSV file.

    Any model class that needs to be pushed to a atlas should inherit this class.
    """

    @abc.abstractmethod
    def create_next_atlas_entity(self) -> Union[AtlasEntity, None]:
        """
        Creates Atlas entity the process that consumes this class takes the output
        serializes to atlas entity

        :return: a Atlas entity or None if no more records to serialize
        """
        raise NotImplementedError

    @abc.abstractmethod
    def create_next_atlas_relation(self) -> Union[AtlasRelationship, None]:
        """
        Creates AtlasRelationship the process that consumes this class takes the output
        serializes to the desired graph database.

        :return: a AtlasRelationship or None if no more record to serialize
        """
        raise NotImplementedError

    def _validate_atlas_entity(self, entity: AtlasEntity) -> None:
        entity_type, operation, relation, attributes = entity

        if entity_type is None:
            raise ValueError('Required header missing: entityType')

        if operation is None:
            raise ValueError('Required header missing: operation')

        if attributes is None:
            raise ValueError('Required header missing: attributes')

        if 'qualifiedName' not in attributes:
            raise ValueError('Attribute qualifiedName is missing')

    def _validate_atlas_relation(self, relation: AtlasRelationship) -> None:
        relation_type, entity_type_1, qualified_name_1, entity_type_2, qualified_name_2, _ = relation

        if relation_type is None:
            raise ValueError(f'Required header missing. Missing: {AtlasRelationship.relationshipType}')

        if entity_type_1 is None:
            raise ValueError(f'Required header missing. Missing: {AtlasRelationship.entityType1}')

        if qualified_name_1 is None:
            raise ValueError(f'Required header missing. Missing: {AtlasRelationship.entityQualifiedName1}')

        if entity_type_2 is None:
            raise ValueError(f'Required header missing. Missing: {AtlasRelationship.entityType2}')

        if qualified_name_2 is None:
            raise ValueError(f'Required header missing. Missing: {AtlasRelationship.entityQualifiedName2}')

    def next_atlas_entity(self) -> Union[AtlasEntity, None]:
        entity_dict = self.create_next_atlas_entity()
        if not entity_dict:
            return None

        self._validate_atlas_entity(entity_dict)
        return entity_dict

    def next_atlas_relation(self) -> Union[AtlasRelationship, None]:
        relation_dict = self.create_next_atlas_relation()
        if not relation_dict:
            return None

        self._validate_atlas_relation(relation_dict)
        return relation_dict
