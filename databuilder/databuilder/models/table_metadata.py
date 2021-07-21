# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import copy
from typing import (
    Any, Dict, Iterable, Iterator, List, Optional, Set, Union,
)

from amundsen_common.utils.atlas import (
    AtlasCommonParams, AtlasCommonTypes, AtlasTableTypes,
)
from amundsen_rds.models import RDSModel
from amundsen_rds.models.cluster import Cluster as RDSCluster
from amundsen_rds.models.column import (
    ColumnBadge as RDSColumnBadge, ColumnDescription as RDSColumnDescription, TableColumn as RDSTableColumn,
)
from amundsen_rds.models.database import Database as RDSDatabase
from amundsen_rds.models.schema import Schema as RDSSchema
from amundsen_rds.models.table import (
    Table as RDSTable, TableDescription as RDSTableDescription,
    TableProgrammaticDescription as RDSTableProgrammaticDescription, TableTag as RDSTableTag,
)
from amundsen_rds.models.tag import Tag as RDSTag

from databuilder.models.atlas_entity import AtlasEntity
from databuilder.models.atlas_relationship import AtlasRelationship
from databuilder.models.atlas_serializable import AtlasSerializable
from databuilder.models.badge import Badge, BadgeMetadata
from databuilder.models.cluster import cluster_constants
from databuilder.models.graph_node import GraphNode
from databuilder.models.graph_relationship import GraphRelationship
from databuilder.models.graph_serializable import GraphSerializable
from databuilder.models.schema import schema_constant
from databuilder.models.table_serializable import TableSerializable
from databuilder.serializers.atlas_serializer import (
    add_entity_relationship, get_entity_attrs, get_entity_relationships,
)
from databuilder.utils.atlas import AtlasRelationshipTypes, AtlasSerializedEntityOperation

DESCRIPTION_NODE_LABEL_VAL = 'Description'
DESCRIPTION_NODE_LABEL = DESCRIPTION_NODE_LABEL_VAL


def _format_as_list(tags: Union[List, str, None]) -> List:
    if tags is None:
        tags = []
    if isinstance(tags, str):
        tags = list(filter(None, tags.split(',')))
    if isinstance(tags, list):
        tags = [tag.lower().strip() for tag in tags]
    return tags


