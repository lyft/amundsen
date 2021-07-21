import { testSaga } from 'redux-saga-test-plan';

import { dashboardMetadata } from 'fixtures/metadata/dashboard';
import * as API from './api/v0';
import * as Sagas from './sagas';

import {
  getDashboard,
  getDashboardFailure,
  getDashboardSuccess,
} from './reducer';
import { GetDashboard } from './types';

describe('dashboard sagas', () => {
  describe('getDashboardWatcher', () => {
    it('takes every GetDashboard.REQUEST with getDashboardWorker', () => {
      testSaga(Sagas.getDashboardWatcher)
        .next()
        .takeEvery(GetDashboard.REQUEST, Sagas.getDashboardWorker)
        .next()
        .isDone();
    });
  });

  describe('getDashboardWorker', () => {
    it('executes flow for successfully getting a dashboard', () => {
      const mockResponse = {
        dashboard: dashboardMetadata,
        statusCode: 200,
      };
      testSaga(
        Sagas.getDashboardWorker,
        getDashboard({ uri: 'testUri', searchIndex: '0', source: 'blah' })
      )
        .next()
        .call(API.getDashboard, 'testUri', '0', 'blah')
        .next(mockResponse)
        .put(getDashboardSuccess(mockResponse))
        .next()
        .isDone();
    });

    it('executes flow for a failed request dashboard', () => {
      const mockResponse = {
        statusCode: 200,
        statusMessage: 'oops',
      };
      testSaga(
        Sagas.getDashboardWorker,
        getDashboard({ uri: 'testUri', searchIndex: '0', source: 'blah' })
      )
        .next()
        .call(API.getDashboard, 'testUri', '0', 'blah')
        // @ts-ignore
        .throw(mockResponse)
        .put(getDashboardFailure(mockResponse))
        .next()
        .isDone();
    });
  });
});
