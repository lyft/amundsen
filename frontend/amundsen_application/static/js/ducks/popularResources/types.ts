import { ResourceDict, PopularResource } from 'interfaces';

export enum GetPopularResources {
  REQUEST = 'amundsen/popularResources/GET_POPULAR_RESOURCES_REQUEST',
  SUCCESS = 'amundsen/popularResources/GET_POPULAR_RESOURCES_SUCCESS',
  FAILURE = 'amundsen/popularResources/GET_POPULAR_RESOURCES_FAILURE',
}
export interface GetPopularResourcesRequest {
  type: GetPopularResources.REQUEST;
}
export interface GetPopularResourcesResponse {
  type: GetPopularResources.SUCCESS | GetPopularResources.FAILURE;
  payload: {
    popularResources: ResourceDict<PopularResource[]>;
  };
}
