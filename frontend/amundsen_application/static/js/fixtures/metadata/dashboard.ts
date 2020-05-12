import { DashboardResource, ResourceType } from 'interfaces';

export const dashboardSummary: DashboardResource = {
  group_name: 'Amundsen Team',
  group_url: 'product/group',
  name: 'Amundsen Metrics Dashboard1',
  product: 'mode',
  type: ResourceType.dashboard,
  description: 'I am a dashboard',
  uri: 'product_dashboard://cluster.group/name',
  url: 'product/name',
  cluster: 'cluster',
  last_successful_run_timestamp: 1585062593
};

export const dashboardMetadata = {
  badges: [],
  chart_names: ["chart 1", "chart 2"],
  cluster: "gold",
  created_timestamp: 1581023497,
  description: "TEST description name",
  frequent_users: [],
  group_name: "test_group_name",
  group_url: "test_group_url",
  last_run_state: "succeeded",
  last_run_timestamp: 1586812894,
  last_successful_run_timestamp: 1586812894,
  name: "Test Dashboard Name",
  owners: [
    {
      display_name: "test",
      email: "test@email.com",
      employee_type: "teamMember",
      first_name: "first",
      full_name: "first last",
      github_username: "",
      is_active: true,
      last_name: "last",
      manager_email: null,
      manager_fullname: "",
      profile_url: "profile_url",
      role_name: "SWE",
      slack_id: "",
      team_name: "team name",
      user_id: "user_id",
    }
  ],
  product: 'mode',
  query_names: ["query 1", "query 2"],
  recent_view_count: 10,
  tables: [],
  tags: [],
  updated_timestamp: 1586672811,
  uri: "test_uri",
  url: "test_url",
};