class TagMetadata(GraphSerializable, TableSerializable, AtlasSerializable):
    TAG_NODE_LABEL = 'Tag'
    TAG_KEY_FORMAT = '{tag}'
    TAG_TYPE = 'tag_type'
    DEFAULT_TYPE = 'default'
    BADGE_TYPE = 'badge'
    DASHBOARD_TYPE = 'dashboard'
    METRIC_TYPE = 'metric'

    TAG_ENTITY_RELATION_TYPE = 'TAG'
    ENTITY_TAG_RELATION_TYPE = 'TAGGED_BY'

    def __init__(self,
                 name: str,
                 tag_type: str = 'default',
                 ):
        self._name = name
        self._tag_type = tag_type
        self._nodes = self._create_node_iterator()
        self._relations = self._create_relation_iterator()
        self._records = self._create_record_iterator()
        self._atlas_entity_iterator = self._create_next_atlas_entity()

    @staticmethod
    def get_tag_key(name: str) -> str:
        if not name:
            return ''
        return TagMetadata.TAG_KEY_FORMAT.format(tag=name)

    def get_node(self) -> GraphNode:
        node = GraphNode(
            key=TagMetadata.get_tag_key(self._name),
            label=TagMetadata.TAG_NODE_LABEL,
            attributes={
                TagMetadata.TAG_TYPE: self._tag_type
            }
        )
        return node

    def get_record(self) -> RDSModel:
        record = RDSTag(
            rk=TagMetadata.get_tag_key(self._name),
            tag_type=self._tag_type
        )
        return record

    def create_next_node(self) -> Optional[GraphNode]:
        # return the string representation of the data
        try:
            return next(self._nodes)
        except StopIteration:
            return None

    def create_next_relation(self) -> Optional[GraphRelationship]:
        # We don't emit any relations for Tag ingestion
        try:
            return next(self._relations)
        except StopIteration:
            return None

    def create_next_record(self) -> Union[RDSModel, None]:
        try:
            return next(self._records)
        except StopIteration:
            return None

    def _create_node_iterator(self) -> Iterator[GraphNode]:
        node = self.get_node()
        yield node

    def _create_relation_iterator(self) -> Iterator[GraphRelationship]:
        return
        yield

    def _create_record_iterator(self) -> Iterator[RDSModel]:
        record = self.get_record()
        yield record

    def _create_atlas_glossary_entity(self) -> AtlasEntity:
        attrs_mapping = [
            (AtlasCommonParams.qualified_name, self._name),
            ('glossary', self._tag_type),
            ('term', self._name)
        ]

        entity_attrs = get_entity_attrs(attrs_mapping)

        entity = AtlasEntity(
            typeName=AtlasCommonTypes.tag,
            operation=AtlasSerializedEntityOperation.CREATE,
            attributes=entity_attrs,
            relationships=None
        )

        return entity

    def create_atlas_tag_relation(self, table_key: str) -> AtlasRelationship:
        table_relationship = AtlasRelationship(
            relationshipType=AtlasRelationshipTypes.tag,
            entityType1=AtlasCommonTypes.data_set,
            entityQualifiedName1=table_key,
            entityType2=AtlasRelationshipTypes.tag,
            entityQualifiedName2=f'glossary={self._tag_type},term={self._name}',
            attributes={}
        )

        return table_relationship

    def create_next_atlas_relation(self) -> Union[AtlasRelationship, None]:
        pass

    def _create_next_atlas_entity(self) -> Iterator[AtlasEntity]:
        yield self._create_atlas_glossary_entity()

    def create_next_atlas_entity(self) -> Union[AtlasEntity, None]:
        try:
            return next(self._atlas_entity_iterator)
        except StopIteration:
            return None


