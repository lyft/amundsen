import {
  GetLastIndexed,
  GetLastIndexedRequest,
  GetLastIndexedResponse,
} from './types';

export interface LastIndexedReducerState {
  lastIndexed: number | null;
}
export const initialState: LastIndexedReducerState = {
  lastIndexed: null,
};

/* ACTIONS */
export function getLastIndexed(): GetLastIndexedRequest {
  return { type: GetLastIndexed.REQUEST };
}

export function getLastIndexedFailure(): GetLastIndexedResponse {
  return { type: GetLastIndexed.FAILURE };
}

export function getLastIndexedSuccess(
  lastIndexedEpoch: number
): GetLastIndexedResponse {
  return {
    type: GetLastIndexed.SUCCESS,
    payload: {
      lastIndexedEpoch,
    },
  };
}

/* REDUCER */
export default function reducer(
  state: LastIndexedReducerState = initialState,
  action
): LastIndexedReducerState {
  switch (action.type) {
    case GetLastIndexed.REQUEST:
      return initialState;
    case GetLastIndexed.SUCCESS: {
      const { payload } = <GetLastIndexedResponse>action;
      if (payload === undefined) {
        throw Error('payload must be set for GetLastIndexed.SUCCESS');
      }
      return {
        lastIndexed: payload.lastIndexedEpoch || null,
      };
    }
    case GetLastIndexed.FAILURE:
      return {
        lastIndexed: null,
      };
    default:
      return state;
  }
}
