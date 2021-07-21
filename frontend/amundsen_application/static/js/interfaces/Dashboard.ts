import { User } from 'interfaces/User';
import { Tag } from 'interfaces/Tags';
import { Badge } from 'interfaces/Badges';
import { TableReader } from 'interfaces/TableMetadata';
import { TableResource, QueryResource } from 'interfaces/Resources';

export interface DashboardMetadata {
  badges: Badge[];
  chart_names: string[];
  cluster: string;
  created_timestamp: number;
  description: string;
  frequent_users: TableReader[];
  group_name: string;
  group_url: string;
  last_run_state: string;
  last_run_timestamp: number | null;
  last_successful_run_timestamp: number | null;
  name: string;
  owners: User[];
  product: string;
  queries: QueryResource[];
  recent_view_count: number;
  tables: TableResource[];
  tags: Tag[];
  updated_timestamp: number;
  uri: string;
  url: string;
}
