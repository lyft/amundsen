export enum GetLastIndexed {
  REQUEST = 'amundsen/GET_LAST_UPDATED_REQUEST',
  SUCCESS = 'amundsen/GET_LAST_UPDATED_SUCCESS',
  FAILURE = 'amundsen/GET_LAST_UPDATED_FAILURE',
}
export interface GetLastIndexedRequest {
  type: GetLastIndexed.REQUEST;
}
export interface GetLastIndexedResponse {
  type: GetLastIndexed.SUCCESS | GetLastIndexed.FAILURE;
  payload?: GetLastIndexedPayload;
}

export interface GetLastIndexedPayload {
  lastIndexedEpoch?: number;
}
