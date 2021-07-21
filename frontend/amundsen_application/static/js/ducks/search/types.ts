import { Search as UrlSearch } from 'history';

import {
  DashboardResource,
  FeatureResource,
  Resource,
  ResourceType,
  SearchType,
  TableResource,
  UserResource,
} from 'interfaces';

import {
  FilterReducerState,
  ResourceFilterReducerState,
} from 'ducks/search/filters/reducer';

export interface SearchResults<T extends Resource> {
  page_index: number;
  total_results: number;
  results: T[];
}
export type DashboardSearchResults = SearchResults<DashboardResource>;
export type FeatureSearchResults = SearchResults<FeatureResource>;
export type TableSearchResults = SearchResults<TableResource>;
export type UserSearchResults = SearchResults<UserResource>;

export interface SearchResponsePayload {
  search_term: string;
  dashboards?: DashboardSearchResults;
  features?: FeatureSearchResults;
  tables?: TableSearchResults;
  users?: UserSearchResults;
}
export interface SearchAllResponsePayload extends SearchResponsePayload {
  resource: ResourceType;
  dashboards: DashboardSearchResults;
  features: FeatureSearchResults;
  tables: TableSearchResults;
  users: UserSearchResults;
}
export interface InlineSearchResponsePayload {
  dashboards: DashboardSearchResults;
  features: FeatureSearchResults;
  tables: TableSearchResults;
  users: UserSearchResults;
}
export interface InlineSearchUpdatePayload {
  searchTerm: string;
  resource: ResourceType;
  dashboards: DashboardSearchResults;
  features: FeatureSearchResults;
  tables: TableSearchResults;
  users: UserSearchResults;
}

export enum SearchAll {
  REQUEST = 'amundsen/search/SEARCH_ALL_REQUEST',
  SUCCESS = 'amundsen/search/SEARCH_ALL_SUCCESS',
  FAILURE = 'amundsen/search/SEARCH_ALL_FAILURE',
}
export interface SearchAllRequest {
  payload: {
    resource: ResourceType;
    pageIndex: number;
    term: string;
    useFilters?: boolean;
    searchType: SearchType;
  };
  type: SearchAll.REQUEST;
}
export interface SearchAllResponse {
  type: SearchAll.SUCCESS | SearchAll.FAILURE;
  payload?: SearchAllResponsePayload;
}

export enum SearchResource {
  REQUEST = 'amundsen/search/SEARCH_RESOURCE_REQUEST',
  SUCCESS = 'amundsen/search/SEARCH_RESOURCE_SUCCESS',
  FAILURE = 'amundsen/search/SEARCH_RESOURCE_FAILURE',
}
export interface SearchResourceRequest {
  payload: {
    pageIndex: number;
    resource: ResourceType;
    term: string;
    searchType: SearchType;
  };
  type: SearchResource.REQUEST;
}
export interface SearchResourceResponse {
  type: SearchResource.SUCCESS | SearchResource.FAILURE;
  payload?: SearchResponsePayload;
}

export enum InlineSearch {
  REQUEST = 'amundsen/search/INLINE_SEARCH_REQUEST',
  REQUEST_DEBOUNCE = 'amundsen/search/INLINE_SEARCH_REQUEST_DEBOUNCE',
  SELECT = 'amundsen/search/INLINE_SEARCH_SELECT',
  SUCCESS = 'amundsen/search/INLINE_SEARCH_SUCCESS',
  FAILURE = 'amundsen/search/INLINE_SEARCH_FAILURE',
  UPDATE = 'amundsen/search/INLINE_SEARCH_UPDATE',
}
export interface InlineSearchRequest {
  payload: {
    term: string;
  };
  type: InlineSearch.REQUEST | InlineSearch.REQUEST_DEBOUNCE;
}
export interface InlineSearchResponse {
  type: InlineSearch.SUCCESS | InlineSearch.FAILURE;
  payload?: InlineSearchResponsePayload;
}
export interface InlineSearchSelect {
  payload: {
    resourceType: ResourceType;
    searchTerm: string;
    updateUrl: boolean;
  };
  type: InlineSearch.SELECT;
}
export interface InlineSearchUpdate {
  payload: InlineSearchUpdatePayload;
  type: InlineSearch.UPDATE;
}

export enum SubmitSearch {
  REQUEST = 'amundsen/search/SUBMIT_SEARCH_REQUEST',
}
export interface SubmitSearchRequest {
  payload: {
    searchTerm: string;
    useFilters: boolean;
  };
  type: SubmitSearch.REQUEST;
}

export enum SubmitSearchResource {
  REQUEST = 'amundsen/search/SUBMIT_SEARCH_RESOURCE_REQUEST',
}
export type SubmitSearchResourcePayload = {
  pageIndex: number;
  searchType: SearchType;
  updateUrl?: boolean;
  resourceFilters?: ResourceFilterReducerState;
  searchTerm?: string;
  resource?: ResourceType;
};
export interface SubmitSearchResourceRequest {
  payload: SubmitSearchResourcePayload;
  type: SubmitSearchResource.REQUEST;
}

export enum UpdateSearchState {
  REQUEST = 'amundsen/search/UPDATE_SEARCH_STATE',
  RESET = 'amundsen/search/RESET_SEARCH_STATE',
}
export type UpdateSearchStatePayload = {
  filters?: FilterReducerState;
  resource?: ResourceType;
  updateUrl?: boolean;
  submitSearch?: boolean;
};
export interface UpdateSearchStateRequest {
  payload?: UpdateSearchStatePayload;
  type: UpdateSearchState.REQUEST;
}
export interface UpdateSearchStateReset {
  type: UpdateSearchState.RESET;
}

export enum LoadPreviousSearch {
  REQUEST = 'amundsen/search/LOAD_PREVIOUS_SEARCH_REQUEST',
}
export interface LoadPreviousSearchRequest {
  type: LoadPreviousSearch.REQUEST;
}

export enum UrlDidUpdate {
  REQUEST = 'amundsen/search/URL_DID_UPDATE_REQUEST',
}
export interface UrlDidUpdateRequest {
  payload: {
    urlSearch: UrlSearch;
  };
  type: UrlDidUpdate.REQUEST;
}
