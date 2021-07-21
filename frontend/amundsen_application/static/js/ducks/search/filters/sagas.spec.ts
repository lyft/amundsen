import { testSaga } from 'redux-saga-test-plan';
import { takeEvery } from 'redux-saga/effects';

import { submitSearchResource } from 'ducks/search/reducer';
import * as SearchUtils from 'ducks/search/utils';

import globalState from 'fixtures/globalState';
import { datasetFilterExample } from 'fixtures/search/filters';

import { SearchType } from 'interfaces';

import { updateFilterByCategory, UpdateSearchFilter } from './reducer';
import * as Sagas from './sagas';

describe('filter sagas', () => {
  describe('filterWatcher', () => {
    it('debounces update filter actions with filterWorker', () => {
      testSaga(Sagas.filterWatcher)
        .next()
        .is(takeEvery(UpdateSearchFilter.REQUEST, Sagas.filterWorker))
        .next()
        .isDone();
    });
  });

  describe('filterWorker', () => {
    let mockSearchStateWithFilters;
    beforeAll(() => {
      mockSearchStateWithFilters = {
        ...globalState.search,
        filters: datasetFilterExample,
      };
    });

    /* TODO: Library has issue rectifying {} vs [Object] */
    /* it('puts expected actions for clearing a filter', () => {
      testSaga(Sagas.filterWorker, updateFilterByCategory({ categoryId: 'database', value: undefined }))
        .next().select(SearchUtils.getSearchState).next(mockSearchStateWithFilters)
        .put(submitSearchResource({
          resource: mockSearchStateWithFilters.resource,
          resourceFilters: {},
          searchTerm: mockSearchStateWithFilters.search_term,
          pageIndex: 0,
          searchType: SearchType.FILTER,
          updateUrl: true,
        }))
        .next().isDone();
    }); */

    it('puts expected actions for updating a filter', () => {
      const testCategoryId = 'database';
      const testValue = { hive: true };
      testSaga(
        Sagas.filterWorker,
        updateFilterByCategory({ categoryId: testCategoryId, value: testValue })
      )
        .next()
        .select(SearchUtils.getSearchState)
        .next(globalState.search)
        .put(
          submitSearchResource({
            resource: mockSearchStateWithFilters.resource,
            resourceFilters: { [testCategoryId]: testValue },
            searchTerm: mockSearchStateWithFilters.search_term,
            pageIndex: 0,
            searchType: SearchType.FILTER,
            updateUrl: true,
          })
        )
        .next()
        .isDone();
    });
  });
});
