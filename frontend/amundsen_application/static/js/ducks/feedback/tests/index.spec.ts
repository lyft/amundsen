import { testSaga } from 'redux-saga-test-plan';

import { SendingState } from 'interfaces';

import * as API from '../api/v0';
import reducer, {
  submitFeedback,
  submitFeedbackFailure,
  submitFeedbackSuccess,
  resetFeedback,
  FeedbackReducerState,
} from '../reducer';
import { submitFeedbackWorker, submitFeedbackWatcher } from '../sagas';
import { SubmitFeedback, SubmitFeedbackRequest, ResetFeedback } from '../types';

describe('feedback ducks', () => {
  let formData: FormData;
  beforeAll(() => {
    formData = new FormData();
    const testData = { rating: 10, comment: 'This is a test' };
    Object.keys(testData).forEach((key) => formData.append(key, testData[key]));
  });

  describe('actions', () => {
    it('submitFeedback - returns the action to submit feedback', () => {
      const action = submitFeedback(formData);
      const { payload } = action;
      expect(action.type).toBe(SubmitFeedback.REQUEST);
      expect(payload.data).toBe(formData);
    });

    it('submitFeedbackFailure - returns the action to process failure', () => {
      const action = submitFeedbackFailure();
      expect(action.type).toBe(SubmitFeedback.FAILURE);
    });

    it('submitFeedbackSuccess - returns the action to process success', () => {
      const action = submitFeedbackSuccess();
      expect(action.type).toBe(SubmitFeedback.SUCCESS);
    });

    it('resetFeedback - returns the action to reset feedback', () => {
      const action = resetFeedback();
      expect(action.type).toBe(ResetFeedback.REQUEST);
    });
  });

  describe('reducer', () => {
    let testState: FeedbackReducerState;
    beforeAll(() => {
      testState = { sendState: SendingState.IDLE };
    });

    it('should return the existing state if action is not handled', () => {
      expect(reducer(testState, { type: 'INVALID.ACTION' })).toEqual(testState);
    });

    it('should handle SubmitFeedback.REQUEST', () => {
      expect(reducer(testState, submitFeedback(formData))).toEqual({
        sendState: SendingState.WAITING,
      });
    });

    it('should handle SubmitFeedback.SUCCESS', () => {
      expect(reducer(testState, submitFeedbackSuccess())).toEqual({
        sendState: SendingState.COMPLETE,
      });
    });

    it('should handle SubmitFeedback.FAILURE', () => {
      expect(reducer(testState, submitFeedbackFailure())).toEqual({
        sendState: SendingState.ERROR,
      });
    });

    it('should handle ResetFeedback.REQUEST', () => {
      expect(reducer(testState, resetFeedback())).toEqual({
        sendState: SendingState.IDLE,
      });
    });
  });

  describe('sagas', () => {
    let action: SubmitFeedbackRequest;
    beforeAll(() => {
      action = submitFeedback(formData);
    });

    describe('submitFeedbackWatcher', () => {
      it('takes every SubmitFeedback.REQUEST with submitFeedbackWorker', () => {
        testSaga(submitFeedbackWatcher)
          .next()
          .takeEvery(SubmitFeedback.REQUEST, submitFeedbackWorker)
          .next()
          .isDone();
      });
    });

    describe('submitFeedbackWorker', () => {
      it('executes submit feedback flow', () => {
        testSaga(submitFeedbackWorker, action)
          .next()
          .call(API.submitFeedback, formData)
          .next()
          .put(submitFeedbackSuccess())
          .next()
          .delay(2000)
          .next()
          .put(resetFeedback())
          .next()
          .isDone();
      });

      it('handles request error', () => {
        testSaga(submitFeedbackWorker, action)
          .next()
          .throw(new Error())
          .put(submitFeedbackFailure())
          .next()
          .delay(2000)
          .next()
          .put(resetFeedback())
          .next()
          .isDone();
      });
    });
  });
});
