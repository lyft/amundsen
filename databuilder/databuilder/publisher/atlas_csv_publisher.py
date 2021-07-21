# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0
import logging
from os import listdir
from os.path import isfile, join
from typing import (
    Any, Dict, Iterator, List, Tuple,
)

import pandas
from amundsen_common.utils.atlas import AtlasCommonParams, AtlasCommonTypes
from apache_atlas.exceptions import AtlasServiceException
from apache_atlas.model.glossary import (
    AtlasGlossary, AtlasGlossaryHeader, AtlasGlossaryTerm,
)
from apache_atlas.model.instance import (
    AtlasEntitiesWithExtInfo, AtlasEntity, AtlasObjectId, AtlasRelatedObjectId,
)
from apache_atlas.model.relationship import AtlasRelationship
from apache_atlas.model.typedef import AtlasClassificationDef, AtlasTypesDef
from pyhocon import ConfigTree

from databuilder.publisher.base_publisher import Publisher
from databuilder.types.atlas import AtlasEntityInitializer
from databuilder.utils.atlas import (
    AtlasRelationshipTypes, AtlasSerializedEntityFields, AtlasSerializedEntityOperation,
    AtlasSerializedRelationshipFields,
)

LOGGER = logging.getLogger(__name__)


class AtlasCSVPublisher(Publisher):
    # atlas client
    ATLAS_CLIENT = 'atlas_client'
    # A directory that contains CSV files for entities
    ENTITY_DIR_PATH = 'entity_files_directory'
    # A directory that contains CSV files for relationships
    RELATIONSHIP_DIR_PATH = 'relationship_files_directory'
    # atlas create entity batch size
    ATLAS_ENTITY_CREATE_BATCH_SIZE = 'batch_size'
    # whether entity types should be registered before data is synced to Atlas
    REGISTER_ENTITY_TYPES = 'register_entity_types'

    def __init__(self) -> None:
        super().__init__()

    def init(self, conf: ConfigTree) -> None:
        self._entity_files = self._list_files(conf, AtlasCSVPublisher.ENTITY_DIR_PATH)
        self._relationship_files = self._list_files(conf, AtlasCSVPublisher.RELATIONSHIP_DIR_PATH)
        self._config = conf
        self._atlas_client = self._config.get(AtlasCSVPublisher.ATLAS_CLIENT)
        self._register_entity_types = self._config.get_bool(AtlasCSVPublisher.REGISTER_ENTITY_TYPES, True)

        if self._register_entity_types:
            LOGGER.info('Registering Atlas Entity Types.')

            try:
                init = AtlasEntityInitializer(self._atlas_client)
                init.create_required_entities()

                LOGGER.info('Registered Atlas Entity Types.')
            except Exception:
                LOGGER.error('Failed to register Atlas Entity Types.', exc_info=True)

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
        return sorted(join(path, f) for f in listdir(path) if isfile(join(path, f)))

    def publish_impl(self) -> None:
        """
        Publishes Entities first and then Relations
        :return:
        """
        LOGGER.info('Creating entities using Entity files: %s', self._entity_files)
        for entity_file in self._entity_files:
            entities_to_create, entities_to_update, \
                glossary_terms_create, classifications_create = self._create_entity_instances(entity_file=entity_file)
            self._sync_entities_to_atlas(entities_to_create)
            self._update_entities(entities_to_update)
            self._create_glossary_terms(glossary_terms_create)
            self._create_classifications(classifications_create)

        LOGGER.info('Creating relations using relation files: %s', self._relationship_files)
        for relation_file in self._relationship_files:
            self._create_relations(relation_file=relation_file)

    def _update_entities(self, entities_to_update: List[AtlasEntity]) -> None:
        """
        Go over the entities list , create atlas relationships instances and sync them with atlas
        :param entities_to_update:
        :return:
        """
        for entity_to_update in entities_to_update:
            existing_entity = self._atlas_client.entity.get_entity_by_attribute(
                entity_to_update.attributes[AtlasCommonParams.type_name],
                [(AtlasCommonParams.qualified_name, entity_to_update.attributes[AtlasCommonParams.qualified_name])],
            )
            existing_entity.entity.attributes.update(entity_to_update.attributes)
            try:
                self._atlas_client.entity.update_entity(existing_entity)
            except AtlasServiceException:
                LOGGER.error('Fail to update entity', exc_info=True)

    def _create_relations(self, relation_file: str) -> None:
        """
        Go over the relation file, create atlas relationships instances and sync them with atlas
        :param relation_file:
        :return:
        """

        with open(relation_file, encoding='utf8') as relation_csv:
            for relation_record in pandas.read_csv(relation_csv, na_filter=False).to_dict(orient='records'):
                if relation_record[AtlasSerializedRelationshipFields.relation_type] == AtlasRelationshipTypes.tag:
                    self._assign_glossary_term(relation_record)
                    continue
                elif relation_record[AtlasSerializedRelationshipFields.relation_type] == AtlasRelationshipTypes.badge:
                    self._assign_classification(relation_record)
                    continue

                relation = self._create_relation(relation_record)
                try:
                    self._atlas_client.relationship.create_relationship(relation)
                except AtlasServiceException:
                    LOGGER.error('Fail to create atlas relationship', exc_info=True)
                except Exception as e:
                    LOGGER.error(e)

    def _render_unique_attributes(self, entity_type: str, qualified_name: str) -> Dict[Any, Any]:
        """
        Render uniqueAttributes dict, this struct is needed to identify AtlasObjects
        :param entity_type:
        :param qualified_name:
        :return: rendered uniqueAttributes dict
        """
        return {
            AtlasCommonParams.type_name: entity_type,
            AtlasCommonParams.unique_attributes: {
                AtlasCommonParams.qualified_name: qualified_name,
            },
        }

    def _get_atlas_related_object_id_by_qn(self, entity_type: str, qn: str) -> AtlasRelatedObjectId:
        return AtlasRelatedObjectId(attrs=self._render_unique_attributes(entity_type, qn))

    def _get_atlas_object_id_by_qn(self, entity_type: str, qn: str) -> AtlasObjectId:
        return AtlasObjectId(attrs=self._render_unique_attributes(entity_type, qn))

    def _create_relation(self, relation_dict: Dict[str, str]) -> AtlasRelationship:
        """
        Go over the relation dictionary file and create atlas relationships instances
        :param relation_dict:
        :return:
        """

        relation = AtlasRelationship(
            {AtlasCommonParams.type_name: relation_dict[AtlasSerializedRelationshipFields.relation_type]},
        )
        relation.end1 = self._get_atlas_object_id_by_qn(
            relation_dict[AtlasSerializedRelationshipFields.entity_type_1],
            relation_dict[AtlasSerializedRelationshipFields.qualified_name_1],
        )
        relation.end2 = self._get_atlas_object_id_by_qn(
            relation_dict[AtlasSerializedRelationshipFields.entity_type_2],
            relation_dict[AtlasSerializedRelationshipFields.qualified_name_2],
        )

        return relation

    def _create_entity_instances(self, entity_file: str) -> Tuple[List[AtlasEntity], List[AtlasEntity],
                                                                  List[Dict], List[Dict]]:
        """
        Go over the entities file and try creating instances
        :param entity_file:
        :return:
        """
        entities_to_create = []
        entities_to_update = []
        glossary_terms_to_create = []
        classifications_to_create = []
        with open(entity_file, encoding='utf8') as entity_csv:
            for entity_record in pandas.read_csv(entity_csv, na_filter=False).to_dict(orient='records'):
                if entity_record[AtlasSerializedEntityFields.type_name] == AtlasCommonTypes.tag:
                    glossary_terms_to_create.append(entity_record)
                    continue

                if entity_record[AtlasSerializedEntityFields.type_name] == AtlasCommonTypes.badge:
                    classifications_to_create.append(entity_record)
                    continue

                if entity_record[AtlasSerializedEntityFields.operation] == AtlasSerializedEntityOperation.CREATE:
                    entities_to_create.append(self._create_entity_from_dict(entity_record))
                if entity_record[AtlasSerializedEntityFields.operation] == AtlasSerializedEntityOperation.UPDATE:
                    entities_to_update.append(self._create_entity_from_dict(entity_record))
        return entities_to_create, entities_to_update, glossary_terms_to_create, classifications_to_create

    def _extract_entity_relations_details(self, relation_details: str) -> Iterator[Tuple]:
        """
        Generate relation details from relation_attr#related_entity_type#related_qualified_name
        """
        relations = relation_details.split(AtlasSerializedEntityFields.relationships_separator)
        for relation in relations:
            relation_split = relation.split(AtlasSerializedEntityFields.relationships_kv_separator)
            yield relation_split[0], relation_split[1], relation_split[2]

    def _create_entity_from_dict(self, entity_dict: Dict) -> AtlasEntity:
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
            relations = {}
            for relation_attr, rel_type, rel_qn in self._extract_entity_relations_details(relationships):
                related_obj = self._get_atlas_related_object_id_by_qn(rel_type, rel_qn)
                relations[relation_attr] = related_obj
            entity.relationshipAttributes = relations
        return entity

    def _chunks(self, lst: List) -> Iterator:
        """
        Yield successive n-sized chunks from lst.
        :param lst:
        :return: chunks generator
        """
        n = self._config.get_int(AtlasCSVPublisher.ATLAS_ENTITY_CREATE_BATCH_SIZE)
        for i in range(0, len(lst), n):
            yield lst[i:i + n]

    def _sync_entities_to_atlas(self, entities: List[AtlasEntity]) -> None:
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
            except AtlasServiceException:
                LOGGER.error('Error during entity syncing', exc_info=True)

    def _create_glossary_terms(self, glossary_terms: List[Dict]) -> None:
        for glossary_term_spec in glossary_terms:
            glossary_name = glossary_term_spec.get('glossary')
            term_name = glossary_term_spec.get('term')

            glossary_def = AtlasGlossary({'name': glossary_name, 'shortDescription': ''})

            try:
                glossary = self._atlas_client.glossary.create_glossary(glossary_def)
            except AtlasServiceException:
                LOGGER.info(f'Glossary: {glossary_name} already exists.')
                glossary = next(filter(lambda x: x.get('name') == glossary_name,
                                       self._atlas_client.glossary.get_all_glossaries()))

            glossary_guid = glossary['guid']
            glossary_def = AtlasGlossaryHeader({'glossaryGuid': glossary_guid})
            term_def = AtlasGlossaryTerm({'name': term_name, 'anchor': glossary_def})

            try:
                self._atlas_client.glossary.create_glossary_term(term_def)
            except AtlasServiceException:
                LOGGER.info(f'Glossary Term: {term_name} already exists.')

    def _assign_glossary_term(self, relationship_spec: Dict) -> None:
        _glossary_name, _term_name = relationship_spec[AtlasSerializedRelationshipFields.qualified_name_2].split(',')

        glossary_name = _glossary_name.split('=')[1]
        term_name = _term_name.split('=')[1]

        entity_type = relationship_spec[AtlasSerializedRelationshipFields.entity_type_1]
        entity_qn = relationship_spec[AtlasSerializedRelationshipFields.qualified_name_1]

        glossary = next(filter(lambda g: g.get('name') == glossary_name,
                               self._atlas_client.glossary.get_all_glossaries()))

        glossary_guid = glossary[AtlasCommonParams.guid]

        term = next(filter(lambda t: t.get('name') == term_name,
                           self._atlas_client.glossary.get_glossary_terms(glossary_guid)))

        entity = self._atlas_client.entity.get_entity_by_attribute(entity_type, uniq_attributes=[
            (AtlasCommonParams.qualified_name, entity_qn)])

        entity_guid = entity.entity.guid

        e = AtlasRelatedObjectId({AtlasCommonParams.guid: entity_guid, AtlasCommonParams.type_name: entity_type})

        try:
            self._atlas_client.glossary.assign_term_to_entities(term[AtlasCommonParams.guid], [e])
        except Exception:
            LOGGER.error('Error assigning terms to entities.', exc_info=True)

    def _render_super_type_from_dict(self, classification_spec: Dict) -> AtlasClassificationDef:
        return self._render_classification(classification_spec, True)

    def _render_sub_type_from_dict(self, classification_spec: Dict) -> AtlasClassificationDef:
        return self._render_classification(classification_spec, False)

    def _render_classification(self, classification_spec: Dict, super_type: bool) -> AtlasClassificationDef:
        name = classification_spec.get('category') if super_type else classification_spec.get('name')
        sub_types = [classification_spec.get('category')] if not super_type else []

        result = AtlasClassificationDef(attrs=dict(name=name,
                                                   attributeDefs=[],
                                                   subTypes=sub_types,
                                                   superTypes=[],
                                                   entityTypes=[]))

        return result

    def _create_classifications(self, classifications: List[Dict]) -> None:
        _st = set()
        super_types = [self._render_super_type_from_dict(s) for s in classifications if s['category'] not in _st and
                       _st.add(s['category'])]  # type: ignore
        super_types_chunks = self._chunks(super_types)

        sub_types = [self._render_sub_type_from_dict(s) for s in classifications]
        sub_types_chunks = self._chunks(sub_types)

        for chunks in [super_types_chunks, sub_types_chunks]:
            for chunk in chunks:
                LOGGER.info(f'Syncing chunk of {len(chunk)} classifications with atlas')
                try:
                    types = AtlasTypesDef(attrs=dict(classificationDefs=chunk))

                    self._atlas_client.typedef.create_atlas_typedefs(types)
                except AtlasServiceException:
                    LOGGER.error('Error during classification syncing', exc_info=True)

    def _assign_classification(self, relationship_spec: Dict) -> None:
        classification_qn = relationship_spec[AtlasSerializedRelationshipFields.qualified_name_2]

        entity_type = relationship_spec[AtlasSerializedRelationshipFields.entity_type_1]
        entity_qn = relationship_spec[AtlasSerializedRelationshipFields.qualified_name_1]

        try:
            self._atlas_client.entity.add_classifications_by_type(entity_type,
                                                                  uniq_attributes=[(AtlasCommonParams.qualified_name,
                                                                                    entity_qn)],
                                                                  classifications=[classification_qn])
        except Exception:
            LOGGER.error('Error during classification assingment.', exc_info=True)

    def get_scope(self) -> str:
        return 'publisher.atlas_csv_publisher'
