# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from unittest.mock import ANY

from databuilder.serializers.neptune_serializer import (
    METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT, NEPTUNE_CREATION_TYPE_JOB,
    NEPTUNE_CREATION_TYPE_NODE_PROPERTY_NAME_BULK_LOADER_FORMAT,
    NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT, NEPTUNE_HEADER_ID, NEPTUNE_HEADER_LABEL,
    NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT, NEPTUNE_RELATIONSHIP_HEADER_FROM,
    NEPTUNE_RELATIONSHIP_HEADER_TO,
)

EXPECTED_NEPTUNE_NODES = [
    {
        'name:String(single)': 'test_table1',
        NEPTUNE_HEADER_ID: 'Table:hive://gold.test_schema1/test_table1',
        METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: 'hive://gold.test_schema1/test_table1',
        NEPTUNE_HEADER_LABEL: 'Table',
        NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
        NEPTUNE_CREATION_TYPE_NODE_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB,
        'is_view:Bool(single)': False
    },
    {
        'description:String(single)': 'test_table1',
        NEPTUNE_HEADER_ID: 'Description:hive://gold.test_schema1/test_table1/_description',
        METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: 'hive://gold.test_schema1/test_table1/_description',
        NEPTUNE_HEADER_LABEL: 'Description',
        NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
        NEPTUNE_CREATION_TYPE_NODE_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB,
        'description_source:String(single)': 'description'
    },
    {
        'sort_order:Long(single)': 0,
        'col_type:String(single)': 'bigint',
        'name:String(single)': 'test_id1',
        NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
        NEPTUNE_CREATION_TYPE_NODE_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB,
        NEPTUNE_HEADER_ID: 'Column:hive://gold.test_schema1/test_table1/test_id1',
        METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: 'hive://gold.test_schema1/test_table1/test_id1',
        NEPTUNE_HEADER_LABEL: 'Column'
    },
    {
        'description:String(single)': 'description of test_table1',
        NEPTUNE_HEADER_ID: 'Description:hive://gold.test_schema1/test_table1/test_id1/_description',
        METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: 'hive://gold.test_schema1/test_table1/test_id1/_description',
        NEPTUNE_HEADER_LABEL: 'Description',
        NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
        NEPTUNE_CREATION_TYPE_NODE_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB,
        'description_source:String(single)': 'description'
    },
    {
        'sort_order:Long(single)': 1,
        'col_type:String(single)': 'bigint',
        'name:String(single)': 'test_id2',
        NEPTUNE_HEADER_ID: 'Column:hive://gold.test_schema1/test_table1/test_id2',
        METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: 'hive://gold.test_schema1/test_table1/test_id2',
        NEPTUNE_HEADER_LABEL: 'Column',
        NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
        NEPTUNE_CREATION_TYPE_NODE_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB,
    },
    {
        'description:String(single)': 'description of test_id2',
        NEPTUNE_HEADER_ID: 'Description:hive://gold.test_schema1/test_table1/test_id2/_description',
        METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: 'hive://gold.test_schema1/test_table1/test_id2/_description',
        NEPTUNE_HEADER_LABEL: 'Description',
        NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
        NEPTUNE_CREATION_TYPE_NODE_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB,
        'description_source:String(single)': 'description'
    },
    {
        'sort_order:Long(single)': 2,
        'col_type:String(single)': 'boolean',
        'name:String(single)': 'is_active',
        NEPTUNE_HEADER_ID: 'Column:hive://gold.test_schema1/test_table1/is_active',
        METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: 'hive://gold.test_schema1/test_table1/is_active',
        NEPTUNE_HEADER_LABEL: 'Column',
        NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
        NEPTUNE_CREATION_TYPE_NODE_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB,
    },
    {
        'sort_order:Long(single)': 3,
        'col_type:String(single)': 'varchar',
        'name:String(single)': 'source',
        NEPTUNE_HEADER_ID: 'Column:hive://gold.test_schema1/test_table1/source',
        METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: 'hive://gold.test_schema1/test_table1/source',
        NEPTUNE_HEADER_LABEL: 'Column',
        NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
        NEPTUNE_CREATION_TYPE_NODE_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB,
    },
    {
        'description:String(single)': 'description of source',
        NEPTUNE_HEADER_ID: 'Description:hive://gold.test_schema1/test_table1/source/_description',
        METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: 'hive://gold.test_schema1/test_table1/source/_description',
        NEPTUNE_HEADER_LABEL: 'Description',
        NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
        NEPTUNE_CREATION_TYPE_NODE_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB,
        'description_source:String(single)': 'description'
    },
    {
        'sort_order:Long(single)': 4,
        'col_type:String(single)': 'timestamp',
        'name:String(single)': 'etl_created_at',
        NEPTUNE_HEADER_ID: 'Column:hive://gold.test_schema1/test_table1/etl_created_at',
        METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: 'hive://gold.test_schema1/test_table1/etl_created_at',
        NEPTUNE_HEADER_LABEL: 'Column',
        NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
        NEPTUNE_CREATION_TYPE_NODE_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB,
    },
    {
        'description:String(single)': 'description of etl_created_at',
        NEPTUNE_HEADER_ID: 'Description:hive://gold.test_schema1/test_table1/etl_created_at/_description',
        METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT:
            'hive://gold.test_schema1/test_table1/etl_created_at/_description',
        NEPTUNE_HEADER_LABEL: 'Description',
        NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
        NEPTUNE_CREATION_TYPE_NODE_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB,
        'description_source:String(single)': 'description'
    },
    {
        'sort_order:Long(single)': 5,
        'col_type:String(single)': 'varchar',
        'name:String(single)': 'ds',
        NEPTUNE_HEADER_ID: 'Column:hive://gold.test_schema1/test_table1/ds',
        METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: 'hive://gold.test_schema1/test_table1/ds',
        NEPTUNE_HEADER_LABEL: 'Column',
        NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
        NEPTUNE_CREATION_TYPE_NODE_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB,
    },
    {
        'name:String(single)': 'hive',
        NEPTUNE_HEADER_ID: 'Database:database://hive',
        METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: 'database://hive',
        NEPTUNE_HEADER_LABEL: 'Database',
        NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
        NEPTUNE_CREATION_TYPE_NODE_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB,
    },
    {
        'name:String(single)': 'gold',
        NEPTUNE_HEADER_ID: 'Cluster:hive://gold',
        METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: 'hive://gold',
        NEPTUNE_HEADER_LABEL: 'Cluster',
        NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
        NEPTUNE_CREATION_TYPE_NODE_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB,
    },
    {
        'name:String(single)': 'test_schema1',
        NEPTUNE_HEADER_ID: 'Schema:hive://gold.test_schema1',
        METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: 'hive://gold.test_schema1',
        NEPTUNE_HEADER_LABEL: 'Schema',
        NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
        NEPTUNE_CREATION_TYPE_NODE_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB,
    }
]

