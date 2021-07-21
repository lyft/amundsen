import { SagaIterator } from 'redux-saga';
import { call, put, takeEvery } from 'redux-saga/effects';

import * as API from './api/v0';
import {
  getPopularResourcesFailure,
  getPopularResourcesSuccess,
} from './reducer';
import { GetPopularResources } from './types';

export function* getPopularResourcesWorker(): SagaIterator {
  try {
    const popularResources = yield call(API.getPopularResources);
    yield put(getPopularResourcesSuccess(popularResources));
  } catch (e) {
    yield put(getPopularResourcesFailure());
  }
}

export function* getPopularResourcesWatcher(): SagaIterator {
  yield takeEvery(GetPopularResources.REQUEST, getPopularResourcesWorker);
}
