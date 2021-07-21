import { AnnouncementPost } from 'interfaces';

import {
  GetAnnouncements,
  GetAnnouncementsRequest,
  GetAnnouncementsResponse,
  GetAnnouncementsPayload,
} from './types';

/* ACTIONS */
export function getAnnouncements(): GetAnnouncementsRequest {
  return { type: GetAnnouncements.REQUEST };
}
export function getAnnouncementsFailure(
  payload: GetAnnouncementsPayload
): GetAnnouncementsResponse {
  return { type: GetAnnouncements.FAILURE, payload };
}
export function getAnnouncementsSuccess(
  payload: GetAnnouncementsPayload
): GetAnnouncementsResponse {
  return {
    type: GetAnnouncements.SUCCESS,
    payload,
  };
}

/* REDUCER */
export interface AnnouncementsReducerState {
  posts: AnnouncementPost[];
  isLoading: boolean;
  statusCode: number | null;
}

export const initialState: AnnouncementsReducerState = {
  posts: [],
  isLoading: true,
  statusCode: null,
};

export default function reducer(
  state: AnnouncementsReducerState = initialState,
  action
): AnnouncementsReducerState {
  switch (action.type) {
    case GetAnnouncements.REQUEST:
      return {
        ...state,
        isLoading: true,
        statusCode: null,
      };
    case GetAnnouncements.FAILURE:
      return {
        ...state,
        isLoading: false,
        statusCode: action.payload.statusCode,
      };
    case GetAnnouncements.SUCCESS: {
      const { payload } = <GetAnnouncementsResponse>action;
      if (payload === undefined) {
        throw Error('payload must be set for GetAnnouncements.SUCCESS');
      }
      return {
        ...state,
        isLoading: false,
        statusCode: action.payload.statusCode,
        posts: payload.posts || [],
      };
    }
    default:
      return state;
  }
}
