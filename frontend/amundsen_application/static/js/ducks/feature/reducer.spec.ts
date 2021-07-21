// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import reducer, {
  getFeature,
  getFeatureFailure,
  getFeatureSuccess,
  FeatureReducerState,
  initialFeatureState,
  initialFeatureCodeState,
  initialPreviewState,
  emptyFeatureCode,
  getFeatureCode,
  getFeatureCodeSuccess,
  getFeatureCodeFailure,
  getFeatureDescriptionSuccess,
  updateFeatureDescriptionSuccess,
  updateFeatureDescriptionFailure,
  initialFeatureLineageState,
  getFeaturePreviewDataSuccess,
  getFeaturePreviewDataFailure,
  getFeaturePreviewData,
} from 'ducks/feature/reducer';
import { featureMetadata } from 'fixtures/metadata/feature';

describe('feature reducer', () => {
  let testState: FeatureReducerState;
  beforeEach(() => {
    testState = {
      isLoading: false,
      isLoadingOwners: false,
      statusCode: 200,
      feature: initialFeatureState,
      featureCode: initialFeatureCodeState,
      featureLineage: initialFeatureLineageState,
      preview: initialPreviewState,
    };
  });

  it('should return the existing state if action is not handled', () => {
    expect(reducer(testState, { type: 'INVALID.ACTION' })).toEqual(testState);
  });

  it('should handle getFeature.REQUEST', () => {
    expect(reducer(testState, getFeature('testKey'))).toEqual({
      ...testState,
      isLoading: true,
      statusCode: null,
    });
  });

  it('should handle GetFeature.SUCCESS', () => {
    expect(
      reducer(
        testState,
        getFeatureSuccess({
          feature: featureMetadata,
          statusCode: 202,
        })
      )
    ).toEqual({
      ...testState,
      isLoading: false,
      statusCode: 202,
      feature: featureMetadata,
      featureCode: initialFeatureCodeState,
    });
  });

  it('should handle GetFeature.FAILURE', () => {
    expect(
      reducer(
        testState,
        getFeatureFailure({
          statusCode: 500,
        })
      )
    ).toEqual({
      ...testState,
      isLoading: false,
      statusCode: 500,
      feature: initialFeatureState,
      featureCode: initialFeatureCodeState,
    });
  });

  it('should handle getFeatureCode.REQUEST', () => {
    expect(reducer(testState, getFeatureCode('testKey'))).toEqual({
      ...testState,
      featureCode: {
        isLoading: true,
        statusCode: null,
        featureCode: emptyFeatureCode,
      },
    });
  });

  it('should handle GetFeatureCode.SUCCESS', () => {
    const response = {
      featureCode: {
        key: 'testKey',
        source: 'testSource',
        text: 'testText',
      },
      statusCode: 202,
    };

    expect(reducer(testState, getFeatureCodeSuccess(response))).toEqual({
      ...testState,
      featureCode: {
        featureCode: response.featureCode,
        statusCode: response.statusCode,
        isLoading: false,
      },
    });
  });

  it('should handle GetFeatureCode.FAILURE', () => {
    expect(
      reducer(
        testState,
        getFeatureCodeFailure({
          statusCode: 500,
        })
      )
    ).toEqual({
      ...testState,
      featureCode: {
        featureCode: emptyFeatureCode,
        statusCode: 500,
        isLoading: false,
      },
    });
  });

  it('should handle GetFeaturePreviewData.REQUEST', () => {
    const request = {
      feature_name: 'name',
      feature_group: 'group',
      version: '3',
    };
    expect(reducer(testState, getFeaturePreviewData(request))).toEqual({
      ...testState,
      preview: {
        isLoading: true,
        previewData: {},
        status: null,
      },
    });
  });

  it('should handle GetFeaturePreviewData.SUCCESS', () => {
    const response = {
      previewData: {
        columns: [],
        data: [],
        error_text: '',
      },
      status: 202,
    };

    expect(reducer(testState, getFeaturePreviewDataSuccess(response))).toEqual({
      ...testState,
      preview: {
        isLoading: false,
        previewData: response.previewData,
        status: response.status,
      },
    });
  });

  it('should handle GetFeaturePreviewData.FAILURE', () => {
    const response = {
      previewData: {
        error_text: 'error message',
      },
      status: 502,
    };

    expect(reducer(testState, getFeaturePreviewDataFailure(response))).toEqual({
      ...testState,
      preview: {
        isLoading: false,
        previewData: response.previewData,
        status: response.status,
      },
    });
  });

  it('should handle GetFeatureDescription.SUCCESS', () => {
    const response = {
      description: 'testDescription',
      statusCode: 200,
    };
    expect(reducer(testState, getFeatureDescriptionSuccess(response))).toEqual({
      ...testState,
      feature: {
        ...testState.feature,
        description: response.description,
      },
    });
  });

  it('should handle GetFeatureDescription.FAILURE', () => {
    const response = {
      description: 'testDescription',
      statusCode: 500,
    };
    expect(reducer(testState, getFeatureDescriptionSuccess(response))).toEqual({
      ...testState,
      feature: {
        ...testState.feature,
        description: response.description,
      },
    });
  });

  it('should handle UpdateFeatureDescription.SUCCESS', () => {
    const response = {
      description: 'testDescription',
      statusCode: 200,
    };
    expect(
      reducer(testState, updateFeatureDescriptionSuccess(response))
    ).toEqual({
      ...testState,
      feature: {
        ...testState.feature,
        description: response.description,
      },
    });
  });

  it('should handle UpdateFeatureDescription.FAILURE', () => {
    const response = {
      description: 'testDescription',
      statusCode: 200,
    };
    expect(
      reducer(testState, updateFeatureDescriptionFailure(response))
    ).toEqual({
      ...testState,
      feature: {
        ...testState.feature,
        description: response.description,
      },
    });
  });
});
