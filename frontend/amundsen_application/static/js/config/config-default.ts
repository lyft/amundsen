import { AppConfig } from './config-types';

import { FilterType, ResourceType, SortDirection } from '../interfaces';

const configDefault: AppConfig = {
  badges: {},
  browse: {
    curatedTags: [],
    showAllTags: true,
  },
  date: {
    default: 'MMM DD, YYYY',
    dateTimeShort: 'MMM DD, YYYY ha z',
    dateTimeLong: 'MMMM Do YYYY [at] h:mm:ss a',
  },
  editableText: {
    tableDescLength: 750,
    columnDescLength: 250,
  },
  analytics: {
    plugins: [],
  },
  indexDashboards: {
    enabled: false,
  },
  indexUsers: {
    enabled: false,
  },
  indexFeatures: {
    enabled: false,
  },
  userIdLabel: 'email address',
  issueTracking: {
    enabled: false,
  },
  logoPath: null,
  logoTitle: 'AMUNDSEN',
  documentTitle: 'Amundsen - Data Discovery Portal',
  numberFormat: null,
  mailClientFeatures: {
    feedbackEnabled: false,
    notificationsEnabled: false,
  },
  announcements: {
    enabled: false,
  },
  navLinks: [
    {
      label: 'Announcements',
      id: 'nav::announcements',
      href: '/announcements',
      use_router: true,
    },
    {
      label: 'Browse',
      id: 'nav::browse',
      href: '/browse',
      use_router: true,
    },
  ],
  resourceConfig: {
    [ResourceType.dashboard]: {
      displayName: 'Dashboards',
      supportedSources: {
        mode: {
          displayName: 'Mode',
          iconClass: 'icon-mode',
        },
        redash: {
          displayName: 'Redash',
          iconClass: 'icon-redash',
        },
        tableau: {
          displayName: 'Tableau',
          iconClass: 'icon-tableau',
        },
        superset: {
          displayName: 'Superset',
          iconClass: 'icon-superset',
        },
      },
      filterCategories: [
        {
          categoryId: 'product',
          displayName: 'Product',
          helpText: 'Enter exact product name or a regex wildcard pattern',
          type: FilterType.INPUT_SELECT,
        },
        {
          categoryId: 'group_name',
          displayName: 'Group',
          helpText: 'Enter exact group name or a regex wildcard pattern',
          type: FilterType.INPUT_SELECT,
        },
        {
          categoryId: 'name',
          displayName: 'Name',
          helpText: 'Enter exact dashboard name or a regex wildcard pattern',
          type: FilterType.INPUT_SELECT,
        },
        {
          categoryId: 'tag',
          displayName: 'Tag',
          helpText: 'Enter exact tag name or a regex wildcard pattern',
          type: FilterType.INPUT_SELECT,
        },
      ],
      notices: {},
    },
    [ResourceType.feature]: {
      displayName: 'ML Features',
      supportedSources: {
        bigquery: {
          displayName: 'BigQuery',
          iconClass: 'icon-bigquery',
        },
        delta: {
          displayName: 'Delta',
          iconClass: 'icon-delta',
        },
        dremio: {
          displayName: 'Dremio',
          iconClass: 'icon-dremio',
        },
        druid: {
          displayName: 'Druid',
          iconClass: 'icon-druid',
        },
        hive: {
          displayName: 'Hive',
          iconClass: 'icon-hive',
        },
        presto: {
          displayName: 'Presto',
          iconClass: 'icon-presto',
        },
        postgres: {
          displayName: 'Postgres',
          iconClass: 'icon-postgres',
        },
        redshift: {
          displayName: 'Redshift',
          iconClass: 'icon-redshift',
        },
        snowflake: {
          displayName: 'Snowflake',
          iconClass: 'icon-snowflake',
        },
      },
    },
    [ResourceType.table]: {
      displayName: 'Datasets',
      supportedSources: {
        bigquery: {
          displayName: 'BigQuery',
          iconClass: 'icon-bigquery',
        },
        delta: {
          displayName: 'Delta',
          iconClass: 'icon-delta',
        },
        dremio: {
          displayName: 'Dremio',
          iconClass: 'icon-dremio',
        },
        druid: {
          displayName: 'Druid',
          iconClass: 'icon-druid',
        },
        hive: {
          displayName: 'Hive',
          iconClass: 'icon-hive',
        },
        presto: {
          displayName: 'Presto',
          iconClass: 'icon-presto',
        },
        postgres: {
          displayName: 'Postgres',
          iconClass: 'icon-postgres',
        },
        redshift: {
          displayName: 'Redshift',
          iconClass: 'icon-redshift',
        },
        snowflake: {
          displayName: 'Snowflake',
          iconClass: 'icon-snowflake',
        },
        elasticsearch: {
          displayName: 'Elasticsearch',
          iconClass: 'icon-elasticsearch',
        },
      },
      filterCategories: [
        {
          categoryId: 'database',
          displayName: 'Source',
          helpText: 'Enter exact database name or a regex wildcard pattern',
          type: FilterType.INPUT_SELECT,
        },
        {
          categoryId: 'column',
          displayName: 'Column',
          helpText: 'Enter exact column name or a regex wildcard pattern',
          type: FilterType.INPUT_SELECT,
        },
        {
          categoryId: 'schema',
          displayName: 'Schema',
          helpText: 'Enter exact schema name or a regex wildcard pattern',
          type: FilterType.INPUT_SELECT,
        },
        {
          categoryId: 'table',
          displayName: 'Table',
          helpText: 'Enter exact table name or a regex wildcard pattern',
          type: FilterType.INPUT_SELECT,
        },
        {
          categoryId: 'tag',
          displayName: 'Tag',
          helpText: 'Enter exact tag name or a regex wildcard pattern',
          type: FilterType.INPUT_SELECT,
        },
      ],
      sortCriterias: {
        sort_order: {
          name: 'Table Default',
          key: 'sort_order',
          direction: SortDirection.ascending,
        },
        name: {
          name: 'Alphabetical',
          key: 'name',
          direction: SortDirection.descending,
        },
      },
      supportedDescriptionSources: {
        dremio: {
          displayName: 'Dremio',
          iconPath: '/static/images/icons/logo-dremio.svg',
        },
        github: {
          displayName: 'Github',
          iconPath: '/static/images/github.png',
        },
      },
      notices: {},
    },
    [ResourceType.feature]: {
      displayName: 'ML Features',
      supportedSources: {
        hive: {
          displayName: 'Hive',
          iconClass: 'icon-hive',
        },
      },
      filterCategories: [
        {
          categoryId: 'entity',
          displayName: 'Entity',
          helpText: 'Enter exact entity name or a regex wildcard pattern',
          type: FilterType.INPUT_SELECT,
        },
        {
          categoryId: 'name',
          displayName: 'Feature Name',
          helpText: 'Enter exact feature name or a regex wildcard pattern',
          type: FilterType.INPUT_SELECT,
        },
        {
          categoryId: 'group',
          displayName: 'Feature Group',
          helpText:
            'Enter exact feature group name or a regex wildcard pattern',
          type: FilterType.INPUT_SELECT,
        },
        {
          categoryId: 'tag',
          displayName: 'Tag',
          helpText: 'Enter exact tag name or a regex wildcard pattern',
          type: FilterType.INPUT_SELECT,
        },
      ],
      notices: {},
    },
    [ResourceType.user]: {
      displayName: 'People',
    },
  },
  featureLineage: {
    inAppListEnabled: false,
  },
  tableLineage: {
    inAppListEnabled: false,
    inAppPageEnabled: false,
    externalEnabled: false,
    iconPath: 'PATH_TO_ICON',
    isBeta: false,
    urlGenerator: (
      database: string,
      cluster: string,
      schema: string,
      table: string
    ) =>
      `https://DEFAULT_LINEAGE_URL?schema=${schema}&cluster=${cluster}&db=${database}&table=${table}`,
  },
  columnLineage: {
    inAppListEnabled: false,
    inAppPageEnabled: false,
    urlGenerator: (
      database: string,
      cluster: string,
      schema: string,
      table: string,
      column: string
    ) =>
      `https://DEFAULT_LINEAGE_URL?schema=${schema}&cluster=${cluster}&db=${database}&table=${table}&column=${column}`,
  },
  tableProfile: {
    isBeta: false,
    isExploreEnabled: false,
    exploreUrlGenerator: (
      database: string,
      cluster: string,
      schema: string,
      table: string,
      partitionKey?: string,
      partitionValue?: string
    ) =>
      `https://DEFAULT_EXPLORE_URL?schema=${schema}&cluster=${cluster}&db=${database}&table=${table}`,
  },
};

export default configDefault;
