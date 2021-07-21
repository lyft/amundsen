import { SagaIterator } from 'redux-saga';
import { call, put, takeEvery } from 'redux-saga/effects';

import * as API from './api/v0';
import { getDashboardSuccess, getDashboardFailure } from './reducer';
import { GetDashboard } from './types';

export function* getDashboardWorker(action): SagaIterator {
  try {
    const { uri, searchIndex, source } = action.payload;
    const response = yield call(API.getDashboard, uri, searchIndex, source);

    yield put(getDashboardSuccess(response));
  } catch (error) {
    yield put(getDashboardFailure(error));
  }
}

export function* getDashboardWatcher(): SagaIterator {
  yield takeEvery(GetDashboard.REQUEST, getDashboardWorker);
}
