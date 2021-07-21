import { SagaIterator } from 'redux-saga';
import { call, put, takeEvery } from 'redux-saga/effects';
import { sendNotification } from './api/v0';

import {
  submitNotificationFailure,
  submitNotificationSuccess,
} from './reducer';
import { SubmitNotification, SubmitNotificationRequest } from './types';

export function* submitNotificationWorker(
  action: SubmitNotificationRequest
): SagaIterator {
  try {
    const { notificationType, options, recipients, sender } = action.payload;
    yield call(sendNotification, recipients, sender, notificationType, options);
    yield put(submitNotificationSuccess());
  } catch (error) {
    yield put(submitNotificationFailure());
  }
}

export function* submitNotificationWatcher(): SagaIterator {
  yield takeEvery(SubmitNotification.REQUEST, submitNotificationWorker);
}
