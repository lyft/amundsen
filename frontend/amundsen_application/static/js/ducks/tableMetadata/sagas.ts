import { SagaIterator } from 'redux-saga';
import { call, put, select, takeEvery, takeLatest } from 'redux-saga/effects';

import * as API from './api/v0';

import {
  getTableDashboardsResponse,
  getTableDataFailure,
  getTableDataSuccess,
  getTableDescriptionFailure,
  getTableDescriptionSuccess,
  getColumnDescriptionFailure,
  getColumnDescriptionSuccess,
  getPreviewDataFailure,
  getPreviewDataSuccess,
  getTableQualityChecksSuccess,
  getTableQualityChecksFailure,
} from './reducer';

import {
  GetPreviewData,
  GetPreviewDataRequest,
  GetTableData,
  GetTableDataRequest,
  GetColumnDescription,
  GetColumnDescriptionRequest,
  GetTableDescription,
  GetTableDescriptionRequest,
  UpdateColumnDescription,
  UpdateColumnDescriptionRequest,
  UpdateTableDescription,
  UpdateTableDescriptionRequest,
  GetTableQualityChecksRequest,
  GetTableQualityChecks,
} from './types';

export function* getTableDataWorker(action: GetTableDataRequest): SagaIterator {
  const { key, searchIndex, source } = action.payload;
  try {
    const { data, owners, statusCode, tags } = yield call(
      API.getTableData,
      key,
      searchIndex,
      source
    );
    yield put(getTableDataSuccess(data, owners, statusCode, tags));

    try {
      const { dashboards } = yield call(API.getTableDashboards, key);
      yield put(getTableDashboardsResponse(dashboards));
    } catch (error) {
      yield put(getTableDashboardsResponse([], error.msg));
    }
  } catch (e) {
    yield put(getTableDataFailure());
  }
}
export function* getTableDataWatcher(): SagaIterator {
  yield takeEvery(GetTableData.REQUEST, getTableDataWorker);
}

export function* getTableDescriptionWorker(
  action: GetTableDescriptionRequest
): SagaIterator {
  const { payload } = action;
  const state = yield select();
  let { tableData } = state.tableMetadata;
  try {
    tableData = yield call(
      API.getTableDescription,
      state.tableMetadata.tableData
    );
    yield put(getTableDescriptionSuccess(tableData));
    if (payload.onSuccess) {
      yield call(payload.onSuccess);
    }
  } catch (e) {
    yield put(getTableDescriptionFailure(tableData));
    if (payload.onFailure) {
      yield call(payload.onFailure);
    }
  }
}
export function* getTableDescriptionWatcher(): SagaIterator {
  yield takeEvery(GetTableDescription.REQUEST, getTableDescriptionWorker);
}

export function* updateTableDescriptionWorker(
  action: UpdateTableDescriptionRequest
): SagaIterator {
  const { payload } = action;
  const state = yield select();
  try {
    yield call(
      API.updateTableDescription,
      payload.newValue,
      state.tableMetadata.tableData
    );
    if (payload.onSuccess) {
      yield call(payload.onSuccess);
    }
  } catch (e) {
    if (payload.onFailure) {
      yield call(payload.onFailure);
    }
  }
}
export function* updateTableDescriptionWatcher(): SagaIterator {
  yield takeEvery(UpdateTableDescription.REQUEST, updateTableDescriptionWorker);
}

export function* getColumnDescriptionWorker(
  action: GetColumnDescriptionRequest
): SagaIterator {
  const { payload } = action;
  const state = yield select();
  let { tableData } = state.tableMetadata;
  try {
    tableData = yield call(
      API.getColumnDescription,
      payload.columnIndex,
      state.tableMetadata.tableData
    );
    yield put(getColumnDescriptionSuccess(tableData));
    if (payload.onSuccess) {
      yield call(payload.onSuccess);
    }
  } catch (e) {
    yield put(getColumnDescriptionFailure(tableData));
    if (payload.onFailure) {
      yield call(payload.onFailure);
    }
  }
}
export function* getColumnDescriptionWatcher(): SagaIterator {
  yield takeEvery(GetColumnDescription.REQUEST, getColumnDescriptionWorker);
}

export function* updateColumnDescriptionWorker(
  action: UpdateColumnDescriptionRequest
): SagaIterator {
  const { payload } = action;
  const state = yield select();
  try {
    yield call(
      API.updateColumnDescription,
      payload.newValue,
      payload.columnIndex,
      state.tableMetadata.tableData
    );
    if (payload.onSuccess) {
      yield call(payload.onSuccess);
    }
  } catch (e) {
    if (payload.onFailure) {
      yield call(payload.onFailure);
    }
  }
}
export function* updateColumnDescriptionWatcher(): SagaIterator {
  yield takeEvery(
    UpdateColumnDescription.REQUEST,
    updateColumnDescriptionWorker
  );
}

export function* getPreviewDataWorker(
  action: GetPreviewDataRequest
): SagaIterator {
  try {
    const response = yield call(API.getPreviewData, action.payload.queryParams);
    const { data, status } = response;
    yield put(getPreviewDataSuccess(data, status));
  } catch (error) {
    const { data, status } = error;
    yield put(getPreviewDataFailure(data, status));
  }
}
export function* getPreviewDataWatcher(): SagaIterator {
  yield takeLatest(GetPreviewData.REQUEST, getPreviewDataWorker);
}

export function* getTableQualityChecksWorker(
  action: GetTableQualityChecksRequest
): SagaIterator {
  const { key } = action.payload;
  try {
    const response = yield call(API.getTableQualityChecks, key);
    const { checks, status } = response;
    yield put(getTableQualityChecksSuccess(checks, status));
  } catch (error) {
    const { status } = error;
    yield put(getTableQualityChecksFailure(status));
  }
}
export function* getTableQualityChecksWatcher(): SagaIterator {
  yield takeLatest(GetTableQualityChecks.REQUEST, getTableQualityChecksWorker);
}
