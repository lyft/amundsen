import { testSaga } from 'redux-saga-test-plan';

import { OwnerDict, UpdateMethod, UpdateOwnerPayload } from 'interfaces';

import globalState from 'fixtures/globalState';

import * as API from '../api/v0';

import reducer, {
  updateTableOwner,
  updateTableOwnerFailure,
  updateTableOwnerSuccess,
  initialOwnersState,
  TableOwnerReducerState,
} from './reducer';
import {
  getTableData,
  getTableDataFailure,
  getTableDataSuccess,
} from '../reducer';

import { updateTableOwnerWorker, updateTableOwnerWatcher } from './sagas';

import { UpdateTableOwner } from '../types';

jest.spyOn(API, 'generateOwnerUpdateRequests').mockImplementation(() => []);

describe('tableMetadata:owners ducks', () => {
  let expectedOwners: OwnerDict;
  let updatePayload: UpdateOwnerPayload[];
  let mockSuccess;
  let mockFailure;
  beforeAll(() => {
    expectedOwners = {
      testId: {
        display_name: 'test',
        profile_url: 'test.io',
        email: 'test@test.com',
        user_id: 'testId',
      },
    };
    updatePayload = [{ method: UpdateMethod.PUT, id: 'testId' }];
    mockSuccess = jest.fn();
    mockFailure = jest.fn();
  });

  describe('actions', () => {
    it('updateTableOwner - returns the action to update table owners', () => {
      const action = updateTableOwner(updatePayload, mockSuccess, mockFailure);
      const { payload } = action;
      expect(action.type).toBe(UpdateTableOwner.REQUEST);
      expect(payload.updateArray).toBe(updatePayload);
      expect(payload.onSuccess).toBe(mockSuccess);
      expect(payload.onFailure).toBe(mockFailure);
    });

    it('updateTableOwnerFailure - returns the action to process failure', () => {
      const action = updateTableOwnerFailure(expectedOwners);
      const { payload } = action;
      expect(action.type).toBe(UpdateTableOwner.FAILURE);
      expect(payload.owners).toBe(expectedOwners);
    });

    it('updateTableOwnerSuccess - returns the action to process success', () => {
      const action = updateTableOwnerSuccess(expectedOwners);
      const { payload } = action;
      expect(action.type).toBe(UpdateTableOwner.SUCCESS);
      expect(payload.owners).toBe(expectedOwners);
    });
  });

  describe('reducer', () => {
    let testState: TableOwnerReducerState;
    beforeAll(() => {
      testState = initialOwnersState;
    });
    it('should return the existing state if action is not handled', () => {
      expect(reducer(testState, { type: 'INVALID.ACTION' })).toEqual(testState);
    });

    it('should handle UpdateTableOwner.REQUEST', () => {
      expect(
        reducer(
          testState,
          updateTableOwner(updatePayload, mockSuccess, mockFailure)
        )
      ).toEqual({
        ...testState,
        isLoading: true,
      });
    });

    it('should handle UpdateTableOwner.FAILURE', () => {
      expect(
        reducer(testState, updateTableOwnerFailure(expectedOwners))
      ).toEqual({
        ...testState,
        isLoading: false,
        owners: expectedOwners,
      });
    });

    it('should handle UpdateTableOwner.SUCCESS', () => {
      expect(
        reducer(testState, updateTableOwnerSuccess(expectedOwners))
      ).toEqual({
        ...testState,
        isLoading: false,
        owners: expectedOwners,
      });
    });

    it('should handle GetTableData.REQUEST', () => {
      expect(reducer(testState, getTableData('testKey'))).toEqual({
        ...testState,
        isLoading: true,
        owners: {},
      });
    });

    it('should handle GetTableData.FAILURE', () => {
      const action = getTableDataFailure();
      expect(reducer(testState, action)).toEqual({
        ...testState,
        isLoading: false,
        owners: action.payload.owners,
      });
    });

    it('should handle GetTableData.SUCCESS', () => {
      const mockTableData = globalState.tableMetadata.tableData;
      expect(
        reducer(
          testState,
          getTableDataSuccess(mockTableData, expectedOwners, 200, [])
        )
      ).toEqual({
        ...testState,
        isLoading: false,
        owners: expectedOwners,
      });
    });
  });

  describe('sagas', () => {
    describe('updateTableOwnerWatcher', () => {
      it('takes every UpdateTableOwner.REQUEST with updateTableOwnerWorker', () => {
        testSaga(updateTableOwnerWatcher)
          .next()
          .takeEvery(UpdateTableOwner.REQUEST, updateTableOwnerWorker);
      });
    });

    describe('updateTableOwnerWorker', () => {
      describe('executes flow for updating owners and returning up to date owner dict', () => {
        let sagaTest;
        beforeAll(() => {
          sagaTest = (action) =>
            testSaga(updateTableOwnerWorker, action)
              .next()
              .select()
              .next(globalState)
              .all(
                API.generateOwnerUpdateRequests(
                  updatePayload,
                  globalState.tableMetadata.tableData
                )
              )
              .next()
              .call(API.getTableOwners, globalState.tableMetadata.tableData.key)
              .next(expectedOwners)
              .put(updateTableOwnerSuccess(expectedOwners));
        });
        it('without success callback', () => {
          sagaTest(updateTableOwner(updatePayload)).next().isDone();
        });

        it('with success callback', () => {
          sagaTest(updateTableOwner(updatePayload, mockSuccess, mockFailure))
            .next()
            .call(mockSuccess)
            .next()
            .isDone();
        });
      });

      describe('handles request error', () => {
        let sagaTest;
        beforeAll(() => {
          sagaTest = (action) =>
            testSaga(updateTableOwnerWorker, action)
              .next()
              .select()
              .next(globalState)
              .throw(new Error())
              .put(
                updateTableOwnerFailure(
                  globalState.tableMetadata.tableOwners.owners
                )
              );
        });
        it('without failure callback', () => {
          sagaTest(updateTableOwner(updatePayload)).next().isDone();
        });

        it('with failure callback', () => {
          sagaTest(updateTableOwner(updatePayload, mockSuccess, mockFailure))
            .next()
            .call(mockFailure)
            .next()
            .isDone();
        });
      });
    });
  });
});
