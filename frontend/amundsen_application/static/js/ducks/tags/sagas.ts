import { SagaIterator } from 'redux-saga';
import { all, call, put, takeEvery } from 'redux-saga/effects';

import {
  updateTagsFailure,
  updateTagsSuccess,
  getAllTagsFailure,
  getAllTagsSuccess,
} from './reducer';

import * as API from './api/v0';

import { GetAllTags, UpdateTags, UpdateTagsRequest } from './types';

export function* getAllTagsWorker(): SagaIterator {
  try {
    const allTags = yield call(API.getAllTags);
    yield put(getAllTagsSuccess(allTags));
  } catch (e) {
    yield put(getAllTagsFailure());
  }
}
export function* getAllTagsWatcher(): SagaIterator {
  yield takeEvery(GetAllTags.REQUEST, getAllTagsWorker);
}

export function* updateResourceTagsWorker(
  action: UpdateTagsRequest
): SagaIterator {
  try {
    const { tagArray, resourceType, uriKey } = action.payload;
    yield all(
      tagArray.map((tagObject) =>
        call(API.updateResourceTag, tagObject, resourceType, uriKey)
      )
    );
    const newTags = yield call(API.getResourceTags, resourceType, uriKey);
    yield put(updateTagsSuccess(newTags));
  } catch (e) {
    yield put(updateTagsFailure());
  }
}
export function* updateResourceTagsWatcher(): SagaIterator {
  yield takeEvery(UpdateTags.REQUEST, updateResourceTagsWorker);
}
