import { SagaIterator } from 'redux-saga';
import { call, put, takeEvery } from 'redux-saga/effects';

import * as API from './api/v0';
import { getAnnouncementsFailure, getAnnouncementsSuccess } from '.';
import { GetAnnouncements } from './types';

export function* getAnnouncementsWorker(): SagaIterator {
  try {
    const response = yield call(API.getAnnouncements);

    yield put(getAnnouncementsSuccess(response));
  } catch (error) {
    yield put(getAnnouncementsFailure(error));
  }
}
export function* getAnnouncementsWatcher(): SagaIterator {
  yield takeEvery(GetAnnouncements.REQUEST, getAnnouncementsWorker);
}
