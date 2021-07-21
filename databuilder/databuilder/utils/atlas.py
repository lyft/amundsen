class AtlasRelationshipTypes:
    group_dashboard = 'DashboardGroup__Dashboard'
    resource_owner = 'DataSet_Users_Owner'
    dashboard_query = 'Dashboard__DashboardQuery'
    query_chart = 'DashboardQuery__DashboardChart'
    dashboard_execution = 'Dashboard__DashboardExecution'
    table_dashboard = 'Table__Dashboard'
    dashboard_owner = 'Dashboard_Users_Owner'
    table_application = 'DataSet__Application'
    table_source = 'Source__Tables'
    lineage_upstream = 'dataset_process_inputs'
    lineage_downstream = 'process_dataset_outputs'
    tag = 'AtlasGlossaryTerm'
    badge = 'AtlasClassification'
    referenceable_reader = 'Referenceable_Readers'
    reader_user = 'Reader_Users'


class AtlasSerializedRelationshipFields:
    relation_type = 'relationshipType'
    entity_type_1 = 'entityType1'
    qualified_name_1 = 'entityQualifiedName1'
    entity_type_2 = 'entityType2'
    qualified_name_2 = 'entityQualifiedName2'


class AtlasSerializedEntityFields:
    operation = 'operation'
    relationships = 'relationships'
    type_name = 'typeName'
    attributes = 'attributes'
    relationships_separator = '|'
    relationships_kv_separator = '#'


class AtlasSerializedEntityOperation:
    CREATE = 'CREATE'
    UPDATE = 'UPDATE'
