import { testSaga } from 'redux-saga-test-plan';

import * as API from '../api/v0';

import reducer, {
  getLastIndexed,
  getLastIndexedFailure,
  getLastIndexedSuccess,
  initialState,
  LastIndexedReducerState,
} from '../reducer';

import { getLastIndexedWatcher, getLastIndexedWorker } from '../sagas';
import { GetLastIndexed } from '../types';

describe('lastIndexed ducks', () => {
  let testEpoch: number;

  beforeAll(() => {
    testEpoch = 1545925769;
  });

  describe('actions', () => {
    it('getLastIndexed - returns the action to get the last indexed date', () => {
      const action = getLastIndexed();
      expect(action.type).toBe(GetLastIndexed.REQUEST);
    });

    it('getLastIndexedFailure - returns the action to process failure', () => {
      const action = getLastIndexedFailure();
      expect(action.type).toBe(GetLastIndexed.FAILURE);
    });

    it('getLastIndexedSuccess - returns the action to process success', () => {
      const action = getLastIndexedSuccess(testEpoch);
      const { payload } = action;
      expect(action.type).toBe(GetLastIndexed.SUCCESS);
      expect(payload?.lastIndexedEpoch).toBe(testEpoch);
    });
  });

  describe('reducer', () => {
    let testState: LastIndexedReducerState;
    beforeAll(() => {
      testState = initialState;
    });

    it('should return the existing state if action is not handled', () => {
      expect(reducer(testState, { type: 'INVALID.ACTION' })).toEqual(testState);
    });

    it('should handle GetLastIndexed.REQUEST', () => {
      expect(reducer(testState, getLastIndexed())).toEqual(initialState);
    });

    it('should handle GetLastIndexed.FAILURE', () => {
      expect(reducer(testState, getLastIndexedFailure())).toEqual({
        lastIndexed: null,
      });
    });

    it('should handle GetLastIndexed.SUCCESS', () => {
      expect(reducer(testState, getLastIndexedSuccess(testEpoch))).toEqual({
        lastIndexed: testEpoch,
      });
    });
  });

  describe('sagas', () => {
    describe('getLastIndexedWatcher', () => {
      it('takes every GetLastIndexed.REQUEST with getLastIndexedWorker', () => {
        testSaga(getLastIndexedWatcher)
          .next()
          .takeEvery(GetLastIndexed.REQUEST, getLastIndexedWorker)
          .next()
          .isDone();
      });
    });

    describe('getLastIndexedWorker', () => {
      it('executes flow for getting last indexed value', () => {
        testSaga(getLastIndexedWorker, getLastIndexed())
          .next()
          .call(API.getLastIndexed)
          .next(testEpoch)
          .put(getLastIndexedSuccess(testEpoch))
          .next()
          .isDone();
      });

      it('handles request error', () => {
        testSaga(getLastIndexedWorker, getLastIndexed())
          .next()
          .throw(new Error())
          .put(getLastIndexedFailure())
          .next()
          .isDone();
      });
    });
  });
});
