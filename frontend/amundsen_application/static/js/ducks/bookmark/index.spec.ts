// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import { expectSaga, testSaga } from 'redux-saga-test-plan';
import * as matchers from 'redux-saga-test-plan/matchers';
import { throwError } from 'redux-saga-test-plan/providers';

import { Bookmark, ResourceType, ResourceDict } from 'interfaces';

import * as API from './api/v0';
import reducer, {
  addBookmark,
  addBookmarkFailure,
  addBookmarkSuccess,
  getBookmarks,
  getBookmarksFailure,
  getBookmarksSuccess,
  getBookmarksForUser,
  getBookmarksForUserFailure,
  getBookmarksForUserSuccess,
  removeBookmark,
  removeBookmarkFailure,
  removeBookmarkSuccess,
  initialState,
  initialBookmarkState,
  BookmarkReducerState,
} from './reducer';
import {
  addBookmarkWatcher,
  addBookmarkWorker,
  getBookmarksWatcher,
  getBookmarksWorker,
  getBookmarksForUserWatcher,
  getBookmarkForUserWorker,
  removeBookmarkWatcher,
  removeBookmarkWorker,
} from './sagas';
import {
  AddBookmark,
  AddBookmarkRequest,
  GetBookmarks,
  GetBookmarksForUser,
  GetBookmarksForUserRequest,
  RemoveBookmark,
  RemoveBookmarkRequest,
} from './types';

