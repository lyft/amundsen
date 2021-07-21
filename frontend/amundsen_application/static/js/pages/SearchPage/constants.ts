import { ResourceType } from 'interfaces/Resources';
import { getDisplayNameByResource } from 'config/config-utils';

export const PAGINATION_PAGE_RANGE = 10;
export const RESULTS_PER_PAGE = 10;

// TODO: Hard-coded text strings should be translatable/customizable
export const DOCUMENT_TITLE_SUFFIX = ' - Amundsen Search';
export const SEARCHPAGE_TITLE = 'Amundsen Search';

export const PAGE_INDEX_ERROR_MESSAGE =
  'Page index out of bounds for available matches';

export const SEARCH_DEFAULT_MESSAGE =
  'Your search results will be shown here.\n\
Try entering a search term or using any of the filters to the left.';

export const SEARCH_SOURCE_NAME = 'search_results';
export const SEARCH_ERROR_MESSAGE_PREFIX = 'Your search did not match any ';
export const SEARCH_ERROR_MESSAGE_SUFFIX = ' results';

export const RESOURCE_SELECTOR_TITLE = 'Resource';
export const DASHBOARD_RESOURCE_TITLE = getDisplayNameByResource(
  ResourceType.dashboard
);
export const TABLE_RESOURCE_TITLE = getDisplayNameByResource(
  ResourceType.table
);
export const USER_RESOURCE_TITLE = getDisplayNameByResource(ResourceType.user);
export const FEATURE_RESOURCE_TITLE = getDisplayNameByResource(
  ResourceType.feature
);
