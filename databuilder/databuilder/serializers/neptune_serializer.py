# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from datetime import datetime
from typing import (
    Any, Dict, List, Optional,
)

from databuilder.models.graph_node import GraphNode
from databuilder.models.graph_relationship import GraphRelationship

NEPTUNE_HEADER_ID = "~id"
NEPTUNE_HEADER_LABEL = "~label"
NEPTUNE_RELATIONSHIP_HEADER_FROM = "~from"
NEPTUNE_RELATIONSHIP_HEADER_TO = "~to"


METADATA_KEY_PROPERTY_NAME = 'key'
METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT = '{name}:String(single)'.format(
    name=METADATA_KEY_PROPERTY_NAME
)

# last seen property names
NEPTUNE_LAST_EXTRACTED_AT_NODE_PROPERTY_NAME = "last_extracted_datetime"
NEPTUNE_LAST_EXTRACTED_AT_NODE_PROPERTY_NAME_BULK_LOADER_FORMAT = "{name}:Date(single)".format(
    name=NEPTUNE_LAST_EXTRACTED_AT_NODE_PROPERTY_NAME
)
NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME = "last_extracted_datetime"
NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT = "{name}:Date(single)".format(
    name=NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME
)
# Add a property showing where the the node or relationship comes from
NEPTUNE_CREATION_TYPE_NODE_PROPERTY_NAME = "creation_type"
NEPTUNE_CREATION_TYPE_NODE_PROPERTY_NAME_BULK_LOADER_FORMAT = "{name}:String(single)".format(
    name=NEPTUNE_CREATION_TYPE_NODE_PROPERTY_NAME
)
NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME = "creation_type"
NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT = "{name}:String".format(
    name=NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME
)

NEPTUNE_CREATION_TYPE_JOB = "job"


def convert_relationship(relationship: Optional[GraphRelationship]) -> List[Dict[str, Any]]:
    if relationship is None:
        return []

    if relationship.start_key == '' or relationship.end_key == '':
        return []

    neptune_start_key = "{label}:{key}".format(
        label=relationship.start_label,
        key=relationship.start_key
    )
    neptune_end_key = "{label}:{key}".format(
        label=relationship.end_label,
        key=relationship.end_key
    )
    relation_id = get_forward_relationship_id(relationship)
    relation_id_reverse = get_reverse_relationship_id(relationship)
    current_string_time = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
    forward_relationship_doc = {
        NEPTUNE_HEADER_ID: relation_id,
        METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: relation_id,
        NEPTUNE_RELATIONSHIP_HEADER_FROM: neptune_start_key,
        NEPTUNE_RELATIONSHIP_HEADER_TO: neptune_end_key,
        NEPTUNE_HEADER_LABEL: relationship.type,
        NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: current_string_time,
        NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB,

    }

    reverse_relationship_doc = {
        NEPTUNE_HEADER_ID: relation_id_reverse,
        METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: relation_id_reverse,
        NEPTUNE_RELATIONSHIP_HEADER_FROM: neptune_end_key,
        NEPTUNE_RELATIONSHIP_HEADER_TO: neptune_start_key,
        NEPTUNE_HEADER_LABEL: relationship.reverse_type,
        NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: current_string_time,
        NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB
    }

    for key, value in relationship.attributes.items():
        neptune_value_type = _get_neptune_type_for_value(value)
        doc_key = "{key_name}:{neptune_value_type}(single)".format(
            key_name=key,
            neptune_value_type=neptune_value_type
        )
        forward_relationship_doc[doc_key] = value
        reverse_relationship_doc[doc_key] = value

    return [
        forward_relationship_doc,
        reverse_relationship_doc
    ]


def get_forward_relationship_id(relationship: GraphRelationship) -> str:
    return "{label}:{from_vertex_label}:{from_vertex_id}_{to_vertex_label}:{to_vertex_id}".format(
        from_vertex_id=relationship.start_key,
        from_vertex_label=relationship.start_label,
        to_vertex_id=relationship.end_key,
        to_vertex_label=relationship.end_label,
        label=relationship.type
    )


def get_reverse_relationship_id(relationship: GraphRelationship) -> str:
    return "{label}:{from_vertex_label}:{from_vertex_id}_{to_vertex_label}:{to_vertex_id}".format(
        to_vertex_id=relationship.start_key,
        to_vertex_label=relationship.start_label,
        from_vertex_id=relationship.end_key,
        from_vertex_label=relationship.end_label,
        label=relationship.reverse_type
    )


def convert_node(node: Optional[GraphNode]) -> Dict[str, Any]:
    if node is None:
        return {}

    if not node.key:
        return {}

    current_string_time = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
    node_id = get_node_id(node)
    node_dict = {
        NEPTUNE_HEADER_ID: node_id,
        METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: node.key,
        NEPTUNE_HEADER_LABEL: node.label,
        NEPTUNE_LAST_EXTRACTED_AT_NODE_PROPERTY_NAME_BULK_LOADER_FORMAT: current_string_time,
        NEPTUNE_CREATION_TYPE_NODE_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB
    }

    for attr_key, attr_value in node.attributes.items():
        neptune_value_type = _get_neptune_type_for_value(attr_value)
        doc_key = "{key_name}:{neptune_value_type}(single)".format(
            key_name=attr_key,
            neptune_value_type=neptune_value_type
        )
        if doc_key not in node_dict:
            node_dict[doc_key] = attr_value

    return node_dict


def get_node_id(node: GraphNode) -> str:
    return "{label}:{key}".format(
        label=node.label,
        key=node.key
    )


def _get_neptune_type_for_value(value: Any) -> Optional[str]:
    if isinstance(value, str):
        return "String"
    elif isinstance(value, bool):
        return "Bool"
    elif isinstance(value, int):
        return "Long"
    elif isinstance(value, float):
        return "Double"

    return None
