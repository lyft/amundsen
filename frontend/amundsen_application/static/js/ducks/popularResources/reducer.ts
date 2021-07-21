import { PopularResource, ResourceDict, ResourceType } from 'interfaces';

import {
  GetPopularResources,
  GetPopularResourcesRequest,
  GetPopularResourcesResponse,
} from './types';

export const initialPopularResourcesState = {
  [ResourceType.table]: [],
  [ResourceType.dashboard]: [],
};

/* ACTIONS */
export function getPopularResources(): GetPopularResourcesRequest {
  return { type: GetPopularResources.REQUEST };
}
export function getPopularResourcesFailure(): GetPopularResourcesResponse {
  return {
    type: GetPopularResources.FAILURE,
    payload: {
      popularResources: {
        ...initialPopularResourcesState,
      },
    },
  };
}
export function getPopularResourcesSuccess(
  popularResources: ResourceDict<PopularResource[]>
): GetPopularResourcesResponse {
  return { type: GetPopularResources.SUCCESS, payload: { popularResources } };
}

/* REDUCER */
export interface PopularResourcesReducerState {
  popularResources: ResourceDict<PopularResource[]>;
  popularResourcesIsLoaded: boolean;
}

const initialState: PopularResourcesReducerState = {
  popularResources: {
    ...initialPopularResourcesState,
  },
  popularResourcesIsLoaded: false,
};

export default function reducer(
  state: PopularResourcesReducerState = initialState,
  action
): PopularResourcesReducerState {
  switch (action.type) {
    case GetPopularResources.REQUEST:
      return {
        ...state,
        ...initialState,
      };
    case GetPopularResources.SUCCESS:
    case GetPopularResources.FAILURE:
      return {
        ...state,
        popularResources: (<GetPopularResourcesResponse>action).payload
          .popularResources,
        popularResourcesIsLoaded: true,
      };
    default:
      return state;
  }
}
