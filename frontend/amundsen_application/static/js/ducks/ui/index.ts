// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

export const pageViewActionType = 'analytics/pageView';

// Actions
export function pageViewed(path: string) {
  return {
    type: pageViewActionType,
    meta: {
      analytics: {
        name: pageViewActionType,
        payload: {
          category: 'pageView',
          label: `${path}`,
        },
      },
    },
  };
}

// Reducer
export interface UIReducerState {}

export const initialState: UIReducerState = {};

export default function reducer(
  state: UIReducerState = initialState,
  action
): UIReducerState {
  switch (action.type) {
    case pageViewActionType: {
      return state;
    }
    default:
      return state;
  }
}
