// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import {
  GetFeature,
  GetFeatureRequest,
  GetFeatureResponse,
  GetFeaturePayload,
  GetFeatureCodeRequest,
  GetFeatureCodePayload,
  GetFeatureCode,
  GetFeatureCodeResponse,
  GetFeatureDescriptionRequest,
  GetFeatureDescription,
  GetFeatureDescriptionPayload,
  GetFeatureDescriptionResponse,
  UpdateFeatureDescriptionRequest,
  UpdateFeatureDescriptionPayload,
  UpdateFeatureDescriptionResponse,
  UpdateFeatureDescription,
  UpdateFeatureOwnerRequest,
  UpdateFeatureOwnerResponse,
  UpdateFeatureOwner,
  GetFeaturePreviewDataRequest,
  GetFeaturePreviewData,
  GetFeaturePreviewDataResponse,
  GetFeaturePreviewPayload,
} from 'ducks/feature/types';
import {
  GetFeatureLineage,
  GetFeatureLineageRequest,
  GetFeatureLineageResponse,
  GetFeatureLineagePayload,
} from 'ducks/lineage/types';
import {
  FeatureCode,
  FeatureMetadata,
  FeaturePreviewQueryParams,
} from 'interfaces/Feature';
import { Lineage } from 'interfaces/Lineage';
import { UpdateOwnerPayload } from 'interfaces/TableMetadata';
import { User } from 'interfaces/User';
import { PreviewData } from 'interfaces/PreviewData';

/* Actions */

export function getFeature(
  key: string,
  index?: string,
  source?: string
): GetFeatureRequest {
  return {
    payload: {
      key,
      index,
      source,
    },
    type: GetFeature.REQUEST,
  };
}

export function getFeatureSuccess(
  payload: GetFeaturePayload
): GetFeatureResponse {
  return {
    payload,
    type: GetFeature.SUCCESS,
  };
}

export function getFeatureFailure(
  payload: GetFeaturePayload
): GetFeatureResponse {
  return {
    payload,
    type: GetFeature.FAILURE,
  };
}

export function getFeatureLineage(key: string): GetFeatureLineageRequest {
  return {
    payload: {
      key,
      depth: 1,
      direction: 'upstream',
    },
    type: GetFeatureLineage.REQUEST,
  };
}
export function getFeatureLineageSuccess(
  payload: GetFeatureLineagePayload
): GetFeatureLineageResponse {
  return {
    payload,
    type: GetFeatureLineage.SUCCESS,
  };
}
export function getFeatureLineageFailure(
  payload: GetFeatureLineagePayload
): GetFeatureLineageResponse {
  return {
    payload,
    type: GetFeatureLineage.FAILURE,
  };
}

export function getFeatureCode(key: string): GetFeatureCodeRequest {
  return {
    payload: {
      key,
    },
    type: GetFeatureCode.REQUEST,
  };
}
export function getFeatureCodeSuccess(
  payload: GetFeatureCodePayload
): GetFeatureCodeResponse {
  return {
    payload,
    type: GetFeatureCode.SUCCESS,
  };
}
export function getFeatureCodeFailure(
  payload: GetFeatureCodePayload
): GetFeatureCodeResponse {
  return {
    payload,
    type: GetFeatureCode.FAILURE,
  };
}

export function getFeaturePreviewData(
  payload: FeaturePreviewQueryParams
): GetFeaturePreviewDataRequest {
  return {
    payload,
    type: GetFeaturePreviewData.REQUEST,
  };
}
export function getFeaturePreviewDataSuccess(
  payload: GetFeaturePreviewPayload
): GetFeaturePreviewDataResponse {
  return {
    payload,
    type: GetFeaturePreviewData.SUCCESS,
  };
}
export function getFeaturePreviewDataFailure(
  payload: GetFeaturePreviewPayload
): GetFeaturePreviewDataResponse {
  return {
    payload,
    type: GetFeaturePreviewData.FAILURE,
  };
}

export function getFeatureDescription(
  onSuccess?: () => any,
  onFailure?: () => any
): GetFeatureDescriptionRequest {
  return {
    payload: {
      onSuccess,
      onFailure,
    },
    type: GetFeatureDescription.REQUEST,
  };
}

export function getFeatureDescriptionSuccess(
  payload: GetFeatureDescriptionPayload
) {
  return {
    payload,
    type: GetFeatureDescription.SUCCESS,
  };
}

export function getFeatureDescriptionFailure(
  payload: GetFeatureDescriptionPayload
): GetFeatureDescriptionResponse {
  return {
    payload,
    type: GetFeatureDescription.FAILURE,
  };
}

export function updateFeatureDescription(
  newValue: string,
  onSuccess?: () => any,
  onFailure?: () => any
): UpdateFeatureDescriptionRequest {
  return {
    payload: {
      newValue,
      onSuccess,
      onFailure,
    },
    type: UpdateFeatureDescription.REQUEST,
  };
}

export function updateFeatureDescriptionSuccess(
  payload: UpdateFeatureDescriptionPayload
) {
  return {
    payload,
    type: UpdateFeatureDescription.SUCCESS,
  };
}

export function updateFeatureDescriptionFailure(
  payload: UpdateFeatureDescriptionPayload
): UpdateFeatureDescriptionResponse {
  return {
    payload,
    type: UpdateFeatureDescription.FAILURE,
  };
}

