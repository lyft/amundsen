import {
  DashboardResource,
  OwnerDict,
  PreviewData,
  TablePreviewQueryParams,
  TableMetadata,
  Tag,
} from 'interfaces';

import {
  GetTableData,
  GetTableDataRequest,
  GetTableDataResponse,
  GetTableDashboards,
  GetTableDashboardsResponse,
  GetTableDescription,
  GetTableDescriptionRequest,
  GetTableDescriptionResponse,
  UpdateTableDescription,
  UpdateTableDescriptionRequest,
  GetColumnDescription,
  GetColumnDescriptionResponse,
  GetColumnDescriptionRequest,
  UpdateColumnDescription,
  UpdateColumnDescriptionRequest,
  GetPreviewData,
  GetPreviewDataRequest,
  GetPreviewDataResponse,
  UpdateTableOwner,
} from './types';

import tableOwnersReducer, {
  initialOwnersState,
  TableOwnerReducerState,
} from './owners/reducer';

export const initialPreviewState = {
  data: {},
  status: null,
};

export const initialTableDataState: TableMetadata = {
  badges: [],
  cluster: '',
  columns: [],
  database: '',
  is_editable: false,
  is_view: false,
  key: '',
  last_updated_timestamp: 0,
  schema: '',
  name: '',
  description: '',
  table_writer: { application_url: '', description: '', id: '', name: '' },
  partition: { is_partitioned: false },
  table_readers: [],
  source: { source: '', source_type: '' },
  resource_reports: [],
  watermarks: [],
  programmatic_descriptions: {},
};

export const initialState: TableMetadataReducerState = {
  isLoading: true,
  preview: initialPreviewState,
  statusCode: null,
  tableData: initialTableDataState,
  tableOwners: initialOwnersState,
  // tableLineage: initialTableLineageState,
  // columnLineageMap: {},
};

/* ACTIONS */
export function getTableData(
  key: string,
  searchIndex?: string,
  source?: string
): GetTableDataRequest {
  return {
    payload: {
      key,
      searchIndex,
      source,
    },
    type: GetTableData.REQUEST,
  };
}

export function getTableDataFailure(): GetTableDataResponse {
  return {
    type: GetTableData.FAILURE,
    payload: {
      data: initialTableDataState,
      owners: {},
      statusCode: 500,
      tags: [],
    },
  };
}

export function getTableDataSuccess(
  data: TableMetadata,
  owners: OwnerDict,
  statusCode: number,
  tags: Tag[]
): GetTableDataResponse {
  return {
    type: GetTableData.SUCCESS,
    payload: {
      data,
      owners,
      statusCode,
      tags,
    },
  };
}

export function getTableDashboardsResponse(
  dashboards: DashboardResource[],
  errorMessage: string = ''
): GetTableDashboardsResponse {
  return {
    type: GetTableDashboards.RESPONSE,
    payload: {
      dashboards,
      errorMessage,
    },
  };
}

export function getTableDescription(
  onSuccess?: () => any,
  onFailure?: () => any
): GetTableDescriptionRequest {
  return {
    payload: {
      onSuccess,
      onFailure,
    },
    type: GetTableDescription.REQUEST,
  };
}
export function getTableDescriptionFailure(
  tableMetadata: TableMetadata
): GetTableDescriptionResponse {
  return {
    type: GetTableDescription.FAILURE,
    payload: {
      tableMetadata,
    },
  };
}
export function getTableDescriptionSuccess(
  tableMetadata: TableMetadata
): GetTableDescriptionResponse {
  return {
    type: GetTableDescription.SUCCESS,
    payload: {
      tableMetadata,
    },
  };
}

export function updateTableDescription(
  newValue: string,
  onSuccess?: () => any,
  onFailure?: () => any
): UpdateTableDescriptionRequest {
  return {
    payload: {
      newValue,
      onSuccess,
      onFailure,
    },
    type: UpdateTableDescription.REQUEST,
  };
}

