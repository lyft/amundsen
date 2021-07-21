import { testSaga } from 'redux-saga-test-plan';

import { PopularResource, ResourceDict, ResourceType } from 'interfaces';

import globalState from 'fixtures/globalState';

import * as API from './api/v0';
import reducer, {
  getPopularResources,
  getPopularResourcesFailure,
  getPopularResourcesSuccess,
  PopularResourcesReducerState,
} from './reducer';
import { getPopularResourcesWorker, getPopularResourcesWatcher } from './sagas';
import { GetPopularResources } from './types';

describe('popularResources ducks', () => {
  let expectedResources: ResourceDict<PopularResource[]>;

  beforeAll(() => {
    expectedResources = globalState.popularResources.popularResources;
  });

  describe('actions', () => {
    it('getPopularResources - returns the action to get popular resources', () => {
      const action = getPopularResources();
      expect(action.type).toBe(GetPopularResources.REQUEST);
    });

    it('getPopularResourcesFailure - returns the action to process failure', () => {
      const action = getPopularResourcesFailure();
      const { payload } = action;
      expect(action.type).toBe(GetPopularResources.FAILURE);
      expect(payload.popularResources).toEqual({ dashboard: [], table: [] });
    });

    it('getPopularResourcesSuccess - returns the action to process success', () => {
      const action = getPopularResourcesSuccess(expectedResources);
      const { payload } = action;
      expect(action.type).toBe(GetPopularResources.SUCCESS);
      expect(payload.popularResources).toBe(expectedResources);
    });
  });

  describe('reducer', () => {
    let testState: PopularResourcesReducerState;

    beforeAll(() => {
      testState = {
        popularResourcesIsLoaded: false,
        popularResources: {
          [ResourceType.table]: [],
          [ResourceType.dashboard]: [],
        },
      };
    });

    it('should return the existing state if action is not handled', () => {
      expect(reducer(testState, { type: 'INVALID.ACTION' })).toEqual(testState);
    });

    it('should handle GetPopularResources.SUCCESS', () => {
      const expected = expectedResources;
      const actual = reducer(
        testState,
        getPopularResourcesSuccess(expectedResources)
      ).popularResources;

      expect(actual).toEqual(expected);
    });

    it('should handle GetPopularResources.FAILURE', () => {
      const expected = {
        popularResources: {
          dashboard: [],
          table: [],
        },
        popularResourcesIsLoaded: true,
      };
      const actual = reducer(testState, getPopularResourcesFailure());

      expect(actual).toEqual(expected);
    });
  });

  describe('sagas', () => {
    describe('getPopularResourcesWatcher', () => {
      it('takes every GetPopularResources.REQUEST with getPopularResourcesWorker', () => {
        testSaga(getPopularResourcesWatcher)
          .next()
          .takeEvery(GetPopularResources.REQUEST, getPopularResourcesWorker)
          .next()
          .isDone();
      });
    });

    describe('getPopularResourcesWorker', () => {
      it('executes flow for returning tables', () => {
        testSaga(getPopularResourcesWorker)
          .next()
          .call(API.getPopularResources)
          .next(expectedResources)
          .put(getPopularResourcesSuccess(expectedResources))
          .next()
          .isDone();
      });

      it('handles request error', () => {
        testSaga(getPopularResourcesWorker)
          .next()
          .throw(new Error())
          .put(getPopularResourcesFailure())
          .next()
          .isDone();
      });
    });
  });
});
