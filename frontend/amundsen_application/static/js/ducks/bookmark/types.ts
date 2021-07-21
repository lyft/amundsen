import {
  AnalyticsEvent,
  Bookmark,
  ResourceType,
  ResourceDict,
} from 'interfaces';

export enum AddBookmark {
  REQUEST = 'amundsen/bookmark/ADD_REQUEST',
  SUCCESS = 'amundsen/bookmark/ADD_SUCCESS',
  FAILURE = 'amundsen/bookmark/ADD_FAILURE',
}
export interface AddBookmarkRequest {
  type: AddBookmark.REQUEST;
  payload: {
    resourceKey: string;
    resourceType: ResourceType;
  };
  meta: {
    analytics: AnalyticsEvent;
  };
}
export interface AddBookmarkResponse {
  type: AddBookmark.SUCCESS | AddBookmark.FAILURE;
  payload?: {
    bookmarks: ResourceDict<Bookmark[]>;
  };
}

export enum RemoveBookmark {
  REQUEST = 'amundsen/bookmark/REMOVE_REQUEST',
  SUCCESS = 'amundsen/bookmark/REMOVE_SUCCESS',
  FAILURE = 'amundsen/bookmark/REMOVE_FAILURE',
}
export interface RemoveBookmarkRequest {
  type: RemoveBookmark.REQUEST;
  payload: {
    resourceKey: string;
    resourceType: ResourceType;
  };
  meta: {
    analytics: AnalyticsEvent;
  };
}
export interface RemoveBookmarkResponse {
  type: RemoveBookmark.SUCCESS | RemoveBookmark.FAILURE;
  payload?: {
    resourceKey: string;
    resourceType: ResourceType;
  };
}

// GetBookmarks - Get all bookmarks for the logged in user. This result will be cached
export enum GetBookmarks {
  REQUEST = 'amundsen/bookmark/GET_REQUEST',
  SUCCESS = 'amundsen/bookmark/GET_SUCCESS',
  FAILURE = 'amundsen/bookmark/GET_FAILURE',
}
export interface GetBookmarksRequest {
  type: GetBookmarks.REQUEST;
}
export interface GetBookmarksResponse {
  type: GetBookmarks.SUCCESS | GetBookmarks.FAILURE;
  payload?: {
    bookmarks: ResourceDict<Bookmark[]>;
  };
}

// GetBookmarksForUser - Get all bookmarks for a specified user
export enum GetBookmarksForUser {
  REQUEST = 'amundsen/bookmark/GET_FOR_USER_REQUEST',
  SUCCESS = 'amundsen/bookmark/GET_FOR_USER_SUCCESS',
  FAILURE = 'amundsen/bookmark/GET_FOR_USER_FAILURE',
}
export interface GetBookmarksForUserRequest {
  type: GetBookmarksForUser.REQUEST;
  payload: {
    userId: string;
  };
}
export interface GetBookmarksForUserResponse {
  type: GetBookmarksForUser.SUCCESS | GetBookmarksForUser.FAILURE;
  payload?: {
    bookmarks: ResourceDict<Bookmark[]>;
  };
}
