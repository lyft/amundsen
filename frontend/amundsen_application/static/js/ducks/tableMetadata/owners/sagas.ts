import { SagaIterator } from 'redux-saga';
import { all, call, put, select, takeEvery } from 'redux-saga/effects';

import * as API from '../api/v0';

import { updateTableOwnerFailure, updateTableOwnerSuccess } from './reducer';

import { UpdateTableOwner, UpdateTableOwnerRequest } from '../types';

export function* updateTableOwnerWorker(
  action: UpdateTableOwnerRequest
): SagaIterator {
  const { payload } = action;
  const state = yield select();
  const { tableData } = state.tableMetadata;
  try {
    const requestList = API.generateOwnerUpdateRequests(
      payload.updateArray,
      tableData
    );
    yield all(requestList);
    const newOwners = yield call(API.getTableOwners, tableData.key);
    yield put(updateTableOwnerSuccess(newOwners));
    if (payload.onSuccess) {
      yield call(payload.onSuccess);
    }
  } catch (e) {
    yield put(updateTableOwnerFailure(state.tableMetadata.tableOwners.owners));
    if (payload.onFailure) {
      yield call(payload.onFailure);
    }
  }
}
export function* updateTableOwnerWatcher(): SagaIterator {
  yield takeEvery(UpdateTableOwner.REQUEST, updateTableOwnerWorker);
}
