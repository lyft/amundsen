// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

const defaultConfig = {
  columns: [
    {
      col_type: 'string',
      description: null,
      is_editable: true,
      name: 'simple_column_name_string',
      sort_order: 0,
      stats: [
        {
          end_epoch: 1600473600,
          start_epoch: 1597881600,
          stat_type: 'column_usage',
          stat_val: '123',
        },
      ],
    },
    {
      col_type: 'int',
      description: null,
      is_editable: true,
      name: 'simple_column_name_int',
      sort_order: 1,
      stats: [
        {
          end_epoch: 1600473600,
          start_epoch: 1597881600,
          stat_type: 'column_usage',
          stat_val: '456',
        },
      ],
    },
    {
      col_type: 'bigint',
      description: null,
      is_editable: true,
      name: 'simple_column_name_bigint',
      sort_order: 2,
      stats: [
        {
          end_epoch: 1600473600,
          start_epoch: 1597881600,
          stat_type: 'column_usage',
          stat_val: '789',
        },
      ],
    },
    {
      col_type: 'timestamp',
      description: null,
      is_editable: true,
      name: 'simple_column_name_timestamp',
      sort_order: 8,
      stats: [
        {
          end_epoch: 1600473600,
          start_epoch: 1597881600,
          stat_type: 'column_usage',
          stat_val: '1011',
        },
      ],
    },
  ],
};

/**
 * Generates test data for the table data
 * @example
 * let testData = new TestDataBuilder()
 *                         .withAllComplexColumns()
 *                         .build();
 */
