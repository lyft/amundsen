import { ResourceType } from 'interfaces';

export const defaultEmptyFilters = {
  [ResourceType.table]: {},
};

export const datasetFilterExample = {
  [ResourceType.table]: {
    schema: 'schema_name',
    database: {
      hive: true,
    },
  },
};
