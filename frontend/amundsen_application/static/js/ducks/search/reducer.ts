import { ResourceType, SearchType } from 'interfaces';

import { Search as UrlSearch } from 'history';

import filterReducer, {
  initialFilterState,
  FilterReducerState,
} from './filters/reducer';

import {
  DashboardSearchResults,
  SearchAll,
  SearchAllRequest,
  SearchAllResponse,
  SearchAllResponsePayload,
  SearchResource,
  SearchResponsePayload,
  SearchResourceRequest,
  SearchResourceResponse,
  InlineSearch,
  InlineSearchRequest,
  InlineSearchResponse,
  InlineSearchResponsePayload,
  InlineSearchUpdatePayload,
  InlineSearchSelect,
  InlineSearchUpdate,
  TableSearchResults,
  UserSearchResults,
  SubmitSearchRequest,
  SubmitSearch,
  SubmitSearchResourcePayload,
  SubmitSearchResourceRequest,
  SubmitSearchResource,
  LoadPreviousSearchRequest,
  LoadPreviousSearch,
  UpdateSearchStateRequest,
  UpdateSearchStateReset,
  UpdateSearchStatePayload,
  UpdateSearchState,
  UrlDidUpdateRequest,
  UrlDidUpdate,
  FeatureSearchResults,
} from './types';

export interface SearchReducerState {
  search_term: string;
  resource: ResourceType;
  isLoading: boolean;
  dashboards: DashboardSearchResults;
  features: FeatureSearchResults;
  tables: TableSearchResults;
  users: UserSearchResults;
  inlineResults: {
    isLoading: boolean;
    dashboards: DashboardSearchResults;
    tables: TableSearchResults;
    users: UserSearchResults;
    features: FeatureSearchResults;
  };
  filters: FilterReducerState;
}

/* ACTIONS */
export function searchAll(
  searchType: SearchType,
  term: string,
  resource: ResourceType,
  pageIndex: number,
  useFilters: boolean = false
): SearchAllRequest {
  return {
    payload: {
      resource,
      pageIndex,
      term,
      useFilters,
      searchType,
    },
    type: SearchAll.REQUEST,
  };
}
export function searchAllSuccess(
  searchResults: SearchAllResponsePayload
): SearchAllResponse {
  return { type: SearchAll.SUCCESS, payload: searchResults };
}
export function searchAllFailure(): SearchAllResponse {
  return { type: SearchAll.FAILURE };
}

export function searchResource(
  searchType: SearchType,
  term: string,
  resource: ResourceType,
  pageIndex: number
): SearchResourceRequest {
  return {
    payload: {
      pageIndex,
      term,
      resource,
      searchType,
    },
    type: SearchResource.REQUEST,
  };
}
export function searchResourceSuccess(
  searchResults: SearchResponsePayload
): SearchResourceResponse {
  return { type: SearchResource.SUCCESS, payload: searchResults };
}
export function searchResourceFailure(): SearchResourceResponse {
  return { type: SearchResource.FAILURE };
}

export function getInlineResultsDebounce(term: string): InlineSearchRequest {
  return {
    payload: {
      term,
    },
    type: InlineSearch.REQUEST_DEBOUNCE,
  };
}
export function getInlineResults(term: string): InlineSearchRequest {
  return {
    payload: {
      term,
    },
    type: InlineSearch.REQUEST,
  };
}
export function getInlineResultsSuccess(
  inlineResults: InlineSearchResponsePayload
): InlineSearchResponse {
  return { type: InlineSearch.SUCCESS, payload: inlineResults };
}
export function getInlineResultsFailure(): InlineSearchResponse {
  return { type: InlineSearch.FAILURE };
}

export function selectInlineResult(
  resourceType: ResourceType,
  searchTerm: string,
  updateUrl: boolean = false
): InlineSearchSelect {
  return {
    payload: {
      resourceType,
      searchTerm,
      updateUrl,
    },
    type: InlineSearch.SELECT,
  };
}

export function updateFromInlineResult(
  data: InlineSearchUpdatePayload
): InlineSearchUpdate {
  return {
    payload: data,
    type: InlineSearch.UPDATE,
  };
}

export function submitSearch({
  searchTerm,
  useFilters,
}: {
  searchTerm: string;
  useFilters: boolean;
}): SubmitSearchRequest {
  return {
    payload: { searchTerm, useFilters },
    type: SubmitSearch.REQUEST,
  };
}

export function submitSearchResource({
  resourceFilters,
  pageIndex,
  searchTerm,
  resource,
  searchType,
  updateUrl,
}: SubmitSearchResourcePayload): SubmitSearchResourceRequest {
  return {
    payload: {
      resourceFilters,
      pageIndex,
      searchTerm,
      resource,
      searchType,
      updateUrl,
    },
    type: SubmitSearchResource.REQUEST,
  };
}