export function getColumnDescription(
  columnIndex: number,
  onSuccess?: () => any,
  onFailure?: () => any
): GetColumnDescriptionRequest {
  return {
    payload: {
      onSuccess,
      onFailure,
      columnIndex,
    },
    type: GetColumnDescription.REQUEST,
  };
}
export function getColumnDescriptionFailure(
  tableMetadata: TableMetadata
): GetColumnDescriptionResponse {
  return {
    type: GetColumnDescription.FAILURE,
    payload: {
      tableMetadata,
    },
  };
}
export function getColumnDescriptionSuccess(
  tableMetadata: TableMetadata
): GetColumnDescriptionResponse {
  return {
    type: GetColumnDescription.SUCCESS,
    payload: {
      tableMetadata,
    },
  };
}

export function updateColumnDescription(
  newValue: string,
  columnIndex: number,
  onSuccess?: () => any,
  onFailure?: () => any
): UpdateColumnDescriptionRequest {
  return {
    payload: {
      newValue,
      columnIndex,
      onSuccess,
      onFailure,
    },
    type: UpdateColumnDescription.REQUEST,
  };
}

export function getPreviewData(
  queryParams: TablePreviewQueryParams
): GetPreviewDataRequest {
  return { payload: { queryParams }, type: GetPreviewData.REQUEST };
}
export function getPreviewDataFailure(
  data: PreviewData,
  status: number
): GetPreviewDataResponse {
  return {
    type: GetPreviewData.FAILURE,
    payload: {
      data,
      status,
    },
  };
}
export function getPreviewDataSuccess(
  data: PreviewData,
  status: number
): GetPreviewDataResponse {
  return {
    type: GetPreviewData.SUCCESS,
    payload: {
      data,
      status,
    },
  };
}

/* REDUCER */
export interface TableMetadataReducerState {
  dashboards?: {
    isLoading: boolean;
    dashboards: DashboardResource[];
    errorMessage?: string;
  };
  isLoading: boolean;
  preview: {
    data: PreviewData;
    status: number | null;
  };
  statusCode: number | null;
  tableData: TableMetadata;
  tableOwners: TableOwnerReducerState;
}

export default function reducer(
  state: TableMetadataReducerState = initialState,
  action
): TableMetadataReducerState {
  switch (action.type) {
    case GetTableDashboards.RESPONSE:
      return {
        ...state,
        dashboards: {
          isLoading: false,
          dashboards: action.payload.dashboards,
          errorMessage: action.payload.errorMessage,
        },
      };
    case GetTableData.REQUEST:
      return initialState;
    case GetTableData.FAILURE:
      return {
        ...state,
        isLoading: false,
        preview: initialPreviewState,
        statusCode: (<GetTableDataResponse>action).payload.statusCode,
        tableData: initialTableDataState,
        tableOwners: tableOwnersReducer(state.tableOwners, action),
      };
    case GetTableData.SUCCESS:
      return {
        ...state,
        isLoading: false,
        statusCode: (<GetTableDataResponse>action).payload.statusCode,
        tableData: (<GetTableDataResponse>action).payload.data,
        tableOwners: tableOwnersReducer(state.tableOwners, action),
      };
    case GetTableDescription.FAILURE:
    case GetTableDescription.SUCCESS:
      return {
        ...state,
        tableData: (<GetTableDescriptionResponse>action).payload.tableMetadata,
      };
    case GetColumnDescription.FAILURE:
    case GetColumnDescription.SUCCESS:
      return {
        ...state,
        tableData: (<GetColumnDescriptionResponse>action).payload.tableMetadata,
      };
    case GetPreviewData.FAILURE:
    case GetPreviewData.SUCCESS:
      return { ...state, preview: (<GetPreviewDataResponse>action).payload };
    case UpdateTableOwner.REQUEST:
    case UpdateTableOwner.FAILURE:
    case UpdateTableOwner.SUCCESS:
      return {
        ...state,
        tableOwners: tableOwnersReducer(state.tableOwners, action),
      };
    default:
      return state;
  }
}
