import { FeatureResource, ResourceType } from 'interfaces';
import { FeatureCode } from 'interfaces/Feature';
import { Lineage } from 'interfaces/Lineage';

export const featureSummary: FeatureResource = {
  type: ResourceType.feature,
  description: 'I am an ML feature',
  key: 'test_feature_group/test_feature_name/1.4',
  name: 'test_feature_name',
  feature_group: 'test_feature_group',
  version: '1.4',
  availability: ['hive'],
  entity: 'test_entity',
  badges: [{ tag_name: 'pii' }],
};

export const featureMetadata = {
  availability: ['hive'],
  badges: [],
  created_timestamp: 946683711,
  description: 'I am an ML feature',
  entity: 'test_entity',
  feature_group: 'test_feature_group',
  key: 'test_feature_group/test_feature_name/1.4',
  last_updated_timestamp: 946684799,
  name: 'test_feature_name',
  owners: [],
  partition_column: 'ds',
  programmatic_descriptions: [],
  status: 'active',
  stats: [],
  tags: [],
  type: ResourceType.feature,
  version: '1.4',
  watermarks: [],
};

export const featureCode: FeatureCode = {
  source: 'testSource',
  key: 'testKey',
  text: 'testText',
};

export const featureLineage: Lineage = {
  downstream_entities: [],
  upstream_entities: [],
  key: 'testKey',
  depth: 1,
  direction: 'upstream',
};

export const previewData = {
  isLoading: false,
  data: {},
  status: null,
};