export function updateFeatureOwner(
  updateArray: UpdateOwnerPayload[],
  onSuccess?: () => any,
  onFailure?: () => any
): UpdateFeatureOwnerRequest {
  return {
    payload: {
      onSuccess,
      onFailure,
      updateArray,
    },
    type: UpdateFeatureOwner.REQUEST,
  };
}
export function updateFeatureOwnerFailure(
  owners: User[]
): UpdateFeatureOwnerResponse {
  return {
    type: UpdateFeatureOwner.FAILURE,
    payload: {
      owners,
    },
  };
}
export function updateFeatureOwnerSuccess(
  owners: User[]
): UpdateFeatureOwnerResponse {
  return {
    type: UpdateFeatureOwner.SUCCESS,
    payload: {
      owners,
    },
  };
}

/* Reducer */
export interface FeatureCodeState {
  featureCode: FeatureCode;
  isLoading: boolean;
  statusCode: number | null;
}

export interface FeatureLineageState {
  featureLineage: Lineage;
  isLoading: boolean;
  statusCode: number | null;
}

export interface FeaturePreviewDataState {
  previewData: PreviewData;
  isLoading: boolean;
  status: number | null;
}

export interface FeatureReducerState {
  isLoading: boolean;
  isLoadingOwners: boolean;
  statusCode: number | null;
  feature: FeatureMetadata;
  featureCode: FeatureCodeState;
  featureLineage: FeatureLineageState;
  preview: FeaturePreviewDataState;
}

export const initialFeatureState: FeatureMetadata = {
  key: '',
  name: '',
  version: '',
  status: '',
  feature_group: '',
  entity: '',
  data_type: '',
  availability: [],
  description: '',
  owners: [],
  badges: [],
  owner_tags: [],
  tags: [],
  programmatic_descriptions: [],
  watermarks: [],
  stats: [],
  last_updated_timestamp: 0,
  created_timestamp: 0,
};

export const emptyFeatureCode: FeatureCode = {
  text: '',
  source: '',
  key: '',
};

export const initialPreviewState = {
  previewData: {},
  isLoading: false,
  status: null,
};

export const initialFeatureCodeState: FeatureCodeState = {
  featureCode: emptyFeatureCode,
  isLoading: false,
  statusCode: null,
};

export const emptyFeatureLineage: Lineage = {
  upstream_entities: [],
  downstream_entities: [],
  depth: 1,
  direction: 'upstream',
  key: '',
};

export const initialFeatureLineageState: FeatureLineageState = {
  featureLineage: emptyFeatureLineage,
  isLoading: false,
  statusCode: null,
};

export const initialState: FeatureReducerState = {
  isLoading: false,
  isLoadingOwners: false,
  statusCode: null,
  feature: initialFeatureState,
  featureCode: initialFeatureCodeState,
  featureLineage: initialFeatureLineageState,
  preview: initialPreviewState,
};

export default function reducer(
  state: FeatureReducerState = initialState,
  action
): FeatureReducerState {
  switch (action.type) {
    case GetFeature.REQUEST:
      return {
        ...state,
        statusCode: null,
        isLoading: true,
      };
    case GetFeature.FAILURE:
      return {
        ...state,
        isLoading: false,
        statusCode: action.payload.statusCode,
        feature: initialFeatureState,
      };
    case GetFeature.SUCCESS:
      return {
        ...state,
        isLoading: false,
        statusCode: action.payload.statusCode,
        feature: action.payload.feature,
      };
    case GetFeatureCode.REQUEST:
      return {
        ...state,
        featureCode: {
          featureCode: emptyFeatureCode,
          isLoading: true,
          statusCode: null,
        },
      };
    case GetFeatureCode.FAILURE:
      return {
        ...state,
        featureCode: {
          featureCode: emptyFeatureCode,
          isLoading: false,
          statusCode: action.payload.statusCode,
        },
      };
    case GetFeatureCode.SUCCESS:
      return {
        ...state,
        featureCode: {
          featureCode: action.payload.featureCode,
          statusCode: action.payload.statusCode,
          isLoading: false,
        },
      };
    case GetFeatureLineage.REQUEST:
      return {
        ...state,
        featureLineage: {
          featureLineage: emptyFeatureLineage,
          isLoading: true,
          statusCode: null,
        },
      };
    case GetFeatureLineage.FAILURE:
      return {
        ...state,
        featureLineage: {
          featureLineage: emptyFeatureLineage,
          isLoading: false,
          statusCode: action.payload.statusCode,
        },
      };
    case GetFeatureLineage.SUCCESS:
      return {
        ...state,
        featureLineage: {
          featureLineage: action.payload.data,
          isLoading: false,
          statusCode: action.payload.statusCode,
        },
      };
    case GetFeaturePreviewData.REQUEST:
      return {
        ...state,
        preview: {
          isLoading: true,
          previewData: {},
          status: null,
        },
      };
    case GetFeaturePreviewData.SUCCESS:
    case GetFeaturePreviewData.FAILURE:
      return {
        ...state,
        preview: {
          isLoading: false,
          previewData: action.payload.previewData,
          status: action.payload.status,
        },
      };
    case GetFeatureDescription.FAILURE:
    case GetFeatureDescription.SUCCESS:
      return {
        ...state,
        feature: {
          ...state.feature,
          description: action.payload.description,
        },
      };
    case UpdateFeatureDescription.FAILURE:
    case UpdateFeatureDescription.SUCCESS:
      return {
        ...state,
        feature: {
          ...state.feature,
          description: action.payload.description,
        },
      };
    case UpdateFeatureOwner.REQUEST:
      return { ...state, isLoadingOwners: true };
    case UpdateFeatureOwner.FAILURE:
    case UpdateFeatureOwner.SUCCESS:
      return {
        ...state,
        isLoadingOwners: false,
        feature: {
          ...state.feature,
          owners: (<UpdateFeatureOwnerResponse>action).payload.owners,
        },
      };
    default:
      return state;
  }
}
