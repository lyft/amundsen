import { UpdateTagData, Tag, ResourceType } from 'interfaces';

import { GetDashboard, GetDashboardResponse } from 'ducks/dashboard/types';
import { GetFeature, GetFeatureResponse } from 'ducks/feature/types';
import { GetTableData, GetTableDataResponse } from 'ducks/tableMetadata/types';

import {
  GetAllTags,
  GetAllTagsRequest,
  GetAllTagsResponse,
  UpdateTags,
  UpdateTagsRequest,
  UpdateTagsResponse,
} from './types';

/* ACTIONS */
export function getAllTags(): GetAllTagsRequest {
  return { type: GetAllTags.REQUEST };
}
export function getAllTagsFailure(): GetAllTagsResponse {
  return { type: GetAllTags.FAILURE, payload: { allTags: [] } };
}
export function getAllTagsSuccess(allTags: Tag[]): GetAllTagsResponse {
  return { type: GetAllTags.SUCCESS, payload: { allTags } };
}

export function updateTags(
  tagArray: UpdateTagData[],
  resourceType: ResourceType,
  uriKey: string
): UpdateTagsRequest {
  return {
    payload: {
      tagArray,
      resourceType,
      uriKey,
    },
    type: UpdateTags.REQUEST,
  };
}
export function updateTagsFailure(): UpdateTagsResponse {
  return {
    type: UpdateTags.FAILURE,
    payload: {
      tags: [],
    },
  };
}
export function updateTagsSuccess(tags: Tag[]): UpdateTagsResponse {
  return {
    type: UpdateTags.SUCCESS,
    payload: {
      tags,
    },
  };
}

/* REDUCER */
export interface TagsReducerState {
  allTags: TagState;
  resourceTags: TagState;
}

interface TagState {
  isLoading: boolean;
  tags: Tag[];
}

export const initialState: TagsReducerState = {
  allTags: {
    isLoading: false,
    tags: [],
  },
  resourceTags: {
    isLoading: false,
    tags: [],
  },
};

export default function reducer(
  state: TagsReducerState = initialState,
  action
): TagsReducerState {
  switch (action.type) {
    case GetAllTags.REQUEST:
      return {
        ...state,
        allTags: {
          ...state.allTags,
          isLoading: true,
          tags: [],
        },
      };
    case GetAllTags.FAILURE:
      return initialState;
    case GetAllTags.SUCCESS:
      return {
        ...state,
        allTags: {
          ...state.allTags,
          isLoading: false,
          tags: (<GetAllTagsResponse>action).payload.allTags,
        },
      };

    case GetTableData.REQUEST:
    case GetDashboard.REQUEST:
    case GetFeature.REQUEST:
      return {
        ...state,
        resourceTags: {
          ...state.resourceTags,
          isLoading: true,
          tags: [],
        },
      };
    case GetTableData.SUCCESS:
      return {
        ...state,
        resourceTags: {
          ...state.resourceTags,
          isLoading: false,
          tags: (<GetTableDataResponse>action).payload.tags,
        },
      };
    case GetDashboard.SUCCESS:
      return {
        ...state,
        resourceTags: {
          ...state.resourceTags,
          isLoading: false,
          tags: (<GetDashboardResponse>action).payload.dashboard?.tags || [],
        },
      };
    case GetFeature.SUCCESS:
      return {
        ...state,
        resourceTags: {
          ...state.resourceTags,
          isLoading: false,
          tags: (<GetFeatureResponse>action).payload.feature?.tags || [],
        },
      };
    case GetTableData.FAILURE:
    case GetDashboard.FAILURE:
    case GetFeature.FAILURE:
      return {
        ...state,
        resourceTags: {
          ...state.resourceTags,
          isLoading: false,
          tags: [],
        },
      };

    case UpdateTags.REQUEST:
      return {
        ...state,
        resourceTags: {
          ...state.resourceTags,
          isLoading: true,
        },
      };
    case UpdateTags.FAILURE:
      return {
        ...state,
        resourceTags: {
          ...state.resourceTags,
          isLoading: false,
        },
      };
    case UpdateTags.SUCCESS:
      return {
        ...state,
        resourceTags: {
          ...state.resourceTags,
          isLoading: false,
          tags: (<UpdateTagsResponse>action).payload.tags,
        },
      };
    default:
      return state;
  }
}
