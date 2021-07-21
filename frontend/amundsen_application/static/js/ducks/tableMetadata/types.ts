import {
  DashboardResource,
  OwnerDict,
  PreviewData,
  TablePreviewQueryParams,
  TableMetadata,
  UpdateOwnerPayload,
  Tag,
} from 'interfaces';

export enum GetTableData {
  REQUEST = 'amundsen/tableMetadata/GET_TABLE_DATA_REQUEST',
  SUCCESS = 'amundsen/tableMetadata/GET_TABLE_DATA_SUCCESS',
  FAILURE = 'amundsen/tableMetadata/GET_TABLE_DATA_FAILURE',
}
export interface GetTableDataRequest {
  type: GetTableData.REQUEST;
  payload: {
    key: string;
    searchIndex?: string;
    source?: string;
  };
}
export interface GetTableDataResponse {
  type: GetTableData.SUCCESS | GetTableData.FAILURE;
  payload: {
    statusCode: number | null;
    data: TableMetadata;
    owners: OwnerDict;
    tags: Tag[];
  };
}

export enum GetTableDashboards {
  RESPONSE = 'amundsen/tableMetadata/GET_TABLE_DASHBOARDS_RESPONSE',
}
export interface GetTableDashboardsResponse {
  type: GetTableDashboards.RESPONSE;
  payload: {
    dashboards: DashboardResource[];
    errorMessage: string;
  };
}

export enum GetTableDescription {
  REQUEST = 'amundsen/tableMetadata/GET_TABLE_DESCRIPTION_REQUEST',
  SUCCESS = 'amundsen/tableMetadata/GET_TABLE_DESCRIPTION_SUCCESS',
  FAILURE = 'amundsen/tableMetadata/GET_TABLE_DESCRIPTION_FAILURE',
}
export interface GetTableDescriptionRequest {
  type: GetTableDescription.REQUEST;
  payload: {
    onSuccess?: () => any;
    onFailure?: () => any;
  };
}
export interface GetTableDescriptionResponse {
  type: GetTableDescription.SUCCESS | GetTableDescription.FAILURE;
  payload: {
    tableMetadata: TableMetadata;
  };
}

export enum UpdateTableDescription {
  REQUEST = 'amundsen/tableMetadata/UPDATE_TABLE_DESCRIPTION_REQUEST',
  SUCCESS = 'amundsen/tableMetadata/UPDATE_TABLE_DESCRIPTION_SUCCESS',
  FAILURE = 'amundsen/tableMetadata/UPDATE_TABLE_DESCRIPTION_FAILURE',
}
export interface UpdateTableDescriptionRequest {
  type: UpdateTableDescription.REQUEST;
  payload: {
    newValue: string;
    onSuccess?: () => any;
    onFailure?: () => any;
  };
}
export interface UpdateTableDescriptionResponse {
  type: UpdateTableDescription.SUCCESS | UpdateTableDescription.FAILURE;
}

export enum GetColumnDescription {
  REQUEST = 'amundsen/tableMetadata/GET_COLUMN_DESCRIPTION_REQUEST',
  SUCCESS = 'amundsen/tableMetadata/GET_COLUMN_DESCRIPTION_SUCCESS',
  FAILURE = 'amundsen/tableMetadata/GET_COLUMN_DESCRIPTION_FAILURE',
}
export interface GetColumnDescriptionRequest {
  type: GetColumnDescription.REQUEST;
  payload: {
    columnIndex: number;
    onSuccess?: () => any;
    onFailure?: () => any;
  };
}
export interface GetColumnDescriptionResponse {
  type: GetColumnDescription.SUCCESS | GetColumnDescription.FAILURE;
  payload: {
    tableMetadata: TableMetadata;
  };
}

export enum UpdateColumnDescription {
  REQUEST = 'amundsen/tableMetadata/UPDATE_COLUMN_DESCRIPTION_REQUEST',
  SUCCESS = 'amundsen/tableMetadata/UPDATE_COLUMN_DESCRIPTION_SUCCESS',
  FAILURE = 'amundsen/tableMetadata/UPDATE_COLUMN_DESCRIPTION_FAILURE',
}
export interface UpdateColumnDescriptionRequest {
  type: UpdateColumnDescription.REQUEST;
  payload: {
    newValue: string;
    columnIndex: number;
    onSuccess?: () => any;
    onFailure?: () => any;
  };
}
export interface UpdateColumnDescriptionResponse {
  type: UpdateColumnDescription.SUCCESS | UpdateColumnDescription.FAILURE;
}

export enum GetPreviewData {
  REQUEST = 'amundsen/preview/GET_PREVIEW_DATA_REQUEST',
  SUCCESS = 'amundsen/preview/GET_PREVIEW_DATA_SUCCESS',
  FAILURE = 'amundsen/preview/GET_PREVIEW_DATA_FAILURE',
}
export interface GetPreviewDataRequest {
  type: GetPreviewData.REQUEST;
  payload: {
    queryParams: TablePreviewQueryParams;
  };
}
export interface GetPreviewDataResponse {
  type: GetPreviewData.SUCCESS | GetPreviewData.FAILURE;
  payload: {
    data: PreviewData;
    status: number | null;
  };
}

export enum UpdateTableOwner {
  REQUEST = 'amundsen/tableMetadata/UPDATE_TABLE_OWNER_REQUEST',
  SUCCESS = 'amundsen/tableMetadata/UPDATE_TABLE_OWNER_SUCCESS',
  FAILURE = 'amundsen/tableMetadata/UPDATE_TABLE_OWNER_FAILURE',
}
export interface UpdateTableOwnerRequest {
  type: UpdateTableOwner.REQUEST;
  payload: {
    updateArray: UpdateOwnerPayload[];
    onSuccess?: () => any;
    onFailure?: () => any;
  };
}
export interface UpdateTableOwnerResponse {
  type: UpdateTableOwner.SUCCESS | UpdateTableOwner.FAILURE;
  payload: {
    owners: OwnerDict;
  };
}
