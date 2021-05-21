# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import pandas
import logging
from os import listdir
from os.path import isfile, join
from typing import List

from apache_atlas.exceptions import AtlasServiceException
from apache_atlas.model.instance import AtlasEntity, AtlasEntitiesWithExtInfo, AtlasRelatedObjectId, AtlasObjectId
from apache_atlas.model.relationship import AtlasRelationship
from amundsen_common.utils.atlas import AtlasCommonParams, AtlasSerializedRelationshipFields, AtlasSerializedEntityFields, AtlasEntityOperation

from pyhocon import ConfigTree

from databuilder.publisher.base_publisher import Publisher

LOGGER = logging.getLogger(__name__)


class AtlasCSVPublisher(Publisher):
    # atlas client
    ATLAS_CLIENT = 'atlas_client'
    # A directory that contains CSV files for entities
    ENTITY_DIR_PATH = 'entity_files_directory'
    # A directory that contains CSV files for relationships
    RELATION_DIR_PATH = 'relation_files_directory'
    # atlas create entity batch size
    ATLAS_ENTITY_CREATE_BATCH_SIZE = 'batch_size'

    def __init__(self) -> None:
        super(AtlasCSVPublisher, self).__init__()

    def init(self, conf: ConfigTree) -> None:
        self._entity_files = self._list_files(conf, AtlasCSVPublisher.ENTITY_DIR_PATH)
        self._relationship_files = self._list_files(conf, AtlasCSVPublisher.RELATION_DIR_PATH)
        self._config = conf
        self._atlas_client = self._config.get(AtlasCSVPublisher.ATLAS_CLIENT)

    def _list_files(self, conf: ConfigTree, path_key: str) -> List[str]:
        """
        List files from directory
        :param conf:
        :param path_key:
        :return: List of file paths
        """
        if path_key not in conf:
            return []

        path = conf.get_string(path_key)
        return sorted([join(path, f) for f in listdir(path) if isfile(join(path, f))])

    def publish_impl(self) -> None:
        """
        Publishes Entities first and then Relations
        :return:
        """
        LOGGER.info('Creating entities using Entity files: %s', self._entity_files)
        for entity_file in self._entity_files:
            entities_to_create, entities_to_update = self._create_entity_instances(entity_file=entity_file)
            self._sync_entities_to_atlas(entities_to_create)
            self._update_entities(entities_to_update)

        LOGGER.info('Creating relations using relation files: %s', self._relationship_files)
        for relation_file in self._relationship_files:
            self._create_relations(relation_file=relation_file)

    def _update_entities(self, entities_to_update) -> None:
        """
        Go over the entities list , create atlas relationships instances and sync them with atlas
        :param entities_to_update:
        :return:
        """
        for entity_to_update in entities_to_update:
            existing_entity = self._atlas_client.entity.get_entity_by_attribute(
                entity_to_update.attributes[AtlasCommonParams.type_name],
                [(AtlasCommonParams.qualified_name, entity_to_update.attributes[AtlasCommonParams.qualified_name])]
            )
            existing_entity.entity.attributes.update(entity_to_update.attributes)
            try:
                self._atlas_client.entity.update_entity(existing_entity)
            except AtlasServiceException as e:
                LOGGER.error(f'Fail to update entity, {e}')

    def _create_relations(self, relation_file: str) -> None:
        """
        Go over the relation file, create atlas relationships instances and sync them with atlas
        :param relation_file:
        :return:
        """

        with open(relation_file, 'r', encoding='utf8') as relation_csv:
            for relation_record in pandas.read_csv(relation_csv, na_filter=False).to_dict(orient='records'):
                relation = self._create_relation(relation_record)
                try:
                    self._atlas_client.relationship.create_relationship(relation)
                except AtlasServiceException as e:
                    LOGGER.error(f'Fail to create atlas relationship {e}')
                except Exception as e:
                    LOGGER.error(e)

    def _render_unique_attributes(self, entity_type, qualified_name):
        """
        Render uniqueAttributes dict, this struct is needed to identify AtlasObjects
        :param entity_type:
        :param qualified_name:
        :return: rendered uniqueAttributes dict
        """
        return {AtlasCommonParams.type_name: entity_type, AtlasCommonParams.unique_attributes: {AtlasCommonParams.qualified_name: qualified_name}}

    def _get_atlas_related_object_id_by_qn(self, entity_type, qn) -> AtlasRelatedObjectId:
        return AtlasRelatedObjectId(attrs=self._render_unique_attributes(entity_type, qn))

    def _get_atlas_object_id_by_qn(self, entity_type, qn):
        return AtlasObjectId(attrs=self._render_unique_attributes(entity_type, qn))

    def _create_relation(self, relation_dict):
        """
        Go over the relation dictionary file and create atlas relationships instances
        :param relation_dict:
        :return:
        """

        relation = AtlasRelationship({AtlasCommonParams.type_name: relation_dict[AtlasSerializedRelationshipFields.relation_type]})
        relation.end1 = self._get_atlas_object_id_by_qn(relation_dict[AtlasSerializedRelationshipFields.entity_type_1],
                                                        relation_dict[AtlasSerializedRelationshipFields.qualified_name_1])
        relation.end2 = self._get_atlas_object_id_by_qn(relation_dict[AtlasSerializedRelationshipFields.entity_type_2],
                                                        relation_dict[AtlasSerializedRelationshipFields.qualified_name_2])

        return relation

    def _create_entity_instances(self, entity_file: str) -> List[AtlasEntity]:
        """
        Go over the entities file and try creating instances
        :param entity_file:
        :return:
        """
        entities_to_create = []
        entities_to_update = []
        with open(entity_file, 'r', encoding='utf8') as entity_csv:
            for entity_record in pandas.read_csv(entity_csv, na_filter=False).to_dict(orient='records'):
                if entity_record[AtlasSerializedEntityFields.operation] == AtlasEntityOperation.CREATE:
                    entities_to_create.append(self._create_entity_from_dict(entity_record))
                if entity_record[AtlasSerializedEntityFields.operation] == AtlasEntityOperation.UPDATE:
                    entities_to_update.append(self._create_entity_from_dict(entity_record))

        return entities_to_create, entities_to_update

    def _extract_entity_relations_details(self, relation_details):
        """
        Generate relation details from relation_attr#related_entity_type#related_qualified_name
        """
        relations = relation_details.split(AtlasSerializedEntityFields.relationships_separator)
        for relation in relations:
            relation_split = relation.split(AtlasSerializedEntityFields.relationships_kv_separator)
            yield relation_split[0], relation_split[1], relation_split[2]

    def _create_entity_from_dict(self, entity_dict) -> AtlasEntity:
        """
        Create atlas entity instance from dict
        :param entity_dict:
        :return: AtlasEntity
        """
        type_name = {AtlasCommonParams.type_name: entity_dict[AtlasCommonParams.type_name]}
        entity = AtlasEntity(type_name)
        entity.attributes = entity_dict
        relationships = entity_dict.get(AtlasSerializedEntityFields.relationships)
        if relationships:
            relations = dict()
            for relation_attr, rel_type, rel_qn in self._extract_entity_relations_details(relationships):
                related_obj = self._get_atlas_related_object_id_by_qn(rel_type, rel_qn)
                relations[relation_attr] = related_obj
            entity.relationshipAttributes = relations
        return entity

    def _chunks(self, lst):
        """
        Yield successive n-sized chunks from lst.
        :param lst:
        :return: chunks generator
        """
        n = self._config.get_int(AtlasCSVPublisher.ATLAS_ENTITY_CREATE_BATCH_SIZE)
        for i in range(0, len(lst), n):
            yield lst[i:i + n]

    def _sync_entities_to_atlas(self, entities):
        """
        Sync entities instances with atlas
        :param entities: list of entities
        :return:
        """
        entities_chunks = self._chunks(entities)
        for entity_chunk in entities_chunks:
            LOGGER.info(f'Syncing chunk of {len(entity_chunk)} entities with atlas')
            chunk = AtlasEntitiesWithExtInfo()
            chunk.entities = entity_chunk
            try:
                self._atlas_client.entity.create_entities(chunk)
            except AtlasServiceException as e:
                LOGGER.error(f'Error during entity syncing, {e}')

    def get_scope(self) -> str:
        return 'publisher.atlas_csv_publisher'
