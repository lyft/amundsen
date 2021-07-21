import { GlobalState } from 'ducks/rootReducer';
import { SearchReducerState } from 'ducks/search/reducer';
import { DEFAULT_RESOURCE_TYPE, ResourceType } from 'interfaces/Resources';

export const getSearchState = (state: GlobalState): SearchReducerState =>
  state.search;

/*
TODO: Coupling the shape of the search state and search response requires the use of
Partial to resolve errors, removing type safty of these methods. We should
restructure any logic that takes of advantage of the case where the shape of the response
and the shape of the state happend to be the same because a piece of application state
can be the combination of multiple responses.
*/

export const getPageIndex = (
  state: Partial<SearchReducerState>,
  resource?: ResourceType
) => {
  resource = resource || state.resource;
  switch (resource) {
    case ResourceType.table:
      return state.tables?.page_index || 0;
    case ResourceType.user:
      return state.users?.page_index || 0;
    case ResourceType.dashboard:
      return state.dashboards?.page_index || 0;
  }
  return 0;
};

export const autoSelectResource = (state: Partial<SearchReducerState>) => {
  if (state.tables && state.tables.total_results > 0) {
    return ResourceType.table;
  }
  if (state.users && state.users.total_results > 0) {
    return ResourceType.user;
  }
  if (state.dashboards && state.dashboards.total_results > 0) {
    return ResourceType.dashboard;
  }
  return DEFAULT_RESOURCE_TYPE;
};
