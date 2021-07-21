import { expectSaga, testSaga } from 'redux-saga-test-plan';
import * as matchers from 'redux-saga-test-plan/matchers';
import { throwError } from 'redux-saga-test-plan/providers';

import { ResourceType, Tag, UpdateMethod, UpdateTagData } from 'interfaces';
import globalState from 'fixtures/globalState';
import {
  getTableData,
  getTableDataFailure,
  getTableDataSuccess,
} from 'ducks/tableMetadata/reducer';
import * as API from '../api/v0';
import reducer, {
  getAllTags,
  getAllTagsFailure,
  getAllTagsSuccess,
  initialState,
  TagsReducerState,
  updateTags,
  updateTagsFailure,
  updateTagsSuccess,
} from '../reducer';

import {
  getAllTagsWatcher,
  getAllTagsWorker,
  updateResourceTagsWatcher,
  updateResourceTagsWorker,
} from '../sagas';
import { GetAllTags, UpdateTags } from '../types';

describe('allTags ducks', () => {
  describe('actions', () => {
    it('getAllTags - returns the action to get all tags', () => {
      const action = getAllTags();
      expect(action.type).toEqual(GetAllTags.REQUEST);
    });

    it('getAllTagsFailure - returns the action to process failure', () => {
      const action = getAllTagsFailure();
      const { payload } = action;
      expect(action.type).toBe(GetAllTags.FAILURE);
      expect(payload.allTags).toEqual([]);
    });

    it('getAllTagsSuccess - returns the action to process success', () => {
      const expectedTags = [
        { tag_count: 2, tag_name: 'test' },
        { tag_count: 1, tag_name: 'test2' },
      ];
      const action = getAllTagsSuccess(expectedTags);
      const { payload } = action;
      expect(action.type).toBe(GetAllTags.SUCCESS);
      expect(payload.allTags).toBe(expectedTags);
    });
  });

  describe('reducer', () => {
    let testState: TagsReducerState;
    beforeAll(() => {
      testState = {
        allTags: {
          isLoading: true,
          tags: [],
        },
        resourceTags: {
          isLoading: false,
          tags: [],
        },
      };
    });
    it('should return the existing state if action is not handled', () => {
      expect(reducer(testState, { type: 'INVALID.ACTION' })).toEqual(testState);
    });

    it('should handle GetAllTags.REQUEST', () => {
      expect(reducer(testState, getAllTags())).toEqual({
        allTags: {
          isLoading: true,
          tags: [],
        },
        resourceTags: {
          isLoading: false,
          tags: [],
        },
      });
    });

    it('should handle GetAllTags.SUCCESS', () => {
      const expectedTags = [
        { tag_count: 2, tag_name: 'test' },
        { tag_count: 1, tag_name: 'test2' },
      ];
      expect(reducer(testState, getAllTagsSuccess(expectedTags))).toEqual({
        allTags: {
          isLoading: false,
          tags: expectedTags,
        },
        resourceTags: {
          isLoading: false,
          tags: [],
        },
      });
    });

    it('should return the initialState if GetAllTags.FAILURE', () => {
      expect(reducer(testState, getAllTagsFailure())).toEqual(initialState);
    });
  });

  describe('sagas', () => {
    describe('getAllTagsWatcher', () => {
      it('takes GetAllTags.REQUEST with getAllTagsWorker', () => {
        testSaga(getAllTagsWatcher)
          .next()
          .takeEvery(GetAllTags.REQUEST, getAllTagsWorker)
          .next()
          .isDone();
      });
    });

    describe('getAllTagsWorker', () => {
      it('gets allTags', () => {
        const mockTags = [
          { tag_count: 2, tag_name: 'test' },
          { tag_count: 1, tag_name: 'test2' },
        ];
        return expectSaga(getAllTagsWorker)
          .provide([[matchers.call.fn(API.getAllTags), mockTags]])
          .put(getAllTagsSuccess(mockTags))
          .run();
      });

      it('handles request error', () =>
        expectSaga(getAllTagsWorker)
          .provide([
            [matchers.call.fn(API.getAllTags), throwError(new Error())],
          ])
          .put(getAllTagsFailure())
          .run());
    });
  });
});

