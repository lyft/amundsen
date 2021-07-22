export enum UpdateMethod {
  PUT = 'PUT',
  DELETE = 'DELETE',
}

export enum FilterType {
  CHECKBOX_SELECT = 'checkboxFilter',
  INPUT_SELECT = 'inputFilter',
}

export enum SearchType {
  CLEAR_TERM = 'clear_search_term',
  FILTER = 'update_filter',
  INLINE_SEARCH = 'inline_search',
  INLINE_SELECT = 'inline_select',
  LOAD_URL = 'load_url',
  PAGINATION = 'update_page',
  SUBMIT_TERM = 'submit_search_term',
}

// Image-based Icon types from _icons.scss
export enum ImageIconType {
  ALERT = 'icon-alert',
  BOOKMARK = 'icon-bookmark',
  BOOKMARK_FILLED = 'icon-bookmark-filled',
  DELETE = 'icon-delete',
  RED_TRIANGLE_WARNING = 'icon-red-triangle-warning',
  DOWN = 'icon-down',
  EDIT = 'icon-edit',
  HELP = 'icon-help',
  GITHUB = 'icon-github',
  LEFT = 'icon-left',
  LOADING = 'icon-loading',
  MAIL = 'icon-mail',
  PLUS = 'icon-plus',
  PLUS_CIRCLE = 'icon-plus-circle',
  PREVIEW = 'icon-preview',
  REFRESH = 'icon-refresh',
  RIGHT = 'icon-right',
  SEARCH = 'icon-search',
  SEND = 'icon-send',
  SLACK = 'icon-slack',
  UP = 'icon-up',
  USER = 'icon-user',
  MORE = 'icon-more',
}

// Icon types from _icons.scss
export enum IconType {
  CHECK = 'icon-check',
  USERS = 'icon-users',
  DASHBOARD = 'icon-dashboard',
  MODE = 'icon-mode',
  REDASH = 'icon-redash',
  TABLEAU = 'icon-tableau',
  DATABASE = 'icon-database',
  HIVE = 'icon-hive',
  BIGQUERY = 'icon-bigquery',
  DREMIO = 'icon-dremio',
  DRUID = 'icon-druid',
  ORACLE = 'icon-oracle',
  PRESTO = 'icon-presto',
  POSTGRES = 'icon-postgres',
  REDSHIFT = 'icon-redshift',
  SNOWFLAKE = 'icon-snowflake',
  SUPERSET = 'icon-superset',
  ELASTICSEARCH = 'icon-elasticsearch',
}

// Icon sizes
export enum IconSizes {
  REGULAR = 24,
  SMALL = 16,
}
