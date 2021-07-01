import axios from 'axios';
import { SagaIterator } from 'redux-saga';
import { all, call, put, select, takeEvery } from 'redux-saga/effects';

import { ResourceType } from 'interfaces/Resources';
import { createOwnerUpdatePayload } from 'utils/ownerUtils';
import { getFeatureLineage } from 'ducks/lineage/api/v0';
import { GetFeatureLineage } from 'ducks/lineage/types';
import * as API from './api/v0';
import {
  getFeatureSuccess,
  getFeatureFailure,
  getFeatureCodeSuccess,
  getFeatureCodeFailure,
  getFeatureLineageSuccess,
  getFeatureLineageFailure,
  getFeatureDescriptionSuccess,
  getFeatureDescriptionFailure,
  updateFeatureOwnerSuccess,
  updateFeatureOwnerFailure,
  getFeaturePreviewDataFailure,
  getFeaturePreviewDataSuccess,
} from './reducer';

import {
  GetFeature,
  GetFeatureCode,
  GetFeatureDescription,
  GetFeatureDescriptionRequest,
  GetFeaturePreviewData,
  UpdateFeatureDescription,
  UpdateFeatureDescriptionRequest,
  UpdateFeatureOwner,
  UpdateFeatureOwnerRequest,
} from './types';

export function* getFeatureWorker(action): SagaIterator {
  try {
    const { key, index, source } = action.payload;
    const response = yield call(API.getFeature, key, index, source);
    yield put(getFeatureSuccess(response));
  } catch (error) {
    yield put(getFeatureFailure(error));
  }
}
export function* getFeatureWatcher(): SagaIterator {
  yield takeEvery(GetFeature.REQUEST, getFeatureWorker);
}

export function* getFeatureCodeWorker(action): SagaIterator {
  try {
    const { key } = action.payload;
    const response = yield call(API.getFeatureCode, key);
    yield put(getFeatureCodeSuccess(response));
  } catch (error) {
    yield put(getFeatureCodeFailure(error));
  }
}
export function* getFeatureCodeWatcher(): SagaIterator {
  yield takeEvery(GetFeatureCode.REQUEST, getFeatureCodeWorker);
}

export function* getFeatureLineageWorker(action): SagaIterator {
  try {
    const { key, depth, direction } = action.payload;
    const response = yield call(getFeatureLineage, key, depth, direction);
    yield put(getFeatureLineageSuccess(response));
  } catch (error) {
    yield put(getFeatureLineageFailure(error));
  }
}
export function* getFeatureLineageWatcher(): SagaIterator {
  yield takeEvery(GetFeatureLineage.REQUEST, getFeatureLineageWorker);
}

export function* getFeaturePreviewDataWorker(action): SagaIterator {
  try {
    const response = yield call(API.getFeaturePreviewData, action.payload);
    yield put(getFeaturePreviewDataSuccess(response));
  } catch (error) {
    yield put(getFeaturePreviewDataFailure(error));
  }
}
export function* getFeaturePreviewDataWatcher(): SagaIterator {
  yield takeEvery(GetFeaturePreviewData.REQUEST, getFeaturePreviewDataWorker);
}

export function* getFeatureDescriptionWorker(
  action: GetFeatureDescriptionRequest
): SagaIterator {
  const { payload } = action;
  const state = yield select();
  const { feature } = state.feature;
  try {
    const response = yield call(API.getFeatureDescription, feature.key);
    yield put(getFeatureDescriptionSuccess(response));
    if (payload.onSuccess) {
      yield call(payload.onSuccess);
    }
  } catch (e) {
    yield put(
      getFeatureDescriptionFailure({
        description: feature.description,
      })
    );
    if (payload.onFailure) {
      yield call(payload.onFailure);
    }
  }
}
export function* getFeatureDescriptionWatcher(): SagaIterator {
  yield takeEvery(GetFeatureDescription.REQUEST, getFeatureDescriptionWorker);
}

export function* updateFeatureDescriptionWorker(
  action: UpdateFeatureDescriptionRequest
): SagaIterator {
  const { payload } = action;
  const state = yield select();
  try {
    yield call(
      API.updateFeatureDescription,
      state.feature.feature.key,
      payload.newValue
    );
    if (payload.onSuccess) {
      yield call(payload.onSuccess);
    }
  } catch (e) {
    if (payload.onFailure) {
      yield call(payload.onFailure);
    }
  }
}
export function* updateFeatureDescriptionWatcher(): SagaIterator {
  yield takeEvery(
    UpdateFeatureDescription.REQUEST,
    updateFeatureDescriptionWorker
  );
}

export function* updateFeatureOwnerWorker(
  action: UpdateFeatureOwnerRequest
): SagaIterator {
  const { payload } = action;
  const state = yield select();
  const { feature } = state.feature;
  try {
    const requestList: any = payload.updateArray.map((updateOwnerPayload) =>
      axios(
        createOwnerUpdatePayload(
          ResourceType.feature,
          feature.key,
          updateOwnerPayload
        )
      )
    );
    yield all(requestList);
    const newOwners = yield call(API.getFeatureOwners, feature.key);
    yield put(updateFeatureOwnerSuccess(newOwners));
    if (payload.onSuccess) {
      yield call(payload.onSuccess);
    }
  } catch (e) {
    yield put(updateFeatureOwnerFailure(state.feature.featureOwners.owners));
    if (payload.onFailure) {
      yield call(payload.onFailure);
    }
  }
}
export function* updateFeatureOwnerWatcher(): SagaIterator {
  yield takeEvery(UpdateFeatureOwner.REQUEST, updateFeatureOwnerWorker);
}