describe('tags ducks', () => {
  let expectedTags: Tag[];
  let updatePayload: UpdateTagData[];
  beforeAll(() => {
    expectedTags = [
      { tag_count: 2, tag_name: 'test' },
      { tag_count: 1, tag_name: 'test2' },
    ];
    updatePayload = [{ methodName: UpdateMethod.PUT, tagName: 'test' }];
  });

  describe('actions', () => {
    it('updateTags - returns the action to updateTags', () => {
      const action = updateTags(updatePayload, ResourceType.table, 'test');
      const { payload } = action;
      expect(action.type).toBe(UpdateTags.REQUEST);
      expect(payload.tagArray).toBe(updatePayload);
    });

    it('updateTagsFailure - returns the action to process failure', () => {
      const action = updateTagsFailure();
      const { payload } = action;
      expect(action.type).toBe(UpdateTags.FAILURE);
      expect(payload.tags).toEqual([]);
    });

    it('updateTagsSuccess - returns the action to process success', () => {
      const action = updateTagsSuccess(expectedTags);
      const { payload } = action;
      expect(action.type).toBe(UpdateTags.SUCCESS);
      expect(payload.tags).toBe(expectedTags);
    });
  });

  describe('reducer', () => {
    let testState: TagsReducerState;
    beforeAll(() => {
      testState = initialState;
    });
    it('should return the existing state if action is not handled', () => {
      expect(reducer(testState, { type: 'INVALID.ACTION' })).toEqual(testState);
    });

    it('should handle UpdateTags.REQUEST', () => {
      expect(
        reducer(
          testState,
          updateTags(updatePayload, ResourceType.table, 'test')
        )
      ).toEqual({
        ...testState,
        resourceTags: {
          ...testState.resourceTags,
          isLoading: true,
        },
      });
    });

    it('should handle UpdateTags.FAILURE', () => {
      expect(reducer(testState, updateTagsFailure())).toEqual({
        ...testState,
        resourceTags: {
          ...testState.resourceTags,
          isLoading: false,
        },
      });
    });

    it('should handle UpdateTags.SUCCESS', () => {
      expect(reducer(testState, updateTagsSuccess(expectedTags))).toEqual({
        ...testState,
        resourceTags: {
          ...testState.resourceTags,
          isLoading: false,
          tags: expectedTags,
        },
      });
    });

    it('should handle GetTableData.REQUEST', () => {
      expect(reducer(testState, getTableData('testKey'))).toEqual({
        ...testState,
        resourceTags: {
          ...testState.resourceTags,
          tags: [],
          isLoading: true,
        },
      });
    });

    it('should handle GetTableData.FAILURE', () => {
      const action = getTableDataFailure();
      expect(reducer(testState, action)).toEqual({
        ...testState,
        resourceTags: {
          ...testState.resourceTags,
          tags: action.payload.tags,
          isLoading: false,
        },
      });
    });

    it('should handle GetTableData.SUCCESS', () => {
      const mockTableData = globalState.tableMetadata.tableData;
      expect(
        reducer(
          testState,
          getTableDataSuccess(mockTableData, {}, 200, expectedTags)
        )
      ).toEqual({
        ...testState,
        resourceTags: {
          ...testState.resourceTags,
          tags: expectedTags,
          isLoading: false,
        },
      });
    });
  });

  describe('sagas', () => {
    describe('updateResourceTagsWatcher', () => {
      it('takes every UpdateTags.REQUEST with updateResourceTagsWorker', () => {
        testSaga(updateResourceTagsWatcher)
          .next()
          .takeEvery(UpdateTags.REQUEST, updateResourceTagsWorker);
      });
    });

    describe('updateResourceTagsWorker', () => {
      /** TODO - fix syntax for testing `all` effect
      it('executes flow for updating tags and returning up to date tag array', () => {
        testSaga(updateResourceTagsWorker, updateTags(updatePayload, ResourceType.table, "test"))
          .next().all(matchers.call.fn(API.updateResourceTag), updatePayload, ResourceType.table, "test"))
          .next().call(API.getResourceTags, ResourceType.table, "test")
          .next(expectedTags).put(updateTagsSuccess(expectedTags))
          .next().isDone();
      });
       */

      it('handles request error', () => {
        testSaga(
          updateResourceTagsWorker,
          updateTags(updatePayload, ResourceType.table, 'test')
        )
          .next(globalState)
          .throw(new Error())
          .put(updateTagsFailure())
          .next()
          .isDone();
      });
    });
  });
});
