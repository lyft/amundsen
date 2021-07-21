import { SagaIterator } from 'redux-saga';
import { takeEvery, put, select } from 'redux-saga/effects';

import { SearchType } from 'interfaces';

import { submitSearchResource } from 'ducks/search/reducer';
import { getSearchState } from 'ducks/search/utils';
import { filterFromObj } from 'ducks/utilMethods';

import { UpdateSearchFilter, UpdateFilterRequest } from './reducer';

/*
 * Generates new filter shape from action payload.
 * Then executes a search on current resource based with new filters and current search state values.
 */
export function* filterWorker(action: UpdateFilterRequest): SagaIterator {
  const { categoryId, value } = action.payload;
  const state = yield select(getSearchState);
  const { search_term, resource, filters } = state;
  let resourceFilters = {
    ...filters[resource],
  };

  if (value === undefined) {
    resourceFilters = filterFromObj(resourceFilters, [categoryId]);
  } else {
    resourceFilters[categoryId] = value;
  }

  yield put(
    submitSearchResource({
      resource,
      resourceFilters,
      searchTerm: search_term,
      pageIndex: 0,
      searchType: SearchType.FILTER,
      updateUrl: true,
    })
  );
}

/**
 * Listens to actions triggers by user updates to the filter state..
 */
export function* filterWatcher(): SagaIterator {
  /*
    TODO: If we want to minimize api calls on checkbox quick-select,
    we will have to debounce and accumulate filter updates elsewhere.
    To be revisited when we have more checkbox filters
  */
  yield takeEvery(UpdateSearchFilter.REQUEST, filterWorker);
}
