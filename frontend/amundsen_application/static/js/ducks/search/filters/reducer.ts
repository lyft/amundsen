import {
  SubmitSearchResource,
  SubmitSearchResourceRequest,
} from 'ducks/search/types';
import { ResourceType } from 'interfaces';

/* ACTION TYPES */
export enum UpdateSearchFilter {
  REQUEST = 'amundsen/search/filter/UPDATE_SEARCH_FILTER_REQUEST',
}
export type UpdateFilterPayload = {
  categoryId: string;
  value: string | FilterOptions | undefined;
};
export interface UpdateFilterRequest {
  payload: UpdateFilterPayload;
  type: UpdateSearchFilter.REQUEST;
}

/* ACTIONS */
export function updateFilterByCategory({
  categoryId,
  value,
}: UpdateFilterPayload): UpdateFilterRequest {
  return {
    payload: {
      categoryId,
      value,
    },
    type: UpdateSearchFilter.REQUEST,
  };
}

/* REDUCER TYPES */
export type FilterOptions = { [id: string]: boolean };

export interface FilterReducerState {
  [ResourceType.dashboard]?: ResourceFilterReducerState;
  [ResourceType.table]?: ResourceFilterReducerState;
  [ResourceType.feature]?: ResourceFilterReducerState;
}

export interface ResourceFilterReducerState {
  [categoryId: string]: string | FilterOptions;
}

/* REDUCER */
export const initialTableFilterState = {};
export const initialDashboardFilterState = {};
export const initialFeatureFilterState = {};

export const initialFilterState: FilterReducerState = {
  [ResourceType.dashboard]: initialDashboardFilterState,
  [ResourceType.table]: initialTableFilterState,
  [ResourceType.feature]: initialFeatureFilterState,
};

export default function reducer(
  state: FilterReducerState = initialFilterState,
  action
): FilterReducerState {
  switch (action.type) {
    case SubmitSearchResource.REQUEST:
      const { payload } = <SubmitSearchResourceRequest>action;
      if (payload.resource && payload.resourceFilters) {
        return {
          ...state,
          [payload.resource]: payload.resourceFilters,
        };
      }
      return state;
    default:
      return state;
  }
}
