// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import { User } from './User';
import { Badge } from './Badges';
import { Tag } from './Tags';
import { ProgrammaticDescription } from './TableMetadata';

export interface FeatureMetadata {
  key: string;
  name: string;
  version: string;
  status: string;
  feature_group: string;
  entity?: string;
  data_type?: string;
  availability: string[];
  description: string;
  owners: User[];
  badges: Badge[];
  owner_tags?: Tag[];
  tags: Tag[];
  programmatic_descriptions: ProgrammaticDescription[];
  watermarks: FeatureWatermark[];
  stats: FeatureStats[];
  last_updated_timestamp: number;
  created_timestamp: number;
  partition_column?: string;
}

// TODO - duplicated with FeatureResource in Resources.ts. Might delete this.
export interface FeatureSummary {
  key: string;
  name: string;
  version: string;
  availability: string[];
  entity?: string[];
  description: string;
}

// TODO - Figure out if we can reuse ColumnStats
export interface FeatureStats {
  name: string;
}

export interface FeatureWatermark {
  key: string;
  watermark_type: string;
  time: string;
}

export interface FeaturePreviewQueryParams {
  feature_name: string;
  feature_group: string;
  version: string;
}

export interface FeatureCode {
  key: string;
  source: string;
  text: string;
}
