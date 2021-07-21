import { ResourceType, Tag, UpdateTagData } from 'interfaces';

export enum GetAllTags {
  REQUEST = 'amundsen/allTags/GET_REQUEST',
  SUCCESS = 'amundsen/allTags/GET_SUCCESS',
  FAILURE = 'amundsen/allTags/GET_FAILURE',
}
export interface GetAllTagsRequest {
  type: GetAllTags.REQUEST;
}
export interface GetAllTagsResponse {
  type: GetAllTags.SUCCESS | GetAllTags.FAILURE;
  payload: {
    allTags: Tag[];
  };
}

export enum UpdateTags {
  REQUEST = 'amundsen/tags/UPDATE_TAGS_REQUEST',
  SUCCESS = 'amundsen/tags/UPDATE_TAGS_SUCCESS',
  FAILURE = 'amundsen/tags/UPDATE_TAGS_FAILURE',
}
export interface UpdateTagsRequest {
  type: UpdateTags.REQUEST;
  payload: {
    tagArray: UpdateTagData[];
    resourceType: ResourceType;
    uriKey: string;
  };
}
export interface UpdateTagsResponse {
  type: UpdateTags.SUCCESS | UpdateTags.FAILURE;
  payload: {
    tags: Tag[];
  };
}