# TODO: this should inherit from ProgrammaticDescription in amundsen-common
class DescriptionMetadata(GraphSerializable, AtlasSerializable):
    DESCRIPTION_NODE_LABEL = DESCRIPTION_NODE_LABEL_VAL
    PROGRAMMATIC_DESCRIPTION_NODE_LABEL = 'Programmatic_Description'
    DESCRIPTION_KEY_FORMAT = '{description}'
    DESCRIPTION_TEXT = 'description'
    DESCRIPTION_SOURCE = 'description_source'

    DESCRIPTION_RELATION_TYPE = 'DESCRIPTION'
    INVERSE_DESCRIPTION_RELATION_TYPE = 'DESCRIPTION_OF'

    # The default editable source.
    DEFAULT_SOURCE = "description"

    def __init__(self,
                 text: Optional[str],
                 source: str = DEFAULT_SOURCE,
                 description_key: Optional[str] = None,
                 start_label: Optional[str] = None,  # Table, Column, Schema
                 start_key: Optional[str] = None,
                 ):
        """
        :param source: The unique source of what is populating this description.
        :param text: the description text. Markdown supported.
        """
        self.source = source
        self.text = text
        #  There are so many dependencies on Description node, that it is probably easier to just separate the rest out.
        if self.source == self.DEFAULT_SOURCE:
            self.label = self.DESCRIPTION_NODE_LABEL
        else:
            self.label = self.PROGRAMMATIC_DESCRIPTION_NODE_LABEL

        self.start_label = start_label
        self.start_key = start_key
        self.description_key = description_key or self.get_description_default_key(start_key)

        self._node_iter = self._create_node_iterator()
        self._relation_iter = self._create_relation_iterator()

    @staticmethod
    def create_description_metadata(text: Union[None, str],
                                    source: Optional[str] = DEFAULT_SOURCE,
                                    description_key: Optional[str] = None,
                                    start_label: Optional[str] = None,  # Table, Column, Schema
                                    start_key: Optional[str] = None,
                                    ) -> Optional['DescriptionMetadata']:
        # We do not want to create a node if there is no description text!
        if text is None:
            return None
        description_node = DescriptionMetadata(text=text,
                                               source=source or DescriptionMetadata.DEFAULT_SOURCE,
                                               description_key=description_key,
                                               start_label=start_label,
                                               start_key=start_key)
        return description_node

    def get_description_id(self) -> str:
        if self.source == self.DEFAULT_SOURCE:
            return "_description"
        else:
            return "_" + self.source + "_description"

    def get_description_default_key(self, start_key: Optional[str]) -> Optional[str]:
        return f'{start_key}/{self.get_description_id()}' if start_key else None

    def get_node(self, node_key: str) -> GraphNode:
        node = GraphNode(
            key=node_key,
            label=self.label,
            attributes={
                DescriptionMetadata.DESCRIPTION_SOURCE: self.source,
                DescriptionMetadata.DESCRIPTION_TEXT: self.text
            }
        )
        return node

    def get_relation(self,
                     start_node: str,
                     start_key: str,
                     end_key: str,
                     ) -> GraphRelationship:
        relationship = GraphRelationship(
            start_label=start_node,
            start_key=start_key,
            end_label=self.label,
            end_key=end_key,
            type=DescriptionMetadata.DESCRIPTION_RELATION_TYPE,
            reverse_type=DescriptionMetadata.INVERSE_DESCRIPTION_RELATION_TYPE,
            attributes={}
        )
        return relationship

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

    def _create_node_iterator(self) -> Iterator[GraphNode]:
        if not self.description_key:
            raise Exception('Required description node key cannot be None')
        yield self.get_node(self.description_key)

    def _create_relation_iterator(self) -> Iterator[GraphRelationship]:
        if not self.start_label:
            raise Exception('Required relation start node label cannot be None')
        if not self.start_key:
            raise Exception('Required relation start key cannot be None')
        if not self.description_key:
            raise Exception('Required relation end key cannot be None')
        yield self.get_relation(
            start_node=self.start_label,
            start_key=self.start_key,
            end_key=self.description_key
        )

    def create_next_atlas_relation(self) -> Union[AtlasRelationship, None]:
        pass

    def create_next_atlas_entity(self) -> Union[AtlasEntity, None]:
        pass

    def __repr__(self) -> str:
        return f'DescriptionMetadata({self.source!r}, {self.text!r})'


class ColumnMetadata:
    COLUMN_NODE_LABEL = 'Column'
    COLUMN_KEY_FORMAT = '{db}://{cluster}.{schema}/{tbl}/{col}'
    COLUMN_NAME = 'name'
    COLUMN_TYPE = 'col_type'
    COLUMN_ORDER = 'sort_order'
    COLUMN_DESCRIPTION = 'description'
    COLUMN_DESCRIPTION_FORMAT = '{db}://{cluster}.{schema}/{tbl}/{col}/{description_id}'

    def __init__(self,
                 name: str,
                 description: Union[str, None],
                 col_type: str,
                 sort_order: int,
                 badges: Union[List[str], None] = None,
                 ) -> None:
        """
        TODO: Add stats
        :param name:
        :param description:
        :param col_type:
        :param sort_order:
        :param badges: Optional. Column level badges
        """
        self.name = name
        self.description = DescriptionMetadata.create_description_metadata(source=None,
                                                                           text=description)
        self.type = col_type
        self.sort_order = sort_order
        formatted_badges = _format_as_list(badges)
        self.badges = [Badge(badge, 'column') for badge in formatted_badges]

    def __repr__(self) -> str:
        return f'ColumnMetadata({self.name!r}, {self.description!r}, {self.type!r}, ' \
               f'{self.sort_order!r}, {self.badges!r})'


