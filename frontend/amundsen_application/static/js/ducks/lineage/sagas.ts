import { SagaIterator } from 'redux-saga';
import { call, put, takeEvery } from 'redux-saga/effects';
import * as API from './api/v0';
import {
  getColumnLineageFailure,
  getColumnLineageSuccess,
  getTableLineageFailure,
  getTableLineageSuccess,
  getTableColumnLineageSuccess,
  getTableColumnLineageFailure,
} from './reducer';

import {
  GetColumnLineage,
  GetColumnLineageRequest,
  GetTableLineage,
  GetTableLineageRequest,
  GetTableColumnLineage,
  GetTableColumnLineageRequest,
} from './types';

export function* getTableLineageWorker(
  action: GetTableLineageRequest
): SagaIterator {
  const { key, depth, direction } = action.payload;
  try {
    const response = yield call(API.getTableLineage, key, depth, direction);
    const { data, statusCode } = response;
    yield put(getTableLineageSuccess(data, statusCode));
  } catch (error) {
    const { statusCode } = error;
    yield put(getTableLineageFailure(statusCode));
  }
}
export function* getTableLineageWatcher(): SagaIterator {
  yield takeEvery(GetTableLineage.REQUEST, getTableLineageWorker);
}

export function* getColumnLineageWorker(
  action: GetColumnLineageRequest
): SagaIterator {
  const { key, columnName, depth, direction } = action.payload;
  try {
    const response = yield call(
      API.getColumnLineage,
      key,
      columnName,
      depth,
      direction
    );
    const { data, statusCode } = response;
    yield put(getColumnLineageSuccess(data, statusCode));
  } catch (error) {
    const { statusCode } = error;
    yield put(getColumnLineageFailure(statusCode));
  }
}
export function* getColumnLineageWatcher(): SagaIterator {
  yield takeEvery(GetColumnLineage.REQUEST, getColumnLineageWorker);
}

// ToDo: Please remove once list based view is deprecated
export function* getTableColumnLineageWorker(
  action: GetTableColumnLineageRequest
): SagaIterator {
  const { key, columnName } = action.payload;
  try {
    const response = yield call(
      API.getColumnLineage,
      key,
      columnName,
      1,
      'both'
    );
    const { data, statusCode } = response;
    yield put(getTableColumnLineageSuccess(data, columnName, statusCode));
  } catch (error) {
    const { statusCode } = error;
    yield put(getTableColumnLineageFailure(columnName, statusCode));
  }
}
// ToDo: Please remove once list based view is deprecated
export function* getTableColumnLineageWatcher(): SagaIterator {
  yield takeEvery(GetTableColumnLineage.REQUEST, getTableColumnLineageWorker);
}
