# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from typing import (
    Any, Dict, List, Optional, Tuple,
)

from databuilder.models.atlas_entity import AtlasEntity
from databuilder.models.atlas_relationship import AtlasRelationship
from databuilder.utils.atlas import AtlasSerializedEntityFields, AtlasSerializedRelationshipFields


def serialize_entity(entity: Optional[AtlasEntity]) -> Dict[str, Any]:
    if entity is None:
        return {}

    entity_dict = {
        AtlasSerializedEntityFields.type_name: entity.typeName,
        AtlasSerializedEntityFields.operation: entity.operation,
        AtlasSerializedEntityFields.relationships: entity.relationships
    }
    for key, value in entity.attributes.items():
        entity_dict[key] = value
    return entity_dict


def serialize_relationship(relationship: Optional[AtlasRelationship]) -> Dict[str, Any]:
    if relationship is None:
        return {}

    relationship_dict = {
        AtlasSerializedRelationshipFields.relation_type: relationship.relationshipType,
        AtlasSerializedRelationshipFields.entity_type_1: relationship.entityType1,
        AtlasSerializedRelationshipFields.qualified_name_1: relationship.entityQualifiedName1,
        AtlasSerializedRelationshipFields.entity_type_2: relationship.entityType2,
        AtlasSerializedRelationshipFields.qualified_name_2: relationship.entityQualifiedName2,
    }
    for key, value in relationship.attributes.items():
        relationship_dict[key] = value

    return relationship_dict


def get_entity_attrs(attrs_mapping: List[Tuple[Any, Any]]) -> Dict:
    entity_attrs = {}
    for attr in attrs_mapping:
        attr_key, attr_value = attr
        entity_attrs[attr_key] = attr_value
    return entity_attrs


def add_entity_relationship(
    relationship_list: List[str], relation_attribute: str,
    relation_entity_type: str, related_object_qualified_name: str,
) -> List[str]:
    """
    relationship in form 'relation_attribute#relation_entity_type#qualified_name_of_related_object
    """
    relationship_list.append(AtlasSerializedEntityFields.relationships_kv_separator.join(
        (relation_attribute, relation_entity_type, related_object_qualified_name),
    ))
    return relationship_list


def get_entity_relationships(relationship_list: List[str]) -> str:
    return AtlasSerializedEntityFields \
        .relationships_separator \
        .join(relationship_list)
