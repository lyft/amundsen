import { Issue, CreateIssuePayload, NotificationPayload } from 'interfaces';
import {
  GetIssues,
  CreateIssue,
  GetIssuesResponse,
  CreateIssueRequest,
  GetIssuesRequest,
  CreateIssueResponse,
} from './types';

/* ACTIONS */
export function createIssue(
  createIssuePayload: CreateIssuePayload,
  notificationPayload: NotificationPayload
): CreateIssueRequest {
  return {
    payload: {
      createIssuePayload,
      notificationPayload,
    },
    type: CreateIssue.REQUEST,
  };
}

export function createIssueSuccess(issue: Issue): CreateIssueResponse {
  return {
    type: CreateIssue.SUCCESS,
    payload: {
      issue,
    },
  };
}

export function createIssueFailure(issue?: Issue): CreateIssueResponse {
  return {
    type: CreateIssue.FAILURE,
    payload: {
      issue,
    },
  };
}

export function getIssues(tableKey: string): GetIssuesRequest {
  return {
    type: GetIssues.REQUEST,
    payload: {
      key: tableKey,
    },
  };
}

export function getIssuesSuccess(
  issues: Issue[],
  total?: number,
  allIssuesUrl?: string
): GetIssuesResponse {
  return {
    type: GetIssues.SUCCESS,
    payload: {
      issues,
      total,
      allIssuesUrl,
    },
  };
}

export function getIssuesFailure(
  issues: Issue[],
  total?: number,
  allIssuesUrl?: string
): GetIssuesResponse {
  return {
    type: GetIssues.FAILURE,
    payload: {
      issues,
      total,
      allIssuesUrl,
    },
  };
}

/* REDUCER */
export interface IssueReducerState {
  issues: Issue[];
  allIssuesUrl?: string;
  total?: number;
  isLoading: boolean;
}

export const initialIssuestate: IssueReducerState = {
  issues: [],
  allIssuesUrl: undefined,
  total: 0,
  isLoading: false,
};

export default function reducer(
  state: IssueReducerState = initialIssuestate,
  action
): IssueReducerState {
  switch (action.type) {
    case GetIssues.REQUEST:
      return {
        ...initialIssuestate,
        isLoading: true,
      };
    case GetIssues.FAILURE:
      return { ...initialIssuestate };
    case GetIssues.SUCCESS:
      return {
        ...state,
        ...(<GetIssuesResponse>action).payload,
        isLoading: false,
      };
    case CreateIssue.REQUEST:
      return { ...state, isLoading: true };
    case CreateIssue.FAILURE:
      return { ...state, isLoading: false };
    case CreateIssue.SUCCESS:
      const { issue } = (<CreateIssueResponse>action).payload;
      if (issue === undefined) {
        throw Error('payload.issue must be set for CreateIssue.SUCCESS');
      }
      return {
        ...state,
        issues: [issue, ...state.issues],
        isLoading: false,
      };
    default:
      return state;
  }
}
