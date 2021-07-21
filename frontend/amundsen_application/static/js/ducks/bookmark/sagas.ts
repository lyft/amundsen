import { SagaIterator } from 'redux-saga';
import { call, put, takeEvery } from 'redux-saga/effects';

import * as API from './api/v0';

import {
  addBookmarkFailure,
  addBookmarkSuccess,
  getBookmarksFailure,
  getBookmarksSuccess,
  getBookmarksForUserFailure,
  getBookmarksForUserSuccess,
  removeBookmarkFailure,
  removeBookmarkSuccess,
} from './reducer';

import {
  AddBookmark,
  AddBookmarkRequest,
  GetBookmarks,
  GetBookmarksRequest,
  GetBookmarksForUser,
  GetBookmarksForUserRequest,
  RemoveBookmark,
  RemoveBookmarkRequest,
} from './types';

export function* addBookmarkWorker(action: AddBookmarkRequest): SagaIterator {
  let response;
  const { resourceKey, resourceType } = action.payload;

  try {
    yield call(API.addBookmark, resourceKey, resourceType);

    // TODO - Consider adding the newly bookmarked resource directly to local store. This would save a round trip.
    response = yield call(API.getBookmarks);
    yield put(addBookmarkSuccess(response.bookmarks));
  } catch (e) {
    yield put(addBookmarkFailure());
  }
}
export function* addBookmarkWatcher(): SagaIterator {
  yield takeEvery(AddBookmark.REQUEST, addBookmarkWorker);
}

export function* removeBookmarkWorker(
  action: RemoveBookmarkRequest
): SagaIterator {
  let response;
  const { resourceKey, resourceType } = action.payload;
  try {
    response = yield call(API.removeBookmark, resourceKey, resourceType);
    yield put(removeBookmarkSuccess(resourceKey, resourceType));
  } catch (e) {
    yield put(removeBookmarkFailure());
  }
}
export function* removeBookmarkWatcher(): SagaIterator {
  yield takeEvery(RemoveBookmark.REQUEST, removeBookmarkWorker);
}

export function* getBookmarksWorker(): SagaIterator {
  let response;
  try {
    response = yield call(API.getBookmarks);
    yield put(getBookmarksSuccess(response.bookmarks));
  } catch (e) {
    yield put(getBookmarksFailure());
  }
}
export function* getBookmarksWatcher(): SagaIterator {
  yield takeEvery(GetBookmarks.REQUEST, getBookmarksWorker);
}

export function* getBookmarkForUserWorker(
  action: GetBookmarksForUserRequest
): SagaIterator {
  let response;
  const { userId } = action.payload;
  try {
    response = yield call(API.getBookmarks, userId);
    yield put(getBookmarksForUserSuccess(response.bookmarks));
  } catch (e) {
    yield put(getBookmarksForUserFailure());
  }
}
export function* getBookmarksForUserWatcher(): SagaIterator {
  yield takeEvery(GetBookmarksForUser.REQUEST, getBookmarkForUserWorker);
}
