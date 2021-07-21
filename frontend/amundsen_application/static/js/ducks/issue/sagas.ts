import { SagaIterator } from 'redux-saga';
import { call, put, takeEvery } from 'redux-saga/effects';

import {
  getIssuesSuccess,
  getIssuesFailure,
  createIssueSuccess,
  createIssueFailure,
} from './reducer';

import {
  GetIssues,
  GetIssuesRequest,
  CreateIssue,
  CreateIssueRequest,
} from './types';

import * as API from './api/v0';

export function* getIssuesWorker(action: GetIssuesRequest): SagaIterator {
  const { key } = action.payload;

  try {
    const response = yield call(API.getIssues, key);

    yield put(
      getIssuesSuccess(response.issues, response.total, response.all_issues_url)
    );
  } catch (e) {
    yield put(getIssuesFailure([], 0, undefined));
  }
}

export function* getIssuesWatcher(): SagaIterator {
  yield takeEvery(GetIssues.REQUEST, getIssuesWorker);
}

export function* createIssueWorker(action: CreateIssueRequest): SagaIterator {
  try {
    const response = yield call(
      API.createIssue,
      action.payload.createIssuePayload,
      action.payload.notificationPayload
    );

    yield put(createIssueSuccess(response));
  } catch (error) {
    yield put(createIssueFailure(undefined));
  }
}

export function* createIssueWatcher(): SagaIterator {
  yield takeEvery(CreateIssue.REQUEST, createIssueWorker);
}