function TestDataBuilder(config = {}) {
  this.Klass = TestDataBuilder;
  this.config = {
    ...defaultConfig,
    ...config,
  };

  this.withAllComplexColumns = () => {
    const attr = {
      columns: [
        {
          col_type:
            'struct<trigger_event:string,backfill:boolean,graphql_version:string>',
          description: null,
          is_editable: true,
          name: 'complex_column_name_2',
          sort_order: 1,
          stats: [
            {
              end_epoch: 1600473600,
              start_epoch: 1597881600,
              stat_type: 'column_usage',
              stat_val: '111',
            },
          ],
        },
        {
          col_type: 'struct<code:string,timezone:string>',
          description: null,
          is_editable: true,
          name: 'complex_column_name_3',
          sort_order: 2,
          stats: [
            {
              end_epoch: 1600473600,
              start_epoch: 1597881600,
              stat_type: 'column_usage',
              stat_val: '222',
            },
          ],
        },
        {
          col_type:
            'struct<route_id:string,shift:struct<shift_id:string,started_at:timestamp,ended_at:timestamp>>',
          description: null,
          is_editable: true,
          name: 'complex_column_name_4',
          sort_order: 3,
          stats: [
            {
              end_epoch: 1600473600,
              start_epoch: 1597881600,
              stat_type: 'column_usage',
              stat_val: '333',
            },
          ],
        },
      ],
    };

    return new this.Klass(attr);
  };

  this.withComplexColumnsNoStats = () => {
    const attr = {
      columns: [
        {
          col_type:
            'struct<event_id:string,occurred_at:timestamp,sample_rate:double,__metadata__:struct<flattened:boolean,sending_service:string,streamcheck_selected_at:timestamp,is_priority:boolean,ingest_library_version:string,requires_field_values_as_strings:boolean,aic_time:bigint,fanner_time:bigint,send_to_realtime:boolean,origin_service:string,complex_persistence:boolean>,__debug_metadata__:struct<__is_empty_struct_set__:boolean>,enrichments:struct<is_simulated_ride:boolean>,logged_at:timestamp,source_pipeline:string,reporter_ip_address:string,reporter_hostname:string,http_request_id:string,event_name:string>',
          description: null,
          is_editable: true,
          name: 'complex_column_name_1',
          sort_order: 0,
          stats: [],
        },
        {
          col_type:
            'struct<platform:string,device:string,app_name:string,app_version:string,platform_version:string>',
          description: null,
          is_editable: true,
          name: 'complex_column_name_2',
          sort_order: 28,
          stats: [],
        },
      ],
    };

    return new this.Klass(attr);
  };

  this.withComplexColumnsOneStat = () => {
    const attr = {
      columns: [
        {
          col_type:
            'struct<event_id:string,occurred_at:timestamp,sample_rate:double,__metadata__:struct<flattened:boolean,sending_service:string,streamcheck_selected_at:timestamp,is_priority:boolean,ingest_library_version:string,requires_field_values_as_strings:boolean,aic_time:bigint,fanner_time:bigint,send_to_realtime:boolean,origin_service:string,complex_persistence:boolean>,__debug_metadata__:struct<__is_empty_struct_set__:boolean>,enrichments:struct<is_simulated_ride:boolean>,logged_at:timestamp,source_pipeline:string,reporter_ip_address:string,reporter_hostname:string,http_request_id:string,event_name:string>',
          description: null,
          is_editable: true,
          name: 'complex_column_name_1',
          sort_order: 0,
          stats: [],
        },
        {
          col_type:
            'struct<platform:string,device:string,app_name:string,app_version:string,platform_version:string>',
          description: null,
          is_editable: true,
          name: 'complex_column_name_2',
          sort_order: 28,
          stats: [],
        },
        {
          col_type:
            'struct<platform:string,device:string,app_name:string,app_version:string,platform_version:string>',
          description: null,
          is_editable: true,
          name: 'complex_column_name_3',
          sort_order: 28,
          stats: [
            {
              end_epoch: 1600473600,
              start_epoch: 1597881600,
              stat_type: 'column_usage',
              stat_val: '111',
            },
          ],
        },
      ],
    };

    return new this.Klass(attr);
  };

  this.withSeveralStats = () => {
    const attr = {
      columns: [
        {
          col_type:
            'struct<trigger_event:string,backfill:boolean,graphql_version:string>',
          description: null,
          is_editable: true,
          name: 'complex_column_name_2',
          sort_order: 1,
          stats: [
            {
              end_epoch: 1600473600,
              start_epoch: 1597881600,
              stat_type: 'column_usage',
              stat_val: '111',
            },
          ],
        },
        {
          col_type: 'struct<code:string,timezone:string>',
          description: null,
          is_editable: true,
          name: 'complex_column_name_3',
          sort_order: 2,
          stats: [
            {
              end_epoch: 1600473600,
              start_epoch: 1597881600,
              stat_type: 'test_stat',
              stat_val: '000',
            },
            {
              end_epoch: 1600473600,
              start_epoch: 1597881600,
              stat_type: 'column_usage',
              stat_val: '222',
            },
          ],
        },
        {
          col_type:
            'struct<route_id:string,shift:struct<shift_id:string,started_at:timestamp,ended_at:timestamp>>',
          description: null,
          is_editable: true,
          name: 'complex_column_name_4',
          sort_order: 3,
          stats: [
            {
              end_epoch: 1600473600,
              start_epoch: 1597881600,
              stat_type: 'column_usage',
              stat_val: '333',
            },
          ],
        },
      ],
    };

    return new this.Klass(attr);
  };

  this.withBadges = () => {
    const attr = {
      columns: [
        {
          col_type:
            'struct<trigger_event:string,backfill:boolean,graphql_version:string>',
          description: null,
          is_editable: true,
          name: 'complex_column_name_2',
          sort_order: 1,
          stats: [
            {
              end_epoch: 1600473600,
              start_epoch: 1597881600,
              stat_type: 'column_usage',
              stat_val: '111',
            },
          ],
          badges: [],
        },
        {
          col_type: 'struct<code:string,timezone:string>',
          description: null,
          is_editable: true,
          name: 'complex_column_name_3',
          sort_order: 2,
          stats: [
            {
              end_epoch: 1600473600,
              start_epoch: 1597881600,
              stat_type: 'test_stat',
              stat_val: '000',
            },
            {
              end_epoch: 1600473600,
              start_epoch: 1597881600,
              stat_type: 'column_usage',
              stat_val: '222',
            },
          ],
          badges: [
            {
              badge_name: 'Badge Name 1',
              category: 'column',
            },
          ],
        },
        {
          col_type:
            'struct<route_id:string,shift:struct<shift_id:string,started_at:timestamp,ended_at:timestamp>>',
          description: null,
          is_editable: true,
          name: 'complex_column_name_4',
          sort_order: 3,
          stats: [
            {
              end_epoch: 1600473600,
              start_epoch: 1597881600,
              stat_type: 'column_usage',
              stat_val: '333',
            },
          ],
          badges: [
            {
              badge_name: 'Badge Name 1',
              category: 'column',
            },
            {
              badge_name: 'Badge Name 2',
              category: 'column',
            },
            {
              badge_name: 'Badge Name 3',
              category: 'column',
            },
          ],
        },
      ],
    };

    return new this.Klass(attr);
  };

  this.withEmptyColumns = () => {
    const attr = { columns: [] };

    return new this.Klass(attr);
  };

  this.build = () => this.config;
}

export default TestDataBuilder;