describe('bookmark ducks', () => {
  let bookmarks: ResourceDict<Bookmark[]>;
  let testResourceKey: string;
  let testResourceType: ResourceType;
  let testUserId: string;
  beforeAll(() => {
    testResourceKey = 'key';
    testResourceType = ResourceType.table;
    testUserId = 'userId';
    bookmarks = {
      [testResourceType]: [
        {
          key: testResourceKey,
          type: testResourceType,
          cluster: 'cluster',
          database: 'database',
          description: 'description',
          name: 'name',
          schema: 'schema',
        },
      ],
    };
  });

  describe('actions', () => {
    it('addBookmark - returns the action to add a bookmark', () => {
      const action = addBookmark(testResourceKey, testResourceType);
      const { payload } = action;
      expect(action.type).toBe(AddBookmark.REQUEST);
      expect(payload.resourceKey).toBe(testResourceKey);
      expect(payload.resourceType).toBe(testResourceType);
    });

    it('addBookmarkFailure - returns the action to process failure', () => {
      const action = addBookmarkFailure();
      expect(action.type).toBe(AddBookmark.FAILURE);
    });

    it('addBookmarkSuccess - returns the action to process success', () => {
      const action = addBookmarkSuccess(bookmarks);
      const { payload } = action;
      expect(action.type).toBe(AddBookmark.SUCCESS);
      expect(payload?.bookmarks).toBe(bookmarks);
    });

    it('getBookmarks - returns the action to get bookmarks', () => {
      const action = getBookmarks();
      expect(action.type).toBe(GetBookmarks.REQUEST);
    });

    it('getBookmarksFailure - returns the action to process failure', () => {
      const action = getBookmarksFailure();
      const { payload } = action;
      expect(action.type).toBe(GetBookmarks.FAILURE);
    });

    it('getBookmarksSuccess - returns the action to process success', () => {
      const action = getBookmarksSuccess(bookmarks);
      const { payload } = action;
      expect(action.type).toBe(GetBookmarks.SUCCESS);
      expect(payload?.bookmarks).toBe(bookmarks);
    });

    it('getBookmarksForUser - returns the action to get bookmarks for a user', () => {
      const action = getBookmarksForUser(testUserId);
      const { payload } = action;
      expect(action.type).toBe(GetBookmarksForUser.REQUEST);
      expect(payload.userId).toBe(testUserId);
    });

    it('getBookmarksForUserFailure - returns the action to process failure', () => {
      const action = getBookmarksForUserFailure();
      const { payload } = action;
      expect(action.type).toBe(GetBookmarksForUser.FAILURE);
    });

    it('getBookmarksForUserSuccess - returns the action to process success', () => {
      const action = getBookmarksForUserSuccess(bookmarks);
      const { payload } = action;
      expect(action.type).toBe(GetBookmarksForUser.SUCCESS);
      expect(payload?.bookmarks).toBe(bookmarks);
    });

    it('removeBookmark - returns the action to remove a bookmark', () => {
      const action = removeBookmark(testResourceKey, testResourceType);
      const { payload } = action;
      expect(action.type).toBe(RemoveBookmark.REQUEST);
      expect(payload.resourceKey).toBe(testResourceKey);
      expect(payload.resourceType).toBe(testResourceType);
    });

    it('removeBookmarkFailure - returns the action to process failure', () => {
      const action = removeBookmarkFailure();
      expect(action.type).toBe(RemoveBookmark.FAILURE);
    });

    it('removeBookmarkSuccess - returns the action to process success', () => {
      const action = removeBookmarkSuccess(testResourceKey, testResourceType);
      const { payload } = action;
      expect(action.type).toBe(RemoveBookmark.SUCCESS);
      expect(payload?.resourceKey).toBe(testResourceKey);
      expect(payload?.resourceType).toBe(testResourceType);
    });
  });

  describe('reducer', () => {
    let testState: BookmarkReducerState;
    let bookmarkList: ResourceDict<Bookmark[]>;
    beforeEach(() => {
      bookmarkList = {
        [ResourceType.table]: [
          {
            key: 'bookmarked_key_0',
            type: ResourceType.table,
            cluster: 'cluster',
            database: 'database',
            description: 'description',
            name: 'name',
            schema: 'schema',
          },
          {
            key: 'bookmarked_key_1',
            type: ResourceType.table,
            cluster: 'cluster',
            database: 'database',
            description: 'description',
            name: 'name',
            schema: 'schema',
          },
        ],
      };
      testState = {
        myBookmarks: bookmarkList,
        myBookmarksIsLoaded: false,
        bookmarksForUser: bookmarkList,
      };
    });
    it('should return the existing state if action is not handled', () => {
      expect(reducer(testState, { type: 'INVALID.ACTION' })).toEqual(testState);
      expect(reducer(testState, addBookmarkFailure())).toEqual(testState);
      expect(reducer(testState, getBookmarksFailure())).toEqual(testState);
      expect(reducer(testState, getBookmarksForUserFailure())).toEqual(
        testState
      );
      expect(reducer(testState, removeBookmarkFailure())).toEqual(testState);
    });

    it('should handle RemoveBookmark.SUCCESS', () => {
      const bookmarkKey = 'bookmarked_key_1';
      const action = {
        type: RemoveBookmark.SUCCESS,
        payload: { resourceType: ResourceType.table, resourceKey: bookmarkKey },
      };
      const newState = reducer(testState, action);
      expect(
        newState.myBookmarks[ResourceType.table].find(
          (bookmark) => bookmark.key === bookmarkKey
        )
      ).toEqual(undefined);
      expect(newState).toEqual({
        ...testState,
        myBookmarks: {
          [ResourceType.table]: [
            {
              key: 'bookmarked_key_0',
              type: ResourceType.table,
              cluster: 'cluster',
              database: 'database',
              description: 'description',
              name: 'name',
              schema: 'schema',
            },
          ],
        },
      });
    });

    it('should handle AddBookmark.SUCCESS', () => {
      expect(reducer(initialState, addBookmarkSuccess(bookmarks))).toEqual({
        ...initialState,
        myBookmarks: bookmarks,
        myBookmarksIsLoaded: true,
      });
    });

    it('should handle GetBookmarks.SUCCESS', () => {
      expect(reducer(initialState, getBookmarksSuccess(bookmarks))).toEqual({
        ...initialState,
        myBookmarks: bookmarks,
        myBookmarksIsLoaded: true,
      });
    });

    it('should handle GetBookmarksForUser.SUCCESS', () => {
      expect(
        reducer(initialState, getBookmarksForUserSuccess(bookmarks))
      ).toEqual({
        ...initialState,
        bookmarksForUser: bookmarks,
      });
    });

    it('should reset bookmarksForUser on GetBookmarksForUser.REQUEST', () => {
      expect(
        reducer(testState, {
          type: GetBookmarksForUser.REQUEST,
          payload: { userId: 'testUser' },
        })
      ).toEqual({
        ...testState,
        bookmarksForUser: initialBookmarkState,
      });
    });
  });

  describe('sagas', () => {
    describe('addBookmarkWatcher', () => {
      it('takes AddBookmark.REQUEST with addBookmarkWorker', () => {
        testSaga(addBookmarkWatcher)
          .next()
          .takeEvery(AddBookmark.REQUEST, addBookmarkWorker)
          .next()
          .isDone();
      });
    });

    describe('addBookmarkWorker', () => {
      let action: AddBookmarkRequest;
      beforeAll(() => {
        action = addBookmark(testResourceKey, testResourceType);
      });

      it('adds a bookmark', () =>
        expectSaga(addBookmarkWorker, action)
          .provide([
            [matchers.call.fn(API.addBookmark), {}],
            [matchers.call.fn(API.getBookmarks), { bookmarks }],
          ])
          .put(addBookmarkSuccess(bookmarks))
          .run());

      it('handles request error', () =>
        expectSaga(addBookmarkWorker, action)
          .provide([
            [matchers.call.fn(API.addBookmark), throwError(new Error())],
            [matchers.call.fn(API.getBookmarks), throwError(new Error())],
          ])
          .put(addBookmarkFailure())
          .run());
    });

    describe('getBookmarksWatcher', () => {
      it('takes GetBookmark.REQUEST with getBookmarksWorker', () => {
        testSaga(getBookmarksWatcher)
          .next()
          .takeEvery(GetBookmarks.REQUEST, getBookmarksWorker)
          .next()
          .isDone();
      });
    });

    describe('getBookmarksWorker', () => {
      it('gets bookmarks', () =>
        expectSaga(getBookmarksWorker)
          .provide([[matchers.call.fn(API.getBookmarks), { bookmarks }]])
          .put(getBookmarksSuccess(bookmarks))
          .run());

      it('handles request error', () =>
        expectSaga(getBookmarksWorker)
          .provide([
            [matchers.call.fn(API.getBookmarks), throwError(new Error())],
          ])
          .put(getBookmarksFailure())
          .run());
    });

    describe('getBookmarksForUserWatcher', () => {
      it('takes GetBookmarksForUser.REQUEST with getBookmarkForUserWorker', () => {
        testSaga(getBookmarksForUserWatcher)
          .next()
          .takeEvery(GetBookmarksForUser.REQUEST, getBookmarkForUserWorker)
          .next()
          .isDone();
      });
    });

    describe('getBookmarkForUserWorker', () => {
      let action: GetBookmarksForUserRequest;
      beforeAll(() => {
        action = getBookmarksForUser(testUserId);
      });

      it('gets bookmarks', () =>
        expectSaga(getBookmarkForUserWorker, action)
          .provide([[matchers.call.fn(API.getBookmarks), { bookmarks }]])
          .put(getBookmarksForUserSuccess(bookmarks))
          .run());

      it('handles request error', () =>
        expectSaga(getBookmarkForUserWorker, action)
          .provide([
            [matchers.call.fn(API.getBookmarks), throwError(new Error())],
          ])
          .put(getBookmarksForUserFailure())
          .run());
    });

    describe('removeBookmarkWatcher', () => {
      it('takes RemoveBookmark.REQUEST with removeBookmarkWorker', () => {
        testSaga(removeBookmarkWatcher)
          .next()
          .takeEvery(RemoveBookmark.REQUEST, removeBookmarkWorker)
          .next()
          .isDone();
      });
    });

    describe('removeBookmarkWorker', () => {
      let action: RemoveBookmarkRequest;
      beforeAll(() => {
        action = removeBookmark(testResourceKey, testResourceType);
      });

      it('removes a bookmark', () =>
        expectSaga(removeBookmarkWorker, action)
          .provide([[matchers.call.fn(API.removeBookmark), {}]])
          .put(removeBookmarkSuccess(testResourceKey, testResourceType))
          .run());

      it('handles request error', () =>
        expectSaga(removeBookmarkWorker, action)
          .provide([
            [matchers.call.fn(API.removeBookmark), throwError(new Error())],
          ])
          .put(removeBookmarkFailure())
          .run());
    });
  });
});
