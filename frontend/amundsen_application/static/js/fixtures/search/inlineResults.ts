import { ResourceType } from 'interfaces';

export const isLoadingExample = {
  isLoading: true,
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
    results: [],
    total_results: 0,
  },
  users: {
    page_index: 0,
    results: [],
    total_results: 0,
  },
};

export const noResultsExample = {
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
    results: [],
    total_results: 0,
  },
  users: {
    page_index: 0,
    results: [],
    total_results: 0,
  },
};

export const allResourcesExample = {
  isLoading: false,
  dashboards: {
    page_index: 0,
    results: [
      {
        group_name: 'Amundsen Team',
        name: 'Amundsen Metrics Dashboard1',
        product: 'mode',
        type: 'dashoard',
        description: 'I am a dashboard',
        uri: 'product_dashboard://cluster.group/name',
        url: 'product/name',
        cluster: 'cluster',
        last_successful_run_timestamp: 1585062593,
      },
    ],
    total_results: 1,
  },
  features: {
    page_index: 0,
    results: [
      {
        description: 'I am an ML feature',
        key: 'test_feature_group/test_feature_name/1.4',
        last_updated_timestamp: 946684799,
        name: 'test_feature_name',
        feature_group: 'test_feature_group',
        version: '1.4',
        availability: ['hive'],
        entity: 'test_entity',
        type: ResourceType.feature,
        badges: [],
      },
    ],
    total_results: 1,
  },
  tables: {
    page_index: 0,
    results: [
      {
        cluster: 'testCluster',
        database: 'testDatabase',
        description: 'I have a lot of users',
        key: 'testDatabase://testCluster.testSchema/testName1',
        last_updated_timestamp: 946684799,
        name: 'testName1',
        schema: 'testSchema',
        type: ResourceType.table,
      },
      {
        cluster: 'testCluster',
        database: 'testDatabase',
        description: 'I have a lot of users',
        key: 'testDatabase://testCluster.testSchema/testName2',
        last_updated_timestamp: 946684799,
        name: 'testName2',
        schema: 'testSchema',
        type: ResourceType.table,
      },
      {
        cluster: 'testCluster',
        database: 'testDatabase',
        description: 'I have a lot of users',
        key: 'testDatabase://testCluster.testSchema/testName3',
        last_updated_timestamp: 946684799,
        name: 'testName3',
        schema: 'testSchema',
        type: ResourceType.table,
      },
    ],
    total_results: 3,
  },
  users: {
    page_index: 0,
    results: [
      {
        display_name: 'Test User',
        email: 'tuser@test.com',
        employee_type: '',
        first_name: 'Test',
        full_name: 'Test User',
        github_username: '',
        is_active: true,
        last_name: 'User',
        manager_email: 'tuser2@test.com',
        manager_fullname: 'Test User2',
        profile_url: '',
        role_name: undefined,
        slack_id: '',
        team_name: 'Amundsen Team',
        type: 'user',
        user_id: 'tuser@test.com',
      },
      {
        display_name: 'Test User2',
        email: 'tuser2@test.com',
        employee_type: '',
        first_name: 'Test',
        full_name: 'Test User2',
        github_username: '',
        is_active: true,
        last_name: 'User2',
        manager_email: 'tuser3@test.com',
        manager_fullname: 'Test User3',
        profile_url: '',
        role_name: undefined,
        slack_id: '',
        team_name: 'Amundsen Team',
        type: 'user',
        user_id: 'tuser2@test.com',
      },
    ],
    total_results: 2,
  },
};
