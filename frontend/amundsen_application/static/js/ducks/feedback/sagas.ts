import { SagaIterator } from 'redux-saga';
import { call, delay, put, takeEvery } from 'redux-saga/effects';

import * as API from './api/v0';
import {
  submitFeedbackFailure,
  submitFeedbackSuccess,
  resetFeedback,
} from './reducer';
import { SubmitFeedback, SubmitFeedbackRequest } from './types';

export function* submitFeedbackWorker(
  action: SubmitFeedbackRequest
): SagaIterator {
  try {
    yield call(API.submitFeedback, action.payload.data);
    yield put(submitFeedbackSuccess());

    yield delay(2000);
    yield put(resetFeedback());
  } catch (error) {
    yield put(submitFeedbackFailure());

    yield delay(2000);
    yield put(resetFeedback());
  }
}

export function* submitFeedbackWatcher(): SagaIterator {
  yield takeEvery(SubmitFeedback.REQUEST, submitFeedbackWorker);
}