export function updateSearchState({
  filters,
  resource,
  updateUrl,
  submitSearch,
}: UpdateSearchStatePayload): UpdateSearchStateRequest {
  return {
    payload: {
      filters,
      resource,
      updateUrl,
      submitSearch,
    },
    type: UpdateSearchState.REQUEST,
  };
}
export function resetSearchState(): UpdateSearchStateReset {
  return {
    type: UpdateSearchState.RESET,
  };
}

export function loadPreviousSearch(): LoadPreviousSearchRequest {
  return {
    type: LoadPreviousSearch.REQUEST,
  };
}

export function urlDidUpdate(urlSearch: UrlSearch): UrlDidUpdateRequest {
  return {
    payload: { urlSearch },
    type: UrlDidUpdate.REQUEST,
  };
}

/* REDUCER */
export const initialInlineResultsState = {
  isLoading: false,
  dashboards: {
    page_index: 0,
    results: [],
    total_results: 0,
  },
  features: {
    page_index: 0,
    results: [],
    total_results: 0,
  },
  tables: {
    page_index: 0,
    results: [],
    total_results: 0,
  },
  users: {
    page_index: 0,
    results: [],
    total_results: 0,
  },
};
export const initialState: SearchReducerState = {
  search_term: '',
  isLoading: false,
  resource: ResourceType.table,
  dashboards: {
    page_index: 0,
    results: [],
    total_results: 0,
  },
  tables: {
    page_index: 0,
    results: [],
    total_results: 0,
  },
  users: {
    page_index: 0,
    results: [],
    total_results: 0,
  },
  features: {
    page_index: 0,
    results: [],
    total_results: 0,
  },
  filters: initialFilterState,
  inlineResults: initialInlineResultsState,
};

export default function reducer(
  state: SearchReducerState = initialState,
  action
): SearchReducerState {
  switch (action.type) {
    case SubmitSearch.REQUEST:
      return {
        ...state,
        isLoading: true,
        search_term: action.payload.searchTerm,
      };
    case SubmitSearchResource.REQUEST:
      return {
        ...state,
        isLoading: true,
        filters: filterReducer(state.filters, action),
        search_term: action.payload.searchTerm || state.search_term,
      };
    case UpdateSearchState.REQUEST:
      const { payload } = action;
      return {
        ...state,
        filters: payload.filters || state.filters,
        resource: payload.resource || state.resource,
      };
    case UpdateSearchState.RESET:
      return initialState;
    case SearchAll.REQUEST:
      return {
        ...state,
        inlineResults: {
          ...initialInlineResultsState,
        },
        search_term: (<SearchAllRequest>action).payload.term,
        isLoading: true,
      };
    case SearchResource.REQUEST:
      return {
        ...state,
        isLoading: true,
      };
    case SearchAll.SUCCESS:
      // resets all resources with initial state then applies search results
      const newState = (<SearchAllResponse>action).payload;
      if (newState === undefined) {
        throw Error(
          'SearchAllResponse.payload must be specified for SUCCESS type'
        );
      }
      return {
        ...initialState,
        ...newState,
        filters: state.filters,
        inlineResults: {
          dashboards: newState.dashboards,
          features: newState.features,
          tables: newState.tables,
          users: newState.users,
          isLoading: false,
        },
      };
    case SearchResource.SUCCESS:
      // resets only a single resource and preserves search state for other resources
      const resourceNewState = (<SearchResourceResponse>action).payload;
      return {
        ...state,
        ...resourceNewState,
        isLoading: false,
      };
    case SearchAll.FAILURE:
    case SearchResource.FAILURE:
      return {
        ...initialState,
        search_term: state.search_term,
      };
    case InlineSearch.UPDATE:
      const { searchTerm, resource, dashboards, features, tables, users } = (<
        InlineSearchUpdate
      >action).payload;
      return {
        ...state,
        resource,
        dashboards,
        features,
        tables,
        users,
        search_term: searchTerm,
        filters: initialFilterState,
      };
    case InlineSearch.SUCCESS:
      const inlineResults = (<InlineSearchResponse>action).payload;
      if (inlineResults === undefined) {
        throw Error(
          'InlineSearchResponse.payload must be specified for SUCCESS type'
        );
      }
      return {
        ...state,
        inlineResults: {
          dashboards: inlineResults.dashboards,
          features: inlineResults.features,
          tables: inlineResults.tables,
          users: inlineResults.users,
          isLoading: false,
        },
      };
    case InlineSearch.FAILURE:
      return {
        ...state,
        inlineResults: {
          ...initialInlineResultsState,
        },
      };
    case InlineSearch.REQUEST:
    case InlineSearch.REQUEST_DEBOUNCE:
      return {
        ...state,
        inlineResults: {
          ...initialInlineResultsState,
          isLoading: true,
        },
      };
    default:
      return state;
  }
}
