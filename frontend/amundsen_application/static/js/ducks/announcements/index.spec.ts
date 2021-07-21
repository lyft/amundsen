import { testSaga } from 'redux-saga-test-plan';

import * as API from './api/v0';
import reducer, {
  getAnnouncements,
  getAnnouncementsFailure,
  getAnnouncementsSuccess,
  initialState,
  AnnouncementsReducerState,
} from '.';
import { getAnnouncementsWatcher, getAnnouncementsWorker } from './sagas';
import { GetAnnouncements } from './types';

const SERVER_ERROR_CODE = 500;

describe('Announcements ducks', () => {
  describe('actions', () => {
    it('getAnnouncements - returns the action to get all tags', () => {
      const action = getAnnouncements();
      expect(action.type).toBe(GetAnnouncements.REQUEST);
    });

    it('getAnnouncementsFailure - returns the action to process failure', () => {
      const expectedPayload = {
        statusCode: SERVER_ERROR_CODE,
        posts: [],
      };
      const action = getAnnouncementsFailure(expectedPayload);
      const { payload } = action;

      expect(action.type).toBe(GetAnnouncements.FAILURE);
      expect(payload.posts).toEqual([]);
      expect(payload.statusCode).toEqual(SERVER_ERROR_CODE);
    });

    it('getAllTagsSuccess - returns the action to process success', () => {
      const expectedPosts = [
        {
          date: '12/31/1999',
          title: 'Test',
          html_content: '<div>Test content</div>',
        },
      ];
      const expectedPayload = {
        posts: expectedPosts,
        statusCode: 200,
      };

      const action = getAnnouncementsSuccess(expectedPayload);
      const { payload } = action;

      expect(action.type).toBe(GetAnnouncements.SUCCESS);
      expect(payload.posts).toBe(expectedPosts);
    });
  });

  describe('reducer', () => {
    let testState: AnnouncementsReducerState;

    beforeAll(() => {
      testState = {
        isLoading: false,
        statusCode: 200,
        posts: [],
      };
    });

    describe('when action is not handled', () => {
      it('should return the existing state', () => {
        const expected = testState;
        const actual = reducer(testState, { type: 'INVALID.ACTION' });

        expect(actual).toEqual(expected);
      });
    });

    describe('when action is REQUEST', () => {
      it('should handle GetAnnouncements.REQUEST', () => {
        const expected = {
          ...testState,
          isLoading: true,
          statusCode: null,
        };
        const actual = reducer(testState, getAnnouncements());

        expect(actual).toEqual(expected);
      });
    });

    describe('when action is SUCCESS', () => {
      it('should handle GetAnnouncements.SUCCESS', () => {
        const expectedPosts = [
          {
            date: '12/31/1999',
            title: 'Test',
            html_content: '<div>Test content</div>',
          },
        ];
        const payload = {
          posts: expectedPosts,
          statusCode: 200,
        };
        const expected = {
          isLoading: false,
          statusCode: 200,
          posts: expectedPosts,
        };
        const actual = reducer(testState, getAnnouncementsSuccess(payload));

        expect(actual).toEqual(expected);
      });
    });

    describe('when action is FAILURE', () => {
      it('should return the initialState with the status code', () => {
        const expected = {
          ...initialState,
          isLoading: false,
          statusCode: SERVER_ERROR_CODE,
        };
        const actual = reducer(
          testState,
          getAnnouncementsFailure({ statusCode: SERVER_ERROR_CODE })
        );

        expect(actual).toEqual(expected);
      });
    });
  });

  describe('sagas', () => {
    describe('getAnnouncementsWatcher', () => {
      it('takes GetAnnouncements.REQUEST with getAnnouncementsWorker', () => {
        testSaga(getAnnouncementsWatcher)
          .next()
          .takeEvery(GetAnnouncements.REQUEST, getAnnouncementsWorker)
          .next()
          .isDone();
      });
    });

    describe('getAnnouncementsWorker', () => {
      it('executes flow for successfuly getting announcements', () => {
        const mockResponse = {
          posts: [
            {
              date: '12/31/1999',
              title: 'Test',
              html_content: '<div>Test content</div>',
            },
          ],
          statusCode: 200,
        };

        testSaga(getAnnouncementsWorker)
          .next()
          .call(API.getAnnouncements)
          .next(mockResponse)
          .put(getAnnouncementsSuccess(mockResponse))
          .next()
          .isDone();
      });

      it('executes flow for a failed request', () => {
        const mockResponse = {
          statusCode: SERVER_ERROR_CODE,
          statusMessage: 'Error',
        };

        testSaga(getAnnouncementsWorker)
          .next()
          .call(API.getAnnouncements)
          // @ts-ignore
          .throw(mockResponse)
          .put(getAnnouncementsFailure(mockResponse))
          .next()
          .isDone();
      });
    });
  });
});
