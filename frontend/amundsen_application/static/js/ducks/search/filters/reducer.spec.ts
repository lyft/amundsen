import { ResourceType, SearchType } from 'interfaces';

import { submitSearchResource } from 'ducks/search/reducer';

import reducer, {
  updateFilterByCategory,
  initialFilterState,
  FilterReducerState,
  UpdateSearchFilter,
} from './reducer';

describe('filters reducer', () => {
  describe('actions', () => {
    it('updateFilterByCategory - returns the action to update the filters for a given category', () => {
      const testCategory = 'column';
      const testValue = 'column_name';
      const action = updateFilterByCategory({
        categoryId: testCategory,
        value: testValue,
      });
      const { payload } = action;
      expect(action.type).toBe(UpdateSearchFilter.REQUEST);
      expect(payload.categoryId).toBe(testCategory);
      expect(payload.value).toBe(testValue);
    });
  });

  describe('reducer', () => {
    let testState: FilterReducerState;
    beforeAll(() => {
      testState = {
        [ResourceType.table]: {
          column: 'column_name',
        },
      };
    });
    it('should return the existing state if action is not handled', () => {
      expect(reducer(testState, { type: 'INVALID.ACTION' })).toBe(testState);
    });

    describe('handles SubmitSearchResource.REQUEST', () => {
      it('updates the filter state if request contains filter information', () => {
        const givenResource = ResourceType.table;
        const givenFilters = { database: { testDb: true } };
        const result = reducer(
          initialFilterState,
          submitSearchResource({
            resource: givenResource,
            resourceFilters: givenFilters,
            searchTerm: 'test',
            pageIndex: 0,
            searchType: SearchType.FILTER,
            updateUrl: true,
          })
        );
        expect(result[givenResource]).toBe(givenFilters);
      });

      it('does not update the filter state if request does not contains filter information', () => {
        const result = reducer(
          testState,
          submitSearchResource({
            pageIndex: 1,
            searchType: SearchType.PAGINATION,
            updateUrl: true,
          })
        );
        expect(result).toBe(testState);
      });
    });
  });
});
