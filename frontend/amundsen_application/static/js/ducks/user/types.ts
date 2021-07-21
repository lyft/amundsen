import { LoggedInUser, PeopleUser, Resource, ResourceDict } from 'interfaces';

export enum GetLoggedInUser {
  REQUEST = 'amundsen/current_user/GET_REQUEST',
  SUCCESS = 'amundsen/current_user/GET_SUCCESS',
  FAILURE = 'amundsen/current_user/GET_FAILURE',
}
export interface GetLoggedInUserRequest {
  type: GetLoggedInUser.REQUEST;
}
export interface GetLoggedInUserResponse {
  type: GetLoggedInUser.SUCCESS | GetLoggedInUser.FAILURE;
  payload?: {
    user: LoggedInUser;
  };
}

export enum GetUser {
  REQUEST = 'amundsen/user/GET_REQUEST',
  SUCCESS = 'amundsen/user/GET_SUCCESS',
  FAILURE = 'amundsen/user/GET_FAILURE',
}
export interface GetUserRequest {
  type: GetUser.REQUEST;
  payload: {
    userId: string;
    source?: string;
    index?: string;
  };
}
export interface GetUserResponse {
  type: GetUser.SUCCESS | GetUser.FAILURE;
  payload?: {
    user: PeopleUser;
  };
}

export enum GetUserOwn {
  REQUEST = 'amundsen/user/own/GET_REQUEST',
  SUCCESS = 'amundsen/user/own/GET_SUCCESS',
  FAILURE = 'amundsen/user/own/GET_FAILURE',
}
export interface GetUserOwnRequest {
  type: GetUserOwn.REQUEST;
  payload: {
    userId: string;
  };
}
export interface GetUserOwnResponse {
  type: GetUserOwn.SUCCESS | GetUserOwn.FAILURE;
  payload?: {
    own: ResourceDict<Resource[]>;
  };
}

export enum GetUserRead {
  REQUEST = 'amundsen/user/read/GET_REQUEST',
  SUCCESS = 'amundsen/user/read/GET_SUCCESS',
  FAILURE = 'amundsen/user/read/GET_FAILURE',
}
export interface GetUserReadRequest {
  type: GetUserRead.REQUEST;
  payload: {
    userId: string;
  };
}
export interface GetUserReadResponse {
  type: GetUserRead.SUCCESS | GetUserRead.FAILURE;
  payload?: {
    read: Resource[];
  };
}
