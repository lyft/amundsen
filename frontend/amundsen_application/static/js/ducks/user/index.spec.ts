import { testSaga } from 'redux-saga-test-plan';

import { LoggedInUser, PeopleUser, Resource, ResourceDict } from 'interfaces';

import globalState from 'fixtures/globalState';

import * as API from './api/v0';
import reducer, {
  getLoggedInUser,
  getLoggedInUserFailure,
  getLoggedInUserSuccess,
  getUser,
  getUserFailure,
  getUserSuccess,
  getUserOwn,
  getUserOwnFailure,
  getUserOwnSuccess,
  getUserRead,
  getUserReadFailure,
  getUserReadSuccess,
  defaultUser,
  initialState,
  initialOwnState,
  UserReducerState,
} from './reducer';
import {
  getLoggedInUserWorker,
  getLoggedInUserWatcher,
  getUserWorker,
  getUserWatcher,
  getUserOwnWorker,
  getUserOwnWatcher,
  getUserReadWorker,
  getUserReadWatcher,
} from './sagas';
import { GetLoggedInUser, GetUser, GetUserOwn, GetUserRead } from './types';

describe('user ducks', () => {
  let currentUser: LoggedInUser;
  let otherUser: {
    own: ResourceDict<Resource[]>;
    read: Resource[];
    user: PeopleUser;
  };
  let userId: string;
  let source: string;
  let index: string;
  beforeAll(() => {
    currentUser = globalState.user.loggedInUser;
    otherUser = globalState.user.profile;
    userId = 'testId';
    source = 'test';
    index = '0';
  });

  describe('actions', () => {
    it('getLoggedInUser - returns the action to get the data for the current user', () => {
      const action = getLoggedInUser();
      expect(action.type).toBe(GetLoggedInUser.REQUEST);
    });

    it('getLoggedInUserSuccess - returns the action to process the success', () => {
      const action = getLoggedInUserSuccess(currentUser);
      const { payload } = action;
      expect(action.type).toBe(GetLoggedInUser.SUCCESS);
      expect(payload?.user).toBe(currentUser);
    });

    it('getLoggedInUserFailure - returns the action to process the failure', () => {
      const action = getLoggedInUserFailure();
      expect(action.type).toBe(GetLoggedInUser.FAILURE);
    });

    it('getUser - returns the action to get the data for a user given an id', () => {
      const action = getUser(userId);
      const { payload } = action;
      expect(action.type).toBe(GetUser.REQUEST);
      expect(payload.userId).toBe(userId);
    });

    it('getUserSuccess - returns the action to process the success', () => {
      const action = getUserSuccess(otherUser.user);
      const { payload } = action;
      expect(action.type).toBe(GetUser.SUCCESS);
      expect(payload?.user).toBe(otherUser.user);
    });

    it('getUserFailure - returns the action to process the failure', () => {
      const action = getUserFailure();
      expect(action.type).toBe(GetUser.FAILURE);
    });

    it('getUserOwn - returns the action to get the owned resources for a user given an id', () => {
      const action = getUserOwn(userId);
      const { payload } = action;
      expect(action.type).toBe(GetUserOwn.REQUEST);
      expect(payload.userId).toBe(userId);
    });

    it('getUserOwnSuccess - returns the action to process the success', () => {
      const action = getUserOwnSuccess(otherUser.own);
      const { payload } = action;
      expect(action.type).toBe(GetUserOwn.SUCCESS);
      expect(payload?.own).toBe(otherUser.own);
    });

    it('getUserOwnFailure - returns the action to process the failure', () => {
      const action = getUserOwnFailure();
      expect(action.type).toBe(GetUserOwn.FAILURE);
    });

    it('getUserRead - returns the action to get the frequently used resources for a user given an id', () => {
      const action = getUserRead(userId);
      const { payload } = action;
      expect(action.type).toBe(GetUserRead.REQUEST);
      expect(payload.userId).toBe(userId);
    });

    it('getUserReadSuccess - returns the action to process the success', () => {
      const action = getUserReadSuccess(otherUser.read);
      const { payload } = action;
      expect(action.type).toBe(GetUserRead.SUCCESS);
      expect(payload?.read).toBe(otherUser.read);
    });

    it('getUserReadFailure - returns the action to process the failure', () => {
      const action = getUserReadFailure();
      expect(action.type).toBe(GetUserRead.FAILURE);
    });
  });

  describe('reducer', () => {
    let testState: UserReducerState;
    beforeAll(() => {
      testState = initialState;
    });
    it('should return the existing state if action is not handled', () => {
      expect(reducer(testState, { type: 'INVALID.ACTION' })).toEqual(testState);
    });

    it('should handle GetLoggedInUser.SUCCESS', () => {
      expect(reducer(testState, getLoggedInUserSuccess(currentUser))).toEqual({
        ...testState,
        loggedInUser: currentUser,
      });
    });

    it('should handle GetUser.REQUEST', () => {
      expect(reducer(testState, getUser(userId))).toEqual({
        ...testState,
        profile: {
          ...testState.profile,
          user: defaultUser,
        },
      });
    });

    it('should handle GetUser.FAILURE', () => {
      expect(reducer(testState, getUserFailure())).toEqual({
        ...testState,
        profile: {
          ...testState.profile,
          user: defaultUser,
        },
      });
    });

    it('should handle GetUser.SUCCESS', () => {
      expect(reducer(testState, getUserSuccess(otherUser.user))).toEqual({
        ...testState,
        profile: {
          ...testState.profile,
          user: otherUser.user,
        },
      });
    });

    it('should handle GetUserOwn.REQUEST', () => {
      expect(reducer(testState, getUserOwn(userId))).toEqual({
        ...testState,
        profile: {
          ...testState.profile,
          own: initialOwnState,
        },
      });
    });

    it('should handle GetUserOwn.FAILURE', () => {
      expect(reducer(testState, getUserOwnFailure())).toEqual({
        ...testState,
        profile: {
          ...testState.profile,
          own: initialOwnState,
        },
      });
    });

    it('should handle GetUserOwn.SUCCESS', () => {
      expect(reducer(testState, getUserOwnSuccess(otherUser.own))).toEqual({
        ...testState,
        profile: {
          ...testState.profile,
          own: otherUser.own,
        },
      });
    });

    it('should handle GetUserRead.REQUEST', () => {
      expect(reducer(testState, getUserRead(userId))).toEqual({
        ...testState,
        profile: {
          ...testState.profile,
          read: [],
        },
      });
    });

    it('should handle GetUserRead.FAILURE', () => {
      expect(reducer(testState, getUserReadFailure())).toEqual({
        ...testState,
        profile: {
          ...testState.profile,
          read: [],
        },
      });
    });

    it('should handle GetUserRead.SUCCESS', () => {
      expect(reducer(testState, getUserReadSuccess(otherUser.read))).toEqual({
        ...testState,
        profile: {
          ...testState.profile,
          read: otherUser.read,
        },
      });
    });
  });

  describe('sagas', () => {
    describe('getLoggedInUserWatcher', () => {
      it('takes every GetLoggedInUser.REQUEST with getLoggedInUserWorker', () => {
        testSaga(getLoggedInUserWatcher)
          .next()
          .takeEvery(GetLoggedInUser.REQUEST, getLoggedInUserWorker);
      });
    });

    describe('getLoggedInUserWorker', () => {
      it('executes flow for returning the currentUser', () => {
        testSaga(getLoggedInUserWorker)
          .next()
          .call(API.getLoggedInUser)
          .next(currentUser)
          .put(getLoggedInUserSuccess(currentUser))
          .next()
          .isDone();
      });

      it('handles request error', () => {
        testSaga(getLoggedInUserWorker)
          .next()
          .throw(new Error())
          .put(getLoggedInUserFailure())
          .next()
          .isDone();
      });
    });

    describe('getUserWatcher', () => {
      it('takes every GetUser.REQUEST with getUserWorker', () => {
        testSaga(getUserWatcher)
          .next()
          .takeEvery(GetUser.REQUEST, getUserWorker);
      });
    });

    describe('getUserWorker', () => {
      it('executes flow for returning a user given an id', () => {
        testSaga(getUserWorker, getUser(userId, index, source))
          .next()
          .call(API.getUser, userId, index, source)
          .next(otherUser.user)
          .put(getUserSuccess(otherUser.user))
          .next()
          .isDone();
      });

      it('handles request error', () => {
        testSaga(getUserWorker, getUser(userId))
          .next()
          .throw(new Error())
          .put(getUserFailure())
          .next()
          .isDone();
      });
    });

    describe('getUserOwnWatcher', () => {
      it('takes every GetUserOwn.REQUEST with getUserOwnWorker', () => {
        testSaga(getUserOwnWatcher)
          .next()
          .takeEvery(GetUserOwn.REQUEST, getUserOwnWorker);
      });
    });

    describe('getUserOwnWorker', () => {
      it('executes flow for returning a users owned resources given an id', () => {
        testSaga(getUserOwnWorker, getUserOwn(userId))
          .next()
          .call(API.getUserOwn, userId)
          .next(otherUser)
          .put(getUserOwnSuccess(otherUser.own))
          .next()
          .isDone();
      });

      it('handles request error', () => {
        testSaga(getUserOwnWorker, getUserOwn(userId))
          .next()
          .throw(new Error())
          .put(getUserOwnFailure())
          .next()
          .isDone();
      });
    });

    describe('getUserReadWatcher', () => {
      it('takes every GetUserRead.REQUEST with getUserReadWorker', () => {
        testSaga(getUserReadWatcher)
          .next()
          .takeEvery(GetUserRead.REQUEST, getUserReadWorker);
      });
    });

    describe('getUserReadWorker', () => {
      it('executes flow for returning a users frequently used resources given an id', () => {
        testSaga(getUserReadWorker, getUserRead(userId))
          .next()
          .call(API.getUserRead, userId)
          .next(otherUser)
          .put(getUserReadSuccess(otherUser.read))
          .next()
          .isDone();
      });

      it('handles request error', () => {
        testSaga(getUserReadWorker, getUserRead(userId))
          .next()
          .throw(new Error())
          .put(getUserReadFailure())
          .next()
          .isDone();
      });
    });
  });
});
