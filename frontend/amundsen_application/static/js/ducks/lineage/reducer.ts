import { ColumnLineageMap, Lineage } from 'interfaces/Lineage';
import {
  GetColumnLineage,
  GetColumnLineageRequest,
  GetColumnLineageResponse,
  GetTableLineage,
  GetTableLineageRequest,
  GetTableLineageResponse,
  GetTableColumnLineage,
  GetTableColumnLineageRequest,
  GetTableColumnLineageResponse,
} from './types';

export const initialLineageState = {
  upstream_entities: [],
  downstream_entities: [],
  depth: 0,
  direction: 'both',
  key: '',
};

export const initialState: LineageReducerState = {
  lineageTree: initialLineageState,
  statusCode: null,
  isLoading: false,
  // ToDo: Please remove once list based view is deprecated
  columnLineageMap: {},
};

/* ACTIONS */
export function getTableLineage(
  key: string,
  depth: number = 1,
  direction: string = 'both'
): GetTableLineageRequest {
  return {
    type: GetTableLineage.REQUEST,
    payload: { key, depth, direction },
  };
}

export function getTableLineageSuccess(
  data: Lineage,
  statusCode: number
): GetTableLineageResponse {
  return {
    type: GetTableLineage.SUCCESS,
    payload: {
      lineageTree: data,
      statusCode,
    },
  };
}

export function getTableLineageFailure(
  statusCode: number
): GetTableLineageResponse {
  return {
    type: GetTableLineage.FAILURE,
    payload: {
      lineageTree: initialLineageState,
      statusCode,
    },
  };
}

export function getColumnLineage(
  key: string,
  columnName: string,
  depth: number = 1,
  direction: string = 'both'
): GetColumnLineageRequest {
  return {
    type: GetColumnLineage.REQUEST,
    payload: { key, depth, direction, columnName },
    meta: {
      analytics: {
        name: `lineage/getColumnLineage`,
        payload: {
          category: 'lineage',
          label: `${key}/${columnName}`,
        },
      },
    },
  };
}

export function getColumnLineageSuccess(
  data: Lineage,
  statusCode: number
): GetColumnLineageResponse {
  return {
    type: GetColumnLineage.SUCCESS,
    payload: {
      lineageTree: data,
      statusCode,
    },
  };
}

export function getColumnLineageFailure(
  statusCode: number
): GetColumnLineageResponse {
  return {
    type: GetColumnLineage.FAILURE,
    payload: {
      lineageTree: initialLineageState,
      statusCode,
    },
  };
}

// ToDo: Please remove once list based view is deprecated
export function getTableColumnLineage(
  key: string,
  columnName: string
): GetTableColumnLineageRequest {
  return {
    type: GetTableColumnLineage.REQUEST,
    payload: { key, columnName },
    meta: {
      analytics: {
        name: `lineage/getTableColumnLineage`,
        payload: {
          category: 'lineage',
          label: `${key}/${columnName}`,
        },
      },
    },
  };
}

// ToDo: Please remove once list based view is deprecated
export function getTableColumnLineageSuccess(
  data: Lineage,
  columnName: string,
  statusCode: number
): GetTableColumnLineageResponse {
  return {
    type: GetTableColumnLineage.SUCCESS,
    payload: {
      columnName,
      statusCode,
      lineageTree: data,
    },
  };
}
// ToDo: Please remove once list based view is deprecated
export function getTableColumnLineageFailure(
  columnName: string,
  statusCode: number
): GetTableColumnLineageResponse {
  return {
    type: GetTableColumnLineage.FAILURE,
    payload: {
      columnName,
      lineageTree: initialLineageState,
      statusCode,
    },
  };
}

/* REDUCER */
export interface LineageReducerState {
  statusCode: number | null;
  lineageTree: Lineage;
  isLoading: boolean;
  // ToDo: Please remove once list based view is deprecated
  columnLineageMap: ColumnLineageMap;
}

export default function reducer(
  state: LineageReducerState = initialState,
  action
): LineageReducerState {
  switch (action.type) {
    case GetTableLineage.SUCCESS:
    case GetTableLineage.FAILURE:
      return {
        ...state,
        lineageTree: (<GetTableLineageResponse>action).payload.lineageTree,
        statusCode: (<GetTableLineageResponse>action).payload.statusCode,
        isLoading: false,
      };
    case GetColumnLineage.SUCCESS:
    case GetColumnLineage.FAILURE:
      return {
        ...state,
        lineageTree: (<GetColumnLineageResponse>action).payload.lineageTree,
        statusCode: (<GetColumnLineageResponse>action).payload.statusCode,
        isLoading: false,
      };
    case GetTableLineage.REQUEST: {
      return {
        ...state,
        isLoading: true,
        statusCode: null,
      };
    }
    case GetTableColumnLineage.REQUEST: {
      const { columnName } = (<GetTableColumnLineageRequest>action).payload;
      return {
        ...state,
        columnLineageMap: {
          ...state.columnLineageMap,
          [columnName]: {
            lineageTree: initialLineageState,
            isLoading: true,
          },
        },
      };
    }
    // ToDo: Please remove once list based view is deprecated
    case GetTableColumnLineage.SUCCESS:
    case GetTableColumnLineage.FAILURE: {
      const { columnName, lineageTree: columnLineage } = (<
        GetTableColumnLineageResponse
      >action).payload;
      return {
        ...state,
        columnLineageMap: {
          ...state.columnLineageMap,
          [columnName]: {
            lineageTree: columnLineage,
            isLoading: false,
          },
        },
      };
    }
    default:
      return state;
  }
}
