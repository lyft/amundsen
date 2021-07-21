import { testSaga } from 'redux-saga-test-plan';

import { featureMetadata } from 'fixtures/metadata/feature';
import {
  previewDataError,
  previewDataSuccess,
} from 'fixtures/metadata/previewData';

import * as API from './api/v0';
import * as Sagas from './sagas';

import {
  getFeature,
  getFeatureCode,
  getFeatureCodeFailure,
  getFeatureCodeSuccess,
  getFeatureDescription,
  getFeatureDescriptionFailure,
  getFeatureDescriptionSuccess,
  getFeatureFailure,
  getFeaturePreviewData,
  getFeaturePreviewDataFailure,
  getFeaturePreviewDataSuccess,
  getFeatureSuccess,
  updateFeatureDescription,
} from './reducer';
import {
  GetFeature,
  GetFeatureCode,
  GetFeatureDescription,
  GetFeaturePreviewData,
  UpdateFeatureDescription,
} from './types';

describe('feature sagas', () => {
  describe('getFeatureWatcher', () => {
    it('takes every GetFeature.REQUEST with getFeatureWorker', () => {
      testSaga(Sagas.getFeatureWatcher)
        .next()
        .takeEvery(GetFeature.REQUEST, Sagas.getFeatureWorker)
        .next()
        .isDone();
    });
  });

  describe('getFeatureWorker', () => {
    it('executes flow for successfully getting a feature', () => {
      const mockResponse = {
        feature: featureMetadata,
        statusCode: 200,
      };
      testSaga(Sagas.getFeatureWorker, getFeature('testUri', '0', 'source'))
        .next()
        .call(API.getFeature, 'testUri', '0', 'source')
        .next(mockResponse)
        .put(getFeatureSuccess(mockResponse))
        .next()
        .isDone();
    });

    it('executes flow for a failed request feature', () => {
      const mockResponse = {
        statusCode: 500,
        statusMessage: 'oops',
      };
      testSaga(Sagas.getFeatureWorker, getFeature('testUri', '0', 'source'))
        .next()
        .call(API.getFeature, 'testUri', '0', 'source')
        // @ts-ignore
        .throw(mockResponse)
        .put(getFeatureFailure(mockResponse))
        .next()
        .isDone();
    });
  });

  describe('getFeatureCodeWatcher', () => {
    it('takes every GetFeatureCode.REQUEST with getFeatureCodeWorker', () => {
      testSaga(Sagas.getFeatureCodeWatcher)
        .next()
        .takeEvery(GetFeatureCode.REQUEST, Sagas.getFeatureCodeWorker)
        .next()
        .isDone();
    });
  });

  describe('getFeatureCodeWorker', () => {
    it('executes flow for successfully getting feature code', () => {
      const mockResponse = {
        feature: featureMetadata,
        statusCode: 200,
      };
      testSaga(Sagas.getFeatureCodeWorker, getFeatureCode('testUri'))
        .next()
        .call(API.getFeatureCode, 'testUri')
        .next(mockResponse)
        .put(getFeatureCodeSuccess(mockResponse))
        .next()
        .isDone();
    });

    it('executes flow for a failed request feature code', () => {
      const mockResponse = {
        statusCode: 500,
        statusMessage: 'oops',
      };
      testSaga(Sagas.getFeatureCodeWorker, getFeatureCode('testUri'))
        .next()
        .call(API.getFeatureCode, 'testUri')
        // @ts-ignore
        .throw(mockResponse)
        .put(getFeatureCodeFailure(mockResponse))
        .next()
        .isDone();
    });
  });

  describe('getFeaturePreviewDataWatcher', () => {
    it('takes every GetFeaturePreviewData.REQUEST with getFeaturePreviewDataWorker', () => {
      testSaga(Sagas.getFeaturePreviewDataWatcher)
        .next()
        .takeEvery(
          GetFeaturePreviewData.REQUEST,
          Sagas.getFeaturePreviewDataWorker
        )
        .next()
        .isDone();
    });
  });

  describe('getFeaturePreviewDataWorker', () => {
    it('executes flow for successfully getting feature preview data', () => {
      const mockParams = {
        feature_name: 'name',
        feature_group: 'group',
        version: '3',
      };
      const mockResponse = {
        previewData: previewDataSuccess,
        status: 200,
      };
      testSaga(
        Sagas.getFeaturePreviewDataWorker,
        getFeaturePreviewData(mockParams)
      )
        .next()
        .call(API.getFeaturePreviewData, mockParams)
        .next(mockResponse)
        .put(getFeaturePreviewDataSuccess(mockResponse))
        .next()
        .isDone();
    });

    it('executes flow for a failed feature preview data request', () => {
      const mockParams = {
        feature_name: 'name',
        feature_group: 'group',
        version: '3',
      };
      const mockResponse = {
        previewData: previewDataError,
        status: 500,
      };
      testSaga(
        Sagas.getFeaturePreviewDataWorker,
        getFeaturePreviewData(mockParams)
      )
        .next()
        .call(API.getFeaturePreviewData, mockParams)
        // @ts-ignore
        .throw(mockResponse)
        .put(getFeaturePreviewDataFailure(mockResponse))
        .next()
        .isDone();
    });
  });

  describe('getFeatureDescriptionWatcher', () => {
    it('takes every getFeatureDescription.REQUEST with getFeatureDescriptionWorker', () => {
      testSaga(Sagas.getFeatureDescriptionWatcher)
        .next()
        .takeEvery(
          GetFeatureDescription.REQUEST,
          Sagas.getFeatureDescriptionWorker
        );
    });
  });

  describe('getFeatureDescription', () => {
    it('executes flow for successfully getting feature description', () => {
      const mockResponse = {
        description: 'testDescription',
        statusCode: 200,
      };
      const mockState = {
        feature: {
          feature: {
            key: 'testUri',
            description: 'test description',
          },
        },
      };
      testSaga(Sagas.getFeatureDescriptionWorker, getFeatureDescription())
        .next()
        .select()
        .next(mockState)
        .call(API.getFeatureDescription, 'testUri')
        .next(mockResponse)
        .put(getFeatureDescriptionSuccess(mockResponse))
        .next()
        .isDone();
    });

    it('executes flow for a failed request feature code', () => {
      const mockResponse = {
        statusCode: 500,
        statusMessage: 'oops',
      };
      const mockState = {
        feature: {
          feature: {
            key: 'testUri',
            description: 'test description',
          },
        },
      };
      testSaga(Sagas.getFeatureDescriptionWorker, getFeatureDescription())
        .next()
        .select()
        .next(mockState)
        .call(API.getFeatureDescription, 'testUri')
        // @ts-ignore
        .throw(mockResponse)
        .put(getFeatureDescriptionFailure({ description: 'test description' }))
        .next()
        .isDone();
    });
  });

  describe('updateFeatureDescriptionWatcher', () => {
    it('takes every updateFeatureDescription.REQUEST with updateFeatureDescriptionWorker', () => {
      testSaga(Sagas.updateFeatureDescriptionWatcher)
        .next()
        .takeEvery(
          UpdateFeatureDescription.REQUEST,
          Sagas.updateFeatureDescriptionWorker
        );
    });
  });

  describe('updateFeatureDescriptionWorker', () => {
    it('executes flow for successfully updating feature description', () => {
      const mockResponse = {
        description: 'test description',
        statusCode: 200,
      };
      const mockState = {
        feature: {
          feature: {
            key: 'testUri',
            description: 'test description',
          },
        },
      };
      const onSuccess = jest.fn();
      testSaga(
        Sagas.updateFeatureDescriptionWorker,
        updateFeatureDescription('new description', onSuccess)
      )
        .next()
        .select()
        .next(mockState)
        .call(API.updateFeatureDescription, 'testUri', 'new description')
        .next(mockResponse)
        .call(onSuccess)
        .next()
        .isDone();
    });
  });
});
