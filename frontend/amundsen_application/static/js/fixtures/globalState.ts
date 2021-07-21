// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import { GlobalState } from 'ducks/rootReducer';
import { LineageItem, ResourceType, SendingState } from 'interfaces';

import { defaultEmptyFilters } from './search/filters';

import { dashboardMetadata } from './metadata/dashboard';

const sharedLineageItemCore = {
  badges: [],
  cluster: 'cluster',
  database: 'h',
  schema: 'schema',
  source: 'source',
  usage: 0,
};

const globalState: GlobalState = {
  announcements: {
    isLoading: false,
    statusCode: 200,
    posts: [
      {
        date: '12/31/1999',
        title: 'Y2K',
        html_content: '<div>The end of the world</div>',
      },
      {
        date: '01/01/2000',
        title: 'False Alarm',
        html_content: '<div>Just kidding</div>',
      },
    ],
  },
  bookmarks: {
    myBookmarks: {
      [ResourceType.table]: [
        {
          key: 'bookmarked_key',
          type: ResourceType.table,
          cluster: 'cluster',
          database: 'database',
          description: 'description',
          name: 'name',
          schema: 'schema',
        },
      ],
      [ResourceType.dashboard]: [
        {
          key: 'product_dashboard://cluster.group/name',
          group_name: 'Amundsen Team',
          group_url: 'product/group',
          name: 'Amundsen Metrics Dashboard1',
          product: 'mode',
          type: ResourceType.dashboard,
          description: 'I am a dashboard',
          uri: 'product_dashboard://cluster.group/name',
          url: 'product/name',
          cluster: 'cluster',
          last_successful_run_timestamp: 1585062593,
        },
      ],
    },
    myBookmarksIsLoaded: false,
    bookmarksForUser: {
      [ResourceType.table]: [],
      [ResourceType.dashboard]: [],
    },
  },
  dashboard: {
    isLoading: false,
    statusCode: 200,
    dashboard: dashboardMetadata,
  },
  feature: {
    statusCode: 200,
    isLoading: false,
    isLoadingOwners: false,
    feature: {
      key: '',
      name: '',
      version: '',
      status: '',
      feature_group: '',
      entity: '',
      data_type: '',
      availability: [],
      description: '',
      owners: [],
      badges: [],
      owner_tags: [],
      tags: [],
      programmatic_descriptions: [],
      watermarks: [],
      stats: [],
      last_updated_timestamp: 0,
      created_timestamp: 0,
    },
    featureCode: {
      isLoading: false,
      statusCode: null,
      featureCode: {
        text: '',
        source: '',
        key: '',
      },
    },
    featureLineage: {
      isLoading: false,
      statusCode: null,
      featureLineage: {
        upstream_entities: [],
        downstream_entities: [],
        depth: 0,
        direction: 'upstream',
        key: '',
      },
    },
    preview: {
      isLoading: false,
      previewData: {},
      status: null,
    },
  },
  feedback: {
    sendState: SendingState.IDLE,
  },
  issue: {
    issues: [],
    allIssuesUrl: '',
    total: 0,
    isLoading: true,
  },
  notification: {
    requestIsOpen: false,
    sendState: SendingState.IDLE,
  },
  popularResources: {
    popularResourcesIsLoaded: true,
    popularResources: {
      [ResourceType.table]: [
        {
          cluster: 'testCluster',
          database: 'testDatabase',
          description: 'I have a lot of users',
          key: 'testDatabase://testCluster.testSchema/testName',
          name: 'testName',
          schema: 'testSchema',
          type: ResourceType.table,
        },
        {
          cluster: 'testCluster',
          database: 'testDatabase',
          description: 'I also have a lot of users',
          key: 'testDatabase://testCluster.testSchema/otherName',
          name: 'otherName',
          schema: 'testSchema',
          type: ResourceType.table,
        },
      ],
    },
  },
  search: {
    search_term: 'testName',
    resource: ResourceType.table,
    isLoading: false,
    dashboards: {
      page_index: 0,
      results: [],
      total_results: 0,
    },
    features: {
      page_index: 0,
      results: [],
      total_results: 0,
    },
    tables: {
      page_index: 0,
      results: [
        {
          cluster: 'testCluster',
          database: 'testDatabase',
          description: 'I have a lot of users',
          key: 'testDatabase://testCluster.testSchema/testName',
          last_updated_timestamp: 946684799,
          name: 'testName',
          schema: 'testSchema',
          type: ResourceType.table,
        },
      ],
      total_results: 1,
    },
    users: {
      page_index: 0,
      results: [],
      total_results: 0,
    },
    inlineResults: {
      isLoading: false,
      dashboards: {
        page_index: 0,
        results: [],
        total_results: 0,
      },
      tables: {
        page_index: 0,
        results: [],
        total_results: 0,
      },
      users: {
        page_index: 0,
        results: [],
        total_results: 0,
      },
      features: {
        page_index: 0,
        results: [],
        total_results: 0,
      },
    },
    filters: defaultEmptyFilters,
  },
  tableMetadata: {
    isLoading: true,
    preview: {
      data: {},
      status: null,
    },
    statusCode: 200,
    tableData: {
      badges: [],
      cluster: '',
      columns: [],
      database: '',
      is_editable: false,
      is_view: false,
      key: '',
      last_updated_timestamp: 0,
      schema: '',
      name: '',
      description: '',
      table_writer: { application_url: '', description: '', id: '', name: '' },
      partition: { is_partitioned: false },
      table_readers: [],
      source: { source: '', source_type: '' },
      resource_reports: [],
      watermarks: [],
      programmatic_descriptions: {},
    },
    tableOwners: {
      isLoading: true,
      owners: {},
    },
  },
  lastIndexed: { lastIndexed: 1555632106 },
  tags: {
    allTags: {
      isLoading: false,
      tags: [
        {
          tag_name: 'curated_tag_1',
          tag_count: 20,
        },
        {
          tag_name: 'other_tag_1',
          tag_count: 15,
        },
        {
          tag_name: 'alphabetical_tag_1',
          tag_count: 5,
        },
        {
          tag_name: 'zero_count_tag_1',
          tag_count: 0,
        },
      ],
    },
    resourceTags: {
      isLoading: false,
      tags: [],
    },
  },
  user: {
    loggedInUser: {
      display_name: 'firstname lastname',
      email: 'test@test.com',
      employee_type: 'fulltime',
      first_name: 'firstname',
      full_name: 'firstname lastname',
      github_username: 'githubName',
      is_active: true,
      last_name: 'lastname',
      manager_fullname: 'Test Manager',
      profile_url: 'www.test.com',
      role_name: 'Tester',
      slack_id: 'www.slack.com',
      team_name: 'QA',
      user_id: 'test0',
    },
    profile: {
      own: {
        [ResourceType.table]: [
          { type: ResourceType.table },
          { type: ResourceType.table },
          { type: ResourceType.table },
        ],
        [ResourceType.dashboard]: [],
      },
      read: [{ type: ResourceType.table }, { type: ResourceType.table }],
      user: {
        display_name: 'firstname lastname',
        email: 'test@test.com',
        employee_type: 'fulltime',
        first_name: 'firstname',
        full_name: 'firstname lastname',
        github_username: 'githubName',
        is_active: true,
        last_name: 'lastname',
        manager_fullname: 'Test Manager',
        profile_url: 'www.test.com',
        role_name: 'Tester',
        slack_id: 'www.slack.com',
        team_name: 'QA',
        user_id: 'test0',
      },
    },
  },
  ui: {},
  lineage: {
    lineageTree: {
      upstream_entities: [
        {
          ...sharedLineageItemCore,
          key: 'h/parent-3',
          level: 3,
          name: 'parent-3',
          parent: '',
        },
        {
          ...sharedLineageItemCore,
          key: 'h/parent-1',
          level: 1,
          name: 'parent-1',
          parent: 'h/parent-2-solo',
        },
        {
          ...sharedLineageItemCore,
          key: 'h/parent-1',
          level: 1,
          name: 'parent-1',
          parent: 'h/parent-2',
        },

        {
          ...sharedLineageItemCore,
          key: 'h/parent-2',
          level: 2,
          name: 'parent-2',
          parent: 'h/parent-3',
        },
        {
          ...sharedLineageItemCore,
          key: 'h/parent-2-solo',
          level: 2,
          name: 'parent-2-solo',
          parent: '',
        },
      ] as LineageItem[],
      downstream_entities: [],
      key: '',
      direction: 'both',
      depth: 1,
    },
    statusCode: null,
    isLoading: false,
    columnLineageMap: {},
  },
};

export default globalState;