class TableMetadata(GraphSerializable, TableSerializable, AtlasSerializable):
    """
    Table metadata that contains columns. It implements Neo4jCsvSerializable so that it can be serialized to produce
    Table, Column and relation of those along with relationship with table and schema. Additionally, it will create
    Database, Cluster, and Schema with relastionships between those.
    These are being created here as it does not make much sense to have different extraction to produce this. As
    database, cluster, schema would be very repititive with low cardinality, it will perform de-dupe so that publisher
    won't need to publish same nodes, relationships.

    This class can be used for both table and view metadata. If it is a View, is_view=True should be passed in.
    """
    TABLE_NODE_LABEL = 'Table'
    TABLE_KEY_FORMAT = '{db}://{cluster}.{schema}/{tbl}'
    TABLE_NAME = 'name'
    IS_VIEW = 'is_view'

    TABLE_DESCRIPTION_FORMAT = '{db}://{cluster}.{schema}/{tbl}/{description_id}'

    DATABASE_NODE_LABEL = 'Database'
    DATABASE_KEY_FORMAT = 'database://{db}'
    DATABASE_CLUSTER_RELATION_TYPE = cluster_constants.CLUSTER_RELATION_TYPE
    CLUSTER_DATABASE_RELATION_TYPE = cluster_constants.CLUSTER_REVERSE_RELATION_TYPE

    CLUSTER_NODE_LABEL = cluster_constants.CLUSTER_NODE_LABEL
    CLUSTER_KEY_FORMAT = '{db}://{cluster}'
    CLUSTER_SCHEMA_RELATION_TYPE = schema_constant.SCHEMA_RELATION_TYPE
    SCHEMA_CLUSTER_RELATION_TYPE = schema_constant.SCHEMA_REVERSE_RELATION_TYPE

    SCHEMA_NODE_LABEL = schema_constant.SCHEMA_NODE_LABEL
    SCHEMA_KEY_FORMAT = schema_constant.DATABASE_SCHEMA_KEY_FORMAT
    SCHEMA_TABLE_RELATION_TYPE = 'TABLE'
    TABLE_SCHEMA_RELATION_TYPE = 'TABLE_OF'

    TABLE_COL_RELATION_TYPE = 'COLUMN'
    COL_TABLE_RELATION_TYPE = 'COLUMN_OF'

    TABLE_TAG_RELATION_TYPE = TagMetadata.ENTITY_TAG_RELATION_TYPE
    TAG_TABLE_RELATION_TYPE = TagMetadata.TAG_ENTITY_RELATION_TYPE

    # Only for deduping database, cluster, and schema (table and column will be always processed)
    serialized_nodes_keys: Set[Any] = set()
    serialized_rels_keys: Set[Any] = set()
    serialized_records_keys: Set[Any] = set()

    def __init__(self,
                 database: str,
                 cluster: str,
                 schema: str,
                 name: str,
                 description: Union[str, None],
                 columns: Iterable[ColumnMetadata] = None,
                 is_view: bool = False,
                 tags: Union[List, str] = None,
                 description_source: Union[str, None] = None,
                 **kwargs: Any
                 ) -> None:
        """
        :param database:
        :param cluster:
        :param schema:
        :param name:
        :param description:
        :param columns:
        :param is_view: Indicate whether the table is a view or not
        :param tags:
        :param description_source: Optional. Where the description is coming from. Used to compose unique id.
        :param kwargs: Put additional attributes to the table model if there is any.
        """
        self.database = database
        self.cluster = cluster
        self.schema = schema
        self.name = name
        self.description = DescriptionMetadata.create_description_metadata(text=description, source=description_source)
        self.columns = columns if columns else []
        self.is_view = is_view
        self.attrs: Optional[Dict[str, Any]] = None

        self.tags = _format_as_list(tags)

        if kwargs:
            self.attrs = copy.deepcopy(kwargs)

        self._node_iterator = self._create_next_node()
        self._relation_iterator = self._create_next_relation()
        self._record_iterator = self._create_record_iterator()
        self._atlas_entity_iterator = self._create_next_atlas_entity()
        self._atlas_relation_iterator = self._create_atlas_relation_iterator()

    def __repr__(self) -> str:
        return f'TableMetadata({self.database!r}, {self.cluster!r}, {self.schema!r}, {self.name!r} ' \
               f'{self.description!r}, {self.columns!r}, {self.is_view!r}, {self.tags!r})'

    def _get_table_key(self) -> str:
        return TableMetadata.TABLE_KEY_FORMAT.format(db=self.database,
                                                     cluster=self.cluster,
                                                     schema=self.schema,
                                                     tbl=self.name)

    def _get_table_description_key(self, description: DescriptionMetadata) -> str:
        return TableMetadata.TABLE_DESCRIPTION_FORMAT.format(db=self.database,
                                                             cluster=self.cluster,
                                                             schema=self.schema,
                                                             tbl=self.name,
                                                             description_id=description.get_description_id())

    def _get_database_key(self) -> str:
        return TableMetadata.DATABASE_KEY_FORMAT.format(db=self.database)

    def _get_cluster_key(self) -> str:
        return TableMetadata.CLUSTER_KEY_FORMAT.format(db=self.database,
                                                       cluster=self.cluster)

    def _get_schema_key(self) -> str:
        return TableMetadata.SCHEMA_KEY_FORMAT.format(db=self.database,
                                                      cluster=self.cluster,
                                                      schema=self.schema)

    def _get_col_key(self, col: ColumnMetadata) -> str:
        return ColumnMetadata.COLUMN_KEY_FORMAT.format(db=self.database,
                                                       cluster=self.cluster,
                                                       schema=self.schema,
                                                       tbl=self.name,
                                                       col=col.name,
                                                       badges=col.badges)

    def _get_col_description_key(self,
                                 col: ColumnMetadata,
                                 description: DescriptionMetadata) -> str:
        return ColumnMetadata.COLUMN_DESCRIPTION_FORMAT.format(db=self.database,
                                                               cluster=self.cluster,
                                                               schema=self.schema,
                                                               tbl=self.name,
                                                               col=col.name,
                                                               description_id=description.get_description_id())

    @staticmethod
    def format_tags(tags: Union[List, str, None]) -> List:
        return _format_as_list(tags)

    def create_next_node(self) -> Union[GraphNode, None]:
        try:
            return next(self._node_iterator)
        except StopIteration:
            return None

    def _create_next_node(self) -> Iterator[GraphNode]:
        yield self._create_table_node()

        if self.description:
            node_key = self._get_table_description_key(self.description)
            yield self.description.get_node(node_key)

        # Create the table tag nodes
        if self.tags:
            for tag in self.tags:
                tag_node = TagMetadata(tag).get_node()
                yield tag_node

        for col in self.columns:
            column_node = GraphNode(
                key=self._get_col_key(col),
                label=ColumnMetadata.COLUMN_NODE_LABEL,
                attributes={
                    ColumnMetadata.COLUMN_NAME: col.name,
                    ColumnMetadata.COLUMN_TYPE: col.type,
                    ColumnMetadata.COLUMN_ORDER: col.sort_order
                }
            )
            yield column_node

            if col.description:
                node_key = self._get_col_description_key(col, col.description)
                yield col.description.get_node(node_key)

            if col.badges:
                col_badge_metadata = BadgeMetadata(
                    start_label=ColumnMetadata.COLUMN_NODE_LABEL,
                    start_key=self._get_col_key(col),
                    badges=col.badges)
                badge_nodes = col_badge_metadata.get_badge_nodes()
                for node in badge_nodes:
                    yield node

        # Database, cluster, schema
        others = [
            GraphNode(
                key=self._get_database_key(),
                label=TableMetadata.DATABASE_NODE_LABEL,
                attributes={
                    'name': self.database
                }
            ),
            GraphNode(
                key=self._get_cluster_key(),
                label=TableMetadata.CLUSTER_NODE_LABEL,
                attributes={
                    'name': self.cluster
                }
            ),
            GraphNode(
                key=self._get_schema_key(),
                label=TableMetadata.SCHEMA_NODE_LABEL,
                attributes={
                    'name': self.schema
                }
            )
        ]

        for node_tuple in others:
            if node_tuple.key not in TableMetadata.serialized_nodes_keys:
                TableMetadata.serialized_nodes_keys.add(node_tuple.key)
                yield node_tuple

    def _create_table_node(self) -> GraphNode:
        table_attributes = {
            TableMetadata.TABLE_NAME: self.name,
            TableMetadata.IS_VIEW: self.is_view
        }
        if self.attrs:
            for k, v in self.attrs.items():
                if k not in table_attributes:
                    table_attributes[k] = v

        return GraphNode(
            key=self._get_table_key(),
            label=TableMetadata.TABLE_NODE_LABEL,
            attributes=table_attributes
        )

    def create_next_relation(self) -> Union[GraphRelationship, None]:
        try:
            return next(self._relation_iterator)
        except StopIteration:
            return None

    def _create_next_relation(self) -> Iterator[GraphRelationship]:
        schema_table_relationship = GraphRelationship(
            start_key=self._get_schema_key(),
            start_label=TableMetadata.SCHEMA_NODE_LABEL,
            end_key=self._get_table_key(),
            end_label=TableMetadata.TABLE_NODE_LABEL,
            type=TableMetadata.SCHEMA_TABLE_RELATION_TYPE,
            reverse_type=TableMetadata.TABLE_SCHEMA_RELATION_TYPE,
            attributes={}
        )
        yield schema_table_relationship

        if self.description:
            yield self.description.get_relation(TableMetadata.TABLE_NODE_LABEL,
                                                self._get_table_key(),
                                                self._get_table_description_key(self.description))

        if self.tags:
            for tag in self.tags:
                tag_relationship = GraphRelationship(
                    start_label=TableMetadata.TABLE_NODE_LABEL,
                    start_key=self._get_table_key(),
                    end_label=TagMetadata.TAG_NODE_LABEL,
                    end_key=TagMetadata.get_tag_key(tag),
                    type=TableMetadata.TABLE_TAG_RELATION_TYPE,
                    reverse_type=TableMetadata.TAG_TABLE_RELATION_TYPE,
                    attributes={}
                )
                yield tag_relationship

        for col in self.columns:
            column_relationship = GraphRelationship(
                start_label=TableMetadata.TABLE_NODE_LABEL,
                start_key=self._get_table_key(),
                end_label=ColumnMetadata.COLUMN_NODE_LABEL,
                end_key=self._get_col_key(col),
                type=TableMetadata.TABLE_COL_RELATION_TYPE,
                reverse_type=TableMetadata.COL_TABLE_RELATION_TYPE,
                attributes={}
            )
            yield column_relationship

            if col.description:
                yield col.description.get_relation(
                    ColumnMetadata.COLUMN_NODE_LABEL,
                    self._get_col_key(col),
                    self._get_col_description_key(col, col.description)
                )

            if col.badges:
                badge_metadata = BadgeMetadata(start_label=ColumnMetadata.COLUMN_NODE_LABEL,
                                               start_key=self._get_col_key(col),
                                               badges=col.badges)
                badge_relations = badge_metadata.get_badge_relations()
                for relation in badge_relations:
                    yield relation

        others = [
            GraphRelationship(
                start_label=TableMetadata.DATABASE_NODE_LABEL,
                end_label=TableMetadata.CLUSTER_NODE_LABEL,
                start_key=self._get_database_key(),
                end_key=self._get_cluster_key(),
                type=TableMetadata.DATABASE_CLUSTER_RELATION_TYPE,
                reverse_type=TableMetadata.CLUSTER_DATABASE_RELATION_TYPE,
                attributes={}
            ),
            GraphRelationship(
                start_label=TableMetadata.CLUSTER_NODE_LABEL,
                end_label=TableMetadata.SCHEMA_NODE_LABEL,
                start_key=self._get_cluster_key(),
                end_key=self._get_schema_key(),
                type=TableMetadata.CLUSTER_SCHEMA_RELATION_TYPE,
                reverse_type=TableMetadata.SCHEMA_CLUSTER_RELATION_TYPE,
                attributes={}
            )
        ]

        for rel_tuple in others:
            if (rel_tuple.start_key, rel_tuple.end_key, rel_tuple.type) not in TableMetadata.serialized_rels_keys:
                TableMetadata.serialized_rels_keys.add((rel_tuple.start_key, rel_tuple.end_key, rel_tuple.type))
                yield rel_tuple

    def create_next_record(self) -> Union[RDSModel, None]:
        try:
            return next(self._record_iterator)
        except StopIteration:
            return None

    def _create_record_iterator(self) -> Iterator[RDSModel]:
        # Database, Cluster, Schema
        others: List[RDSModel] = [
            RDSDatabase(
                rk=self._get_database_key(),
                name=self.database
            ),
            RDSCluster(
                rk=self._get_cluster_key(),
                name=self.cluster,
                database_rk=self._get_database_key()
            ),
            RDSSchema(
                rk=self._get_schema_key(),
                name=self.schema,
                cluster_rk=self._get_cluster_key()
            )
        ]

        for record in others:
            if record.rk not in TableMetadata.serialized_records_keys:
                TableMetadata.serialized_records_keys.add(record.rk)
                yield record

        # Table
        yield RDSTable(
            rk=self._get_table_key(),
            name=self.name,
            is_view=self.is_view,
            schema_rk=self._get_schema_key()
        )

        # Table description
        if self.description:
            description_record_key = self._get_table_description_key(self.description)
            if self.description.label == DescriptionMetadata.DESCRIPTION_NODE_LABEL:
                yield RDSTableDescription(
                    rk=description_record_key,
                    description_source=self.description.source,
                    description=self.description.text,
                    table_rk=self._get_table_key()
                )
            else:
                yield RDSTableProgrammaticDescription(
                    rk=description_record_key,
                    description_source=self.description.source,
                    description=self.description.text,
                    table_rk=self._get_table_key()
                )

        # Tag
        for tag in self.tags:
            tag_record = TagMetadata(tag).get_record()
            yield tag_record

            table_tag_record = RDSTableTag(
                table_rk=self._get_table_key(),
                tag_rk=TagMetadata.get_tag_key(tag)
            )
            yield table_tag_record

        # Column
        for col in self.columns:
            yield RDSTableColumn(
                rk=self._get_col_key(col),
                name=col.name,
                type=col.type,
                sort_order=col.sort_order,
                table_rk=self._get_table_key()
            )

            if col.description:
                description_record_key = self._get_col_description_key(col, col.description)
                yield RDSColumnDescription(
                    rk=description_record_key,
                    description_source=col.description.source,
                    description=col.description.text,
                    column_rk=self._get_col_key(col)
                )

            if col.badges:
                badge_metadata = BadgeMetadata(
                    start_label=ColumnMetadata.COLUMN_NODE_LABEL,
                    start_key=self._get_col_key(col),
                    badges=col.badges
                )

                badge_records = badge_metadata.get_badge_records()
                for badge_record in badge_records:
                    yield badge_record

                    column_badge_record = RDSColumnBadge(
                        column_rk=self._get_col_key(col),
                        badge_rk=badge_record.rk
                    )
                    yield column_badge_record

    def _create_atlas_cluster_entity(self) -> AtlasEntity:
        attrs_mapping = [
            (AtlasCommonParams.qualified_name, self._get_cluster_key()),
            ('name', self.cluster),
            ('displayName', self.cluster)
        ]

        entity_attrs = get_entity_attrs(attrs_mapping)

        entity = AtlasEntity(
            typeName=AtlasCommonTypes.cluster,
            operation=AtlasSerializedEntityOperation.CREATE,
            attributes=entity_attrs,
            relationships=None
        )

        return entity

    def _create_atlas_database_entity(self) -> AtlasEntity:
        attrs_mapping = [
            (AtlasCommonParams.qualified_name, self._get_database_key()),
            ('name', self.database),
            ('displayName', self.database)
        ]

        entity_attrs = get_entity_attrs(attrs_mapping)

        relationship_list = []  # type: ignore

        add_entity_relationship(
            relationship_list,
            'cluster',
            AtlasCommonTypes.cluster,
            self._get_cluster_key()
        )

        entity = AtlasEntity(
            typeName=AtlasTableTypes.database,
            operation=AtlasSerializedEntityOperation.CREATE,
            attributes=entity_attrs,
            relationships=get_entity_relationships(relationship_list)
        )

        return entity

    def _create_atlas_schema_entity(self) -> AtlasEntity:
        attrs_mapping = [
            (AtlasCommonParams.qualified_name, self._get_schema_key()),
            ('name', self.schema),
            ('displayName', self.schema)
        ]

        entity_attrs = get_entity_attrs(attrs_mapping)

        relationship_list = []  # type: ignore

        add_entity_relationship(
            relationship_list,
            'cluster',
            AtlasCommonTypes.cluster,
            self._get_cluster_key()
        )

        entity = AtlasEntity(
            typeName=AtlasTableTypes.schema,
            operation=AtlasSerializedEntityOperation.CREATE,
            attributes=entity_attrs,
            relationships=get_entity_relationships(relationship_list)
        )

        return entity

    def _create_atlas_table_entity(self) -> AtlasEntity:
        table_type = 'table' if not self.is_view else 'view'

        attrs_mapping = [
            (AtlasCommonParams.qualified_name, self._get_table_key()),
            ('name', self.name),
            ('tableType', table_type),
            ('description', self.description.text if self.description else ''),
            ('displayName', self.name)
        ]

        entity_attrs = get_entity_attrs(attrs_mapping)

        relationship_list = []  # type: ignore

        add_entity_relationship(
            relationship_list,
            'amundsen_schema',
            AtlasTableTypes.schema,
            self._get_schema_key()
        )

        entity = AtlasEntity(
            typeName=AtlasTableTypes.table,
            operation=AtlasSerializedEntityOperation.CREATE,
            attributes=entity_attrs,
            relationships=get_entity_relationships(relationship_list)
        )

        return entity

    def _create_atlas_column_entity(self, column_metadata: ColumnMetadata) -> AtlasEntity:
        qualified_name = column_metadata.COLUMN_KEY_FORMAT.format(db=self.database,
                                                                  cluster=self.cluster,
                                                                  schema=self.schema,
                                                                  tbl=self.name,
                                                                  col=column_metadata.name)
        attrs_mapping = [
            (AtlasCommonParams.qualified_name, qualified_name),
            ('name', column_metadata.name or ''),
            ('description', column_metadata.description.text if column_metadata.description else ''),
            ('type', column_metadata.type),
            ('position', column_metadata.sort_order),
            ('displayName', column_metadata.name or '')
        ]

        entity_attrs = get_entity_attrs(attrs_mapping)

        relationship_list = []  # type: ignore

        add_entity_relationship(
            relationship_list,
            'table',
            AtlasTableTypes.table,
            self._get_table_key()
        )

        entity = AtlasEntity(
            typeName=AtlasTableTypes.column,
            operation=AtlasSerializedEntityOperation.CREATE,
            attributes=entity_attrs,
            relationships=get_entity_relationships(relationship_list)
        )

        return entity

    def _create_next_atlas_relation(self) -> Iterator[AtlasRelationship]:
        pass

    def _create_atlas_relation_iterator(self) -> Iterator[AtlasRelationship]:
        for tag in self.tags:
            tag_relation = TagMetadata(tag).create_atlas_tag_relation(self._get_table_key())
            yield tag_relation

    def create_next_atlas_relation(self) -> Union[AtlasRelationship, None]:
        try:
            return next(self._atlas_relation_iterator)
        except StopIteration:
            return None

    def _create_next_atlas_entity(self) -> Iterator[AtlasEntity]:
        yield self._create_atlas_cluster_entity()
        yield self._create_atlas_database_entity()
        yield self._create_atlas_schema_entity()
        yield self._create_atlas_table_entity()

        for col in self.columns:
            yield self._create_atlas_column_entity(col)

        if self.tags:
            for tag in self.tags:
                tag_entity = TagMetadata(tag).create_next_atlas_entity()
                if tag_entity:
                    yield tag_entity

    def create_next_atlas_entity(self) -> Union[AtlasEntity, None]:
        try:
            return next(self._atlas_entity_iterator)
        except StopIteration:
            return None
