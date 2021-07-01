import { Lineage, AnalyticsEvent } from 'interfaces';

export enum GetFeatureLineage {
  REQUEST = 'amundsen/lineage/GET_FEATURE_LINEAGE_REQUEST',
  SUCCESS = 'amundsen/lineage/GET_FEATURE_LINEAGE_SUCCESS',
  FAILURE = 'amundsen/lineage/GET_FEATURE_LINEAGE_FAILURE',
}

export interface GetFeatureLineagePayload {
  lineageTree: Lineage;
  statusCode: number;
}

export interface GetFeatureLineageRequest {
  type: GetFeatureLineage.REQUEST;
  payload: {
    key: string;
    direction: string;
    depth: number;
  };
}
export interface GetFeatureLineageResponse {
  type: GetFeatureLineage.SUCCESS | GetFeatureLineage.FAILURE;
  payload: {
    lineageTree: Lineage;
    statusCode: number;
  };
}

export enum GetTableLineage {
  REQUEST = 'amundsen/lineage/GET_TABLE_LINEAGE_REQUEST',
  SUCCESS = 'amundsen/lineage/GET_TABLE_LINEAGE_SUCCESS',
  FAILURE = 'amundsen/lineage/GET_TABLE_LINEAGE_FAILURE',
}
export interface GetTableLineageRequest {
  type: GetTableLineage.REQUEST;
  payload: {
    key: string;
    direction: string;
    depth: number;
  };
}
export interface GetTableLineageResponse {
  type: GetTableLineage.SUCCESS | GetTableLineage.FAILURE;
  payload: {
    lineageTree: Lineage;
    statusCode: number;
  };
}

export enum GetColumnLineage {
  REQUEST = 'amundsen/lineage/GET_COLUMN_LINEAGE_REQUEST',
  SUCCESS = 'amundsen/lineage/GET_COLUMN_LINEAGE_SUCCESS',
  FAILURE = 'amundsen/lineage/GET_COLUMN_LINEAGE_FAILURE',
}
export interface GetColumnLineageRequest {
  type: GetColumnLineage.REQUEST;
  payload: {
    key: string;
    columnName: string;
    direction: string;
    depth: number;
  };
  meta: {
    analytics: AnalyticsEvent;
  };
}
export interface GetColumnLineageResponse {
  type: GetColumnLineage.SUCCESS | GetColumnLineage.FAILURE;
  payload: {
    lineageTree: Lineage;
    statusCode: number;
  };
}

// To keep the backward compatibility for the list based lineage on table detail page
// ToDo: Please remove once list based view is deprecated
export enum GetTableColumnLineage {
  REQUEST = 'amundsen/tableMetadata/GET_COLUMN_LINEAGE_REQUEST',
  SUCCESS = 'amundsen/tableMetadata/GET_COLUMN_LINEAGE_SUCCESS',
  FAILURE = 'amundsen/tableMetadata/GET_COLUMN_LINEAGE_FAILURE',
}
export interface GetTableColumnLineageRequest {
  type: GetTableColumnLineage.REQUEST;
  payload: {
    key: string;
    columnName: string;
  };
  meta: {
    analytics: AnalyticsEvent;
  };
}
export interface GetTableColumnLineageResponse {
  type: GetTableColumnLineage.SUCCESS | GetTableColumnLineage.FAILURE;
  payload: {
    lineageTree: Lineage;
    columnName: string;
    statusCode: number;
  };
}
