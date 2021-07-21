import * as qs from 'simple-query-string';
import { createBrowserHistory } from 'history';

import { ResourceType, TableMetadata } from 'interfaces';

// https://github.com/ReactTraining/react-router/issues/3972#issuecomment-264805667
export const BrowserHistory = createBrowserHistory();

export interface SearchParams {
  term?: string;
  resource?: ResourceType;
  index?: number;
  filters?: {};
}

export interface TablePageParams {
  database: string;
  cluster: string;
  schema: string;
  table: string;
}

export const DEFAULT_SEARCH_ROUTE = '/search';

export const generateSearchUrl = (searchParams: SearchParams): string => {
  const filtersForResource =
    (searchParams.filters &&
      searchParams.resource &&
      searchParams.filters[searchParams.resource]) ||
    {};
  const hasFilters = Object.keys(filtersForResource).length > 0;

  // If there is no search input return the search route url
  if (!searchParams.term && !hasFilters) {
    return DEFAULT_SEARCH_ROUTE;
  }

  // Explicitly list out parameters to ensure consistent URL format
  const queryStringValues = {
    term: searchParams.term || undefined,
    resource: searchParams.resource,
    index: searchParams.index,
  };
  if (hasFilters) {
    // eslint-disable-next-line @typescript-eslint/dot-notation
    queryStringValues['filters'] = filtersForResource;
  }

  const urlParams = qs.stringify(queryStringValues);
  return `${DEFAULT_SEARCH_ROUTE}?${urlParams}`;
};

export const updateSearchUrl = (
  searchParams: SearchParams,
  replace: boolean = false
) => {
  const newUrl = generateSearchUrl(searchParams);

  if (replace) {
    BrowserHistory.replace(newUrl);
  } else {
    BrowserHistory.push(newUrl);
  }
};

/**
 * Creates a table key for endpoints from url params.
 * @param TablePageParams Route params with expectations of matching a Table resource
 * @return String Params formatted as a table key.
 */
export const buildTableKey = (params: TablePageParams) =>
  `${params.database}://${params.cluster}.${params.schema}/${params.table}`;

/**
 * Create a lineage path from table metadata.
 * @param TableMetadata - information on table properties.
 * @return String Params formatted a path to a lineage table.
 */
export const buildLineageURL = ({
  cluster,
  database,
  schema,
  name,
}: Partial<TableMetadata>) =>
  `/lineage/table/${cluster}/${database}/${schema}/${name}`;

/**
 * Creates the dashboard detail URL from the URI
 * @param URI String  URI of the dashboard, it has this shape: uri = "<product>_dashboard://<cluster>.<groupID>/<dashboardID>"
 * @return String     Dashboard Detail page URL
 */
export const buildDashboardURL = (URI: string) =>
  `/dashboard/${encodeURIComponent(URI)}`;