EXPECTED_RELATIONSHIPS_NEPTUNE = [
    [
        {
            NEPTUNE_HEADER_ID: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                from_vertex_id='Schema:hive://gold.test_schema1',
                to_vertex_id='Table:hive://gold.test_schema1/test_table1',
                label='TABLE'
            ),
            METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                from_vertex_id='Schema:hive://gold.test_schema1',
                to_vertex_id='Table:hive://gold.test_schema1/test_table1',
                label='TABLE'
            ),
            NEPTUNE_RELATIONSHIP_HEADER_FROM: 'Schema:hive://gold.test_schema1',
            NEPTUNE_RELATIONSHIP_HEADER_TO: 'Table:hive://gold.test_schema1/test_table1',
            NEPTUNE_HEADER_LABEL: 'TABLE',
            NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
            NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB
        },
        {
            NEPTUNE_HEADER_ID: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                from_vertex_id='Table:hive://gold.test_schema1/test_table1',
                to_vertex_id='Schema:hive://gold.test_schema1',
                label='TABLE_OF'
            ),
            METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                from_vertex_id='Table:hive://gold.test_schema1/test_table1',
                to_vertex_id='Schema:hive://gold.test_schema1',
                label='TABLE_OF'
            ),
            NEPTUNE_RELATIONSHIP_HEADER_FROM: 'Table:hive://gold.test_schema1/test_table1',
            NEPTUNE_RELATIONSHIP_HEADER_TO: 'Schema:hive://gold.test_schema1',
            NEPTUNE_HEADER_LABEL: 'TABLE_OF',
            NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
            NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB
        }
    ],
    [
        {
            NEPTUNE_HEADER_ID: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                from_vertex_id='Table:hive://gold.test_schema1/test_table1',
                to_vertex_id='Description:hive://gold.test_schema1/test_table1/_description',
                label='DESCRIPTION'
            ),
            METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                from_vertex_id='Table:hive://gold.test_schema1/test_table1',
                to_vertex_id='Description:hive://gold.test_schema1/test_table1/_description',
                label='DESCRIPTION'
            ),
            NEPTUNE_RELATIONSHIP_HEADER_FROM: 'Table:hive://gold.test_schema1/test_table1',
            NEPTUNE_RELATIONSHIP_HEADER_TO: 'Description:hive://gold.test_schema1/test_table1/_description',
            NEPTUNE_HEADER_LABEL: 'DESCRIPTION',
            NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
            NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB
        },
        {
            NEPTUNE_HEADER_ID: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                from_vertex_id='Description:hive://gold.test_schema1/test_table1/_description',
                to_vertex_id='Table:hive://gold.test_schema1/test_table1',
                label='DESCRIPTION_OF'
            ),
            METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                from_vertex_id='Description:hive://gold.test_schema1/test_table1/_description',
                to_vertex_id='Table:hive://gold.test_schema1/test_table1',
                label='DESCRIPTION_OF'
            ),
            NEPTUNE_RELATIONSHIP_HEADER_FROM: 'Description:hive://gold.test_schema1/test_table1/_description',
            NEPTUNE_RELATIONSHIP_HEADER_TO: 'Table:hive://gold.test_schema1/test_table1',
            NEPTUNE_HEADER_LABEL: 'DESCRIPTION_OF',
            NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
            NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB
        }
    ],
    [
        {
            NEPTUNE_HEADER_ID: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                from_vertex_id='Table:hive://gold.test_schema1/test_table1',
                to_vertex_id='Column:hive://gold.test_schema1/test_table1/test_id1',
                label='COLUMN'
            ),
            METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                from_vertex_id='Table:hive://gold.test_schema1/test_table1',
                to_vertex_id='Column:hive://gold.test_schema1/test_table1/test_id1',
                label='COLUMN'
            ),
            NEPTUNE_RELATIONSHIP_HEADER_FROM: 'Table:hive://gold.test_schema1/test_table1',
            NEPTUNE_RELATIONSHIP_HEADER_TO: 'Column:hive://gold.test_schema1/test_table1/test_id1',
            NEPTUNE_HEADER_LABEL: 'COLUMN',
            NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
            NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB
        },
        {
            NEPTUNE_HEADER_ID: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                from_vertex_id='Column:hive://gold.test_schema1/test_table1/test_id1',
                to_vertex_id='Table:hive://gold.test_schema1/test_table1',
                label='COLUMN_OF'
            ),
            METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                from_vertex_id='Column:hive://gold.test_schema1/test_table1/test_id1',
                to_vertex_id='Table:hive://gold.test_schema1/test_table1',
                label='COLUMN_OF'
            ),
            NEPTUNE_RELATIONSHIP_HEADER_FROM: 'Column:hive://gold.test_schema1/test_table1/test_id1',
            NEPTUNE_RELATIONSHIP_HEADER_TO: 'Table:hive://gold.test_schema1/test_table1',
            NEPTUNE_HEADER_LABEL: 'COLUMN_OF',
            NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
            NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB
        }
    ],
    [
        {
            NEPTUNE_HEADER_ID: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                from_vertex_id='Column:hive://gold.test_schema1/test_table1/test_id1',
                to_vertex_id='Description:hive://gold.test_schema1/test_table1/test_id1/_description',
                label='DESCRIPTION'
            ),
            METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                from_vertex_id='Column:hive://gold.test_schema1/test_table1/test_id1',
                to_vertex_id='Description:hive://gold.test_schema1/test_table1/test_id1/_description',
                label='DESCRIPTION'
            ),
            NEPTUNE_RELATIONSHIP_HEADER_FROM: 'Column:hive://gold.test_schema1/test_table1/test_id1',
            NEPTUNE_RELATIONSHIP_HEADER_TO: 'Description:hive://gold.test_schema1/test_table1/test_id1/_description',
            NEPTUNE_HEADER_LABEL: 'DESCRIPTION',
            NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
            NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB
        },
        {
            NEPTUNE_HEADER_ID: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                from_vertex_id='Description:hive://gold.test_schema1/test_table1/test_id1/_description',
                to_vertex_id='Column:hive://gold.test_schema1/test_table1/test_id1',
                label='DESCRIPTION_OF'
            ),
            METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                from_vertex_id='Description:hive://gold.test_schema1/test_table1/test_id1/_description',
                to_vertex_id='Column:hive://gold.test_schema1/test_table1/test_id1',
                label='DESCRIPTION_OF'
            ),
            NEPTUNE_RELATIONSHIP_HEADER_FROM: 'Description:hive://gold.test_schema1/test_table1/test_id1/_description',
            NEPTUNE_RELATIONSHIP_HEADER_TO: 'Column:hive://gold.test_schema1/test_table1/test_id1',
            NEPTUNE_HEADER_LABEL: 'DESCRIPTION_OF',
            NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
            NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB
        }
    ],
    [
        {
            NEPTUNE_HEADER_ID: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                from_vertex_id='Table:hive://gold.test_schema1/test_table1',
                to_vertex_id='Column:hive://gold.test_schema1/test_table1/test_id2',
                label='COLUMN'
            ),
            METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                from_vertex_id='Table:hive://gold.test_schema1/test_table1',
                to_vertex_id='Column:hive://gold.test_schema1/test_table1/test_id2',
                label='COLUMN'
            ),
            NEPTUNE_RELATIONSHIP_HEADER_FROM: 'Table:hive://gold.test_schema1/test_table1',
            NEPTUNE_RELATIONSHIP_HEADER_TO: 'Column:hive://gold.test_schema1/test_table1/test_id2',
            NEPTUNE_HEADER_LABEL: 'COLUMN',
            NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
            NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB
        },
        {
            NEPTUNE_HEADER_ID: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                from_vertex_id='Column:hive://gold.test_schema1/test_table1/test_id2',
                to_vertex_id='Table:hive://gold.test_schema1/test_table1',
                label='COLUMN_OF'
            ),
            METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                from_vertex_id='Column:hive://gold.test_schema1/test_table1/test_id2',
                to_vertex_id='Table:hive://gold.test_schema1/test_table1',
                label='COLUMN_OF'
            ),
            NEPTUNE_RELATIONSHIP_HEADER_FROM: 'Column:hive://gold.test_schema1/test_table1/test_id2',
            NEPTUNE_RELATIONSHIP_HEADER_TO: 'Table:hive://gold.test_schema1/test_table1',
            NEPTUNE_HEADER_LABEL: 'COLUMN_OF',
            NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
            NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB
        }
    ],
    [
        {
            NEPTUNE_HEADER_ID: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                from_vertex_id='Column:hive://gold.test_schema1/test_table1/test_id2',
                to_vertex_id='Description:hive://gold.test_schema1/test_table1/test_id2/_description',
                label='DESCRIPTION'
            ),
            METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                from_vertex_id='Column:hive://gold.test_schema1/test_table1/test_id2',
                to_vertex_id='Description:hive://gold.test_schema1/test_table1/test_id2/_description',
                label='DESCRIPTION'
            ),
            NEPTUNE_RELATIONSHIP_HEADER_FROM: 'Column:hive://gold.test_schema1/test_table1/test_id2',
            NEPTUNE_RELATIONSHIP_HEADER_TO: 'Description:hive://gold.test_schema1/test_table1/test_id2/_description',
            NEPTUNE_HEADER_LABEL: 'DESCRIPTION',
            NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
            NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB
        },
        {
            NEPTUNE_HEADER_ID: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                from_vertex_id='Description:hive://gold.test_schema1/test_table1/test_id2/_description',
                to_vertex_id='Column:hive://gold.test_schema1/test_table1/test_id2',
                label='DESCRIPTION_OF'
            ),
            METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                from_vertex_id='Description:hive://gold.test_schema1/test_table1/test_id2/_description',
                to_vertex_id='Column:hive://gold.test_schema1/test_table1/test_id2',
                label='DESCRIPTION_OF'
            ),
            NEPTUNE_RELATIONSHIP_HEADER_FROM: 'Description:hive://gold.test_schema1/test_table1/test_id2/_description',
            NEPTUNE_RELATIONSHIP_HEADER_TO: 'Column:hive://gold.test_schema1/test_table1/test_id2',
            NEPTUNE_HEADER_LABEL: 'DESCRIPTION_OF',
            NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
            NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB
        }
    ],
    [
        {
            NEPTUNE_HEADER_ID: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                from_vertex_id='Table:hive://gold.test_schema1/test_table1',
                to_vertex_id='Column:hive://gold.test_schema1/test_table1/is_active',
                label='COLUMN'
            ),
            METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                from_vertex_id='Table:hive://gold.test_schema1/test_table1',
                to_vertex_id='Column:hive://gold.test_schema1/test_table1/is_active',
                label='COLUMN'
            ),
            NEPTUNE_RELATIONSHIP_HEADER_FROM: 'Table:hive://gold.test_schema1/test_table1',
            NEPTUNE_RELATIONSHIP_HEADER_TO: 'Column:hive://gold.test_schema1/test_table1/is_active',
            NEPTUNE_HEADER_LABEL: 'COLUMN',
            NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
            NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB
        },
        {
            NEPTUNE_HEADER_ID: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                from_vertex_id='Column:hive://gold.test_schema1/test_table1/is_active',
                to_vertex_id='Table:hive://gold.test_schema1/test_table1',
                label='COLUMN_OF'
            ),
            METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                from_vertex_id='Column:hive://gold.test_schema1/test_table1/is_active',
                to_vertex_id='Table:hive://gold.test_schema1/test_table1',
                label='COLUMN_OF'
            ),
            NEPTUNE_RELATIONSHIP_HEADER_FROM: 'Column:hive://gold.test_schema1/test_table1/is_active',
            NEPTUNE_RELATIONSHIP_HEADER_TO: 'Table:hive://gold.test_schema1/test_table1',
            NEPTUNE_HEADER_LABEL: 'COLUMN_OF',
            NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
            NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB
        }
    ],
    [
        {
            NEPTUNE_HEADER_ID: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                from_vertex_id='Table:hive://gold.test_schema1/test_table1',
                to_vertex_id='Column:hive://gold.test_schema1/test_table1/source',
                label='COLUMN'
            ),
            METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                from_vertex_id='Table:hive://gold.test_schema1/test_table1',
                to_vertex_id='Column:hive://gold.test_schema1/test_table1/source',
                label='COLUMN'
            ),
            NEPTUNE_RELATIONSHIP_HEADER_FROM: 'Table:hive://gold.test_schema1/test_table1',
            NEPTUNE_RELATIONSHIP_HEADER_TO: 'Column:hive://gold.test_schema1/test_table1/source',
            NEPTUNE_HEADER_LABEL: 'COLUMN',
            NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
            NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB
        },
        {
            NEPTUNE_HEADER_ID: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                from_vertex_id='Column:hive://gold.test_schema1/test_table1/source',
                to_vertex_id='Table:hive://gold.test_schema1/test_table1',
                label='COLUMN_OF'
            ),
            METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                from_vertex_id='Column:hive://gold.test_schema1/test_table1/source',
                to_vertex_id='Table:hive://gold.test_schema1/test_table1',
                label='COLUMN_OF'
            ),
            NEPTUNE_RELATIONSHIP_HEADER_FROM: 'Column:hive://gold.test_schema1/test_table1/source',
            NEPTUNE_RELATIONSHIP_HEADER_TO: 'Table:hive://gold.test_schema1/test_table1',
            NEPTUNE_HEADER_LABEL: 'COLUMN_OF',
            NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
            NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB
        }
    ],
    [
        {
            NEPTUNE_HEADER_ID: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                from_vertex_id='Column:hive://gold.test_schema1/test_table1/source',
                to_vertex_id='Description:hive://gold.test_schema1/test_table1/source/_description',
                label='DESCRIPTION'
            ),
            METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                from_vertex_id='Column:hive://gold.test_schema1/test_table1/source',
                to_vertex_id='Description:hive://gold.test_schema1/test_table1/source/_description',
                label='DESCRIPTION'
            ),
            NEPTUNE_RELATIONSHIP_HEADER_FROM: 'Column:hive://gold.test_schema1/test_table1/source',
            NEPTUNE_RELATIONSHIP_HEADER_TO: 'Description:hive://gold.test_schema1/test_table1/source/_description',
            NEPTUNE_HEADER_LABEL: 'DESCRIPTION',
            NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
            NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB
        },
        {
            NEPTUNE_HEADER_ID: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                from_vertex_id='Description:hive://gold.test_schema1/test_table1/source/_description',
                to_vertex_id='Column:hive://gold.test_schema1/test_table1/source',
                label='DESCRIPTION_OF'
            ),
            METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                from_vertex_id='Description:hive://gold.test_schema1/test_table1/source/_description',
                to_vertex_id='Column:hive://gold.test_schema1/test_table1/source',
                label='DESCRIPTION_OF'
            ),
            NEPTUNE_RELATIONSHIP_HEADER_FROM: 'Description:hive://gold.test_schema1/test_table1/source/_description',
            NEPTUNE_RELATIONSHIP_HEADER_TO: 'Column:hive://gold.test_schema1/test_table1/source',
            NEPTUNE_HEADER_LABEL: 'DESCRIPTION_OF',
            NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
            NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB
        }
    ],
    [
        {
            NEPTUNE_HEADER_ID: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                from_vertex_id='Table:hive://gold.test_schema1/test_table1',
                to_vertex_id='Column:hive://gold.test_schema1/test_table1/etl_created_at',
                label='COLUMN'
            ),
            METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                from_vertex_id='Table:hive://gold.test_schema1/test_table1',
                to_vertex_id='Column:hive://gold.test_schema1/test_table1/etl_created_at',
                label='COLUMN'
            ),
            NEPTUNE_RELATIONSHIP_HEADER_FROM: 'Table:hive://gold.test_schema1/test_table1',
            NEPTUNE_RELATIONSHIP_HEADER_TO: 'Column:hive://gold.test_schema1/test_table1/etl_created_at',
            NEPTUNE_HEADER_LABEL: 'COLUMN',
            NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
            NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB
        },
        {
            NEPTUNE_HEADER_ID: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                from_vertex_id='Column:hive://gold.test_schema1/test_table1/etl_created_at',
                to_vertex_id='Table:hive://gold.test_schema1/test_table1',
                label='COLUMN_OF'
            ),
            METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                from_vertex_id='Column:hive://gold.test_schema1/test_table1/etl_created_at',
                to_vertex_id='Table:hive://gold.test_schema1/test_table1',
                label='COLUMN_OF'
            ),
            NEPTUNE_RELATIONSHIP_HEADER_FROM: 'Column:hive://gold.test_schema1/test_table1/etl_created_at',
            NEPTUNE_RELATIONSHIP_HEADER_TO: 'Table:hive://gold.test_schema1/test_table1',
            NEPTUNE_HEADER_LABEL: 'COLUMN_OF',
            NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
            NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB
        }
    ],
    [
        {
            NEPTUNE_HEADER_ID: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                from_vertex_id='Column:hive://gold.test_schema1/test_table1/etl_created_at',
                to_vertex_id='Description:hive://gold.test_schema1/test_table1/etl_created_at/_description',
                label='DESCRIPTION'
            ),
            METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                from_vertex_id='Column:hive://gold.test_schema1/test_table1/etl_created_at',
                to_vertex_id='Description:hive://gold.test_schema1/test_table1/etl_created_at/_description',
                label='DESCRIPTION'
            ),
            NEPTUNE_RELATIONSHIP_HEADER_FROM: 'Column:hive://gold.test_schema1/test_table1/etl_created_at',
            NEPTUNE_RELATIONSHIP_HEADER_TO:
                'Description:hive://gold.test_schema1/test_table1/etl_created_at/_description',
            NEPTUNE_HEADER_LABEL: 'DESCRIPTION',
            NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
            NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB
        },
        {
            NEPTUNE_HEADER_ID: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                from_vertex_id='Description:hive://gold.test_schema1/test_table1/etl_created_at/_description',
                to_vertex_id='Column:hive://gold.test_schema1/test_table1/etl_created_at',
                label='DESCRIPTION_OF'
            ),
            METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                from_vertex_id='Description:hive://gold.test_schema1/test_table1/etl_created_at/_description',
                to_vertex_id='Column:hive://gold.test_schema1/test_table1/etl_created_at',
                label='DESCRIPTION_OF'
            ),
            NEPTUNE_RELATIONSHIP_HEADER_FROM:
                'Description:hive://gold.test_schema1/test_table1/etl_created_at/_description',
            NEPTUNE_RELATIONSHIP_HEADER_TO: 'Column:hive://gold.test_schema1/test_table1/etl_created_at',
            NEPTUNE_HEADER_LABEL: 'DESCRIPTION_OF',
            NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
            NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB
        }
    ],
    [
        {
            NEPTUNE_HEADER_ID: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                from_vertex_id='Table:hive://gold.test_schema1/test_table1',
                to_vertex_id='Column:hive://gold.test_schema1/test_table1/ds',
                label='COLUMN'
            ),
            METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                from_vertex_id='Table:hive://gold.test_schema1/test_table1',
                to_vertex_id='Column:hive://gold.test_schema1/test_table1/ds',
                label='COLUMN'
            ),
            NEPTUNE_RELATIONSHIP_HEADER_FROM: 'Table:hive://gold.test_schema1/test_table1',
            NEPTUNE_RELATIONSHIP_HEADER_TO: 'Column:hive://gold.test_schema1/test_table1/ds',
            NEPTUNE_HEADER_LABEL: 'COLUMN',
            NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
            NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB
        },
        {
            NEPTUNE_HEADER_ID: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                from_vertex_id='Column:hive://gold.test_schema1/test_table1/ds',
                to_vertex_id='Table:hive://gold.test_schema1/test_table1',
                label='COLUMN_OF'
            ),
            METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: "{label}:{from_vertex_id}_{to_vertex_id}".format(
                from_vertex_id='Column:hive://gold.test_schema1/test_table1/ds',
                to_vertex_id='Table:hive://gold.test_schema1/test_table1',
                label='COLUMN_OF'
            ),
            NEPTUNE_RELATIONSHIP_HEADER_FROM: 'Column:hive://gold.test_schema1/test_table1/ds',
            NEPTUNE_RELATIONSHIP_HEADER_TO: 'Table:hive://gold.test_schema1/test_table1',
            NEPTUNE_HEADER_LABEL: 'COLUMN_OF',
            NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
            NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB
        }
    ],
    [
        {
            NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB,
            NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
            NEPTUNE_RELATIONSHIP_HEADER_FROM: 'Database:database://hive',
            NEPTUNE_HEADER_ID: 'CLUSTER:Database:database://hive_Cluster:hive://gold',
            METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: 'CLUSTER:Database:database://hive_Cluster:hive://gold',
            NEPTUNE_HEADER_LABEL: 'CLUSTER',
            NEPTUNE_RELATIONSHIP_HEADER_TO: 'Cluster:hive://gold'
        },
        {
            NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB,
            NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
            NEPTUNE_RELATIONSHIP_HEADER_FROM: 'Cluster:hive://gold',
            NEPTUNE_HEADER_ID: 'CLUSTER_OF:Cluster:hive://gold_Database:database://hive',
            METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: 'CLUSTER_OF:Cluster:hive://gold_Database:database://hive',
            NEPTUNE_HEADER_LABEL: 'CLUSTER_OF',
            NEPTUNE_RELATIONSHIP_HEADER_TO: 'Database:database://hive'
        }
    ],
    [
        {
            NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB,
            NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
            NEPTUNE_RELATIONSHIP_HEADER_FROM: 'Cluster:hive://gold',
            NEPTUNE_HEADER_ID: 'SCHEMA:Cluster:hive://gold_Schema:hive://gold.test_schema1',
            METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT: 'SCHEMA:Cluster:hive://gold_Schema:hive://gold.test_schema1',
            NEPTUNE_HEADER_LABEL: 'SCHEMA',
            NEPTUNE_RELATIONSHIP_HEADER_TO: 'Schema:hive://gold.test_schema1'
        },
        {
            NEPTUNE_CREATION_TYPE_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: NEPTUNE_CREATION_TYPE_JOB,
            NEPTUNE_LAST_EXTRACTED_AT_RELATIONSHIP_PROPERTY_NAME_BULK_LOADER_FORMAT: ANY,
            NEPTUNE_RELATIONSHIP_HEADER_FROM: 'Schema:hive://gold.test_schema1',
            NEPTUNE_HEADER_ID: 'SCHEMA_OF:Schema:hive://gold.test_schema1_Cluster:hive://gold',
            METADATA_KEY_PROPERTY_NAME_BULK_LOADER_FORMAT:
                'SCHEMA_OF:Schema:hive://gold.test_schema1_Cluster:hive://gold',
            NEPTUNE_HEADER_LABEL: 'SCHEMA_OF',
            NEPTUNE_RELATIONSHIP_HEADER_TO: 'Cluster:hive://gold'
        }
    ]
]

