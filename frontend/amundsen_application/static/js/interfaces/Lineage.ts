import { Badge } from './Badges';

export interface LineageItem {
  badges: Badge[];
  cluster: string;
  database: string;
  key: string;
  level: number;
  name: string;
  schema: string;
  parent: string | null;
  usage: number | null;
  source?: string;
}

export interface Lineage {
  key?: string;
  direction?: string;
  depth?: number;
  downstream_entities: LineageItem[];
  upstream_entities: LineageItem[];
}

export interface TableLineageParams {
  key: string;
  direction: string;
  depth: number;
}

export interface ColumnLineageParams {
  key: string;
  direction: string;
  depth: number;
  column: string;
}

// To keep the backward compatibility for the list based lineage
// ToDo: Please remove once list based view is deprecated
export interface ColumnLineageMap {
  [columnName: string]: {
    lineageTree: Lineage;
    isLoading: boolean;
  };
}