EXPECTED_RECORDS_MYSQL = [
    {
        'rk': 'database://hive',
        'name': 'hive'
    },
    {
        'rk': 'hive://gold',
        'name': 'gold',
        'database_rk': 'database://hive'
    },
    {
        'rk': 'hive://gold.test_schema1',
        'name': 'test_schema1',
        'cluster_rk': 'hive://gold',
    },
    {
        'rk': 'hive://gold.test_schema1/test_table1',
        'name': 'test_table1',
        'is_view': False,
        'schema_rk': 'hive://gold.test_schema1'
    },
    {
        'rk': 'hive://gold.test_schema1/test_table1/_description',
        'description': 'test_table1',
        'description_source': 'description',
        'table_rk': 'hive://gold.test_schema1/test_table1'
    },
    {
        'rk': 'hive://gold.test_schema1/test_table1/test_id1',
        'name': 'test_id1',
        'type': 'bigint',
        'sort_order': 0,
        'table_rk': 'hive://gold.test_schema1/test_table1'
    },
    {
        'rk': 'hive://gold.test_schema1/test_table1/test_id1/_description',
        'description': 'description of test_table1',
        'description_source': 'description',
        'column_rk': 'hive://gold.test_schema1/test_table1/test_id1'
    },
    {
        'rk': 'hive://gold.test_schema1/test_table1/test_id2',
        'name': 'test_id2',
        'type': 'bigint',
        'sort_order': 1,
        'table_rk': 'hive://gold.test_schema1/test_table1'
    },
    {
        'rk': 'hive://gold.test_schema1/test_table1/test_id2/_description',
        'description': 'description of test_id2',
        'description_source': 'description',
        'column_rk': 'hive://gold.test_schema1/test_table1/test_id2'
    },
    {
        'rk': 'hive://gold.test_schema1/test_table1/is_active',
        'name': 'is_active',
        'type': 'boolean',
        'sort_order': 2,
        'table_rk': 'hive://gold.test_schema1/test_table1'
    },
    {
        'rk': 'hive://gold.test_schema1/test_table1/source',
        'name': 'source',
        'type': 'varchar',
        'sort_order': 3,
        'table_rk': 'hive://gold.test_schema1/test_table1'
    },
    {
        'rk': 'hive://gold.test_schema1/test_table1/source/_description',
        'description': 'description of source',
        'description_source': 'description',
        'column_rk': 'hive://gold.test_schema1/test_table1/source'
    },
    {
        'rk': 'hive://gold.test_schema1/test_table1/etl_created_at',
        'name': 'etl_created_at',
        'type': 'timestamp',
        'sort_order': 4,
        'table_rk': 'hive://gold.test_schema1/test_table1'
    },
    {
        'rk': 'hive://gold.test_schema1/test_table1/etl_created_at/_description',
        'description': 'description of etl_created_at',
        'description_source': 'description',
        'column_rk': 'hive://gold.test_schema1/test_table1/etl_created_at'
    },
    {
        'rk': 'hive://gold.test_schema1/test_table1/ds',
        'name': 'ds',
        'type': 'varchar',
        'sort_order': 5,
        'table_rk': 'hive://gold.test_schema1/test_table1'
    }
]
