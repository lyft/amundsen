import { testSaga } from 'redux-saga-test-plan';

import { ResourceType, SearchType } from 'interfaces';

import * as NavigationUtils from 'utils/navigationUtils';
import * as SearchUtils from 'ducks/search/utils';

import globalState from 'fixtures/globalState';
import * as API from '../api/v0';
import * as Sagas from '../sagas';

import {
  searchAll,
  searchAllFailure,
  searchResource,
  searchResourceFailure,
  searchResourceSuccess,
  submitSearch,
  submitSearchResource,
  updateSearchState,
  urlDidUpdate,
} from '../reducer';
import {
  LoadPreviousSearch,
  InlineSearch,
  SearchAll,
  SearchResource,
  SearchResponsePayload,
  SubmitSearch,
  SubmitSearchResource,
  UpdateSearchState,
  UrlDidUpdate,
} from '../types';

const updateSearchUrlSpy = jest.spyOn(NavigationUtils, 'updateSearchUrl');
const searchState = globalState.search;

describe('search sagas', () => {
  const expectedSearchResults: SearchResponsePayload = {
    search_term: 'testName',
    tables: {
      page_index: 0,
      results: [
        {
          cluster: 'testCluster',
          database: 'testDatabase',
          description: 'I have a lot of users',
          key: 'testDatabase://testCluster.testSchema/testName',
          last_updated_timestamp: 946684799,
          name: 'testName',
          schema: 'testSchema',
          type: ResourceType.table,
        },
      ],
      total_results: 1,
    },
  };

  describe('searchAllWatcher', () => {
    it('takes every SearchAll.REQUEST with searchAllWorker', () => {
      testSaga(Sagas.searchAllWatcher)
        .next()
        .takeEvery(SearchAll.REQUEST, Sagas.searchAllWorker)
        .next()
        .isDone();
    });
  });

  describe('searchAllWorker', () => {
    /*
      TODO - There seems to be no straughtforward way to test this method.
      We should re-evaluate how much logic is wrapped into sagas specifically
      question:
      1. Processing the response in the saga
      2. Helper methods
      Can we pass all necessary information to the api method such that the api method
      does all of the processing and returns what we need?
    */

    it('handles request error', () => {
      testSaga(
        Sagas.searchAllWorker,
        searchAll(SearchType.SUBMIT_TERM, 'test', ResourceType.table, 0, true)
      )
        .next()
        .select(SearchUtils.getSearchState)
        .next(globalState.search)
        .throw(new Error())
        .put(searchAllFailure())
        .next()
        .isDone();
    });
  });

  describe('searchResourceWatcher', () => {
    it('takes every SearchResource.REQUEST with searchResourceWorker', () => {
      testSaga(Sagas.searchResourceWatcher)
        .next()
        .takeEvery(SearchResource.REQUEST, Sagas.searchResourceWorker)
        .next()
        .isDone();
    });
  });

  describe('searchResourceWorker', () => {
    it('executes flow for returning search results', () => {
      const pageIndex = 0;
      const resource = ResourceType.table;
      const term = 'test';
      const mockSearchState = globalState.search;
      const searchType = SearchType.PAGINATION;
      testSaga(
        Sagas.searchResourceWorker,
        searchResource(searchType, term, resource, pageIndex)
      )
        .next()
        .select(SearchUtils.getSearchState)
        .next(mockSearchState)
        .call(
          API.searchResource,
          pageIndex,
          resource,
          term,
          mockSearchState.filters[resource],
          searchType
        )
        .next(expectedSearchResults)
        .put(searchResourceSuccess(expectedSearchResults))
        .next()
        .isDone();
    });

    it('handles request error', () => {
      testSaga(
        Sagas.searchResourceWorker,
        searchResource(SearchType.PAGINATION, 'test', ResourceType.table, 0)
      )
        .next()
        .select(SearchUtils.getSearchState)
        .next(globalState.search)
        .throw(new Error())
        .put(searchResourceFailure())
        .next()
        .isDone();
    });
  });

  describe('submitSearchWorker', () => {
    it('initiates flow to search with a term and optional filters', () => {
      const term = 'test';
      testSaga(
        Sagas.submitSearchWorker,
        submitSearch({ searchTerm: term, useFilters: true })
      )
        .next()
        .put(
          searchAll(SearchType.SUBMIT_TERM, term, ResourceType.table, 0, true)
        )
        .next()
        .isDone();
    });

    it('initiates flow to search with empty term and existing filters', () => {
      testSaga(
        Sagas.submitSearchWorker,
        submitSearch({ searchTerm: '', useFilters: false })
      )
        .next()
        .put(searchAll(SearchType.CLEAR_TERM, '', ResourceType.table, 0, false))
        .next()
        .isDone();
    });
  });

  describe('submitSearchWatcher', () => {
    it('takes latest SubmitSearch.REQUEST with submitSearchWorker', () => {
      testSaga(Sagas.submitSearchWatcher)
        .next()
        .takeLatest(SubmitSearch.REQUEST, Sagas.submitSearchWorker)
        .next()
        .isDone();
    });
  });

  describe('submitSearchResourceWorker', () => {
    describe('when no new search state input is passed', () => {
      it('it updates url if necessary + calls searchResource with given pageIndex and existing search input', () => {
        updateSearchUrlSpy.mockClear();
        const paginationAction = submitSearchResource({
          pageIndex: 1,
          searchType: SearchType.PAGINATION,
          updateUrl: true,
        });
        const { search_term, resource } = searchState;
        testSaga(Sagas.submitSearchResourceWorker, paginationAction)
          .next()
          .select(SearchUtils.getSearchState)
          .next(searchState)
          .put(searchResource(SearchType.PAGINATION, search_term, resource, 1))
          .next()
          .isDone();

        expect(updateSearchUrlSpy).toHaveBeenCalledWith({
          term: searchState.search_term,
          resource: searchState.resource,
          index: 1,
          filters: searchState.filters,
        });
      });
    });

    it('calls searchResource with given term', () => {
      const filterAction = submitSearchResource({
        pageIndex: 0,
        searchTerm: '',
        searchType: SearchType.FILTER,
        resourceFilters: { database: { hive: true } },
      });
      const { resource } = searchState;
      testSaga(Sagas.submitSearchResourceWorker, filterAction)
        .next()
        .select(SearchUtils.getSearchState)
        .next(searchState)
        .put(searchResource(SearchType.FILTER, '', resource, 0))
        .next()
        .isDone();
    });

    it('calls searchResource with given resource', () => {
      const filterAction = submitSearchResource({
        pageIndex: 0,
        searchTerm: 'hello',
        searchType: SearchType.FILTER,
        resourceFilters: { database: { hive: true } },
        resource: ResourceType.table,
      });

      testSaga(Sagas.submitSearchResourceWorker, filterAction)
        .next()
        .select(SearchUtils.getSearchState)
        .next(searchState)
        .put(searchResource(SearchType.FILTER, 'hello', ResourceType.table, 0))
        .next()
        .isDone();
    });
  });

  describe('submitSearchResourceWatcher', () => {
    it('takes every SubmitSearchResource.REQUEST with submitSearchResourceWorker', () => {
      testSaga(Sagas.submitSearchResourceWatcher)
        .next()
        .takeEvery(
          SubmitSearchResource.REQUEST,
          Sagas.submitSearchResourceWorker
        )
        .next()
        .isDone();
    });
  });

  describe('updateSearchStateWorker', () => {
    it('it update url if necessary with existing state values', () => {
      updateSearchUrlSpy.mockClear();
      const action = updateSearchState({ updateUrl: true });

      testSaga(Sagas.updateSearchStateWorker, action)
        .next()
        .select(SearchUtils.getSearchState)
        .next(searchState)
        .isDone();

      expect(updateSearchUrlSpy).toHaveBeenCalledWith({
        term: searchState.search_term,
        resource: searchState.resource,
        index: 0,
        filters: searchState.filters,
      });
    });

    it('it updates filters and executes search', () => {
      const action = updateSearchState({
        filters: { [ResourceType.table]: { database: { bigquery: true } } },
        submitSearch: true,
      });

      testSaga(Sagas.updateSearchStateWorker, action)
        .next()
        .select(SearchUtils.getSearchState)
        .next(searchState)
        .put(searchAll(SearchType.FILTER, '', ResourceType.table, 0, true))
        .next()
        .isDone();
    });
  });

  describe('updateSearchStateWatcher', () => {
    it('takes every UpdateSearchState.REQUEST with updateSearchStateWorker', () => {
      testSaga(Sagas.updateSearchStateWatcher)
        .next()
        .takeEvery(UpdateSearchState.REQUEST, Sagas.updateSearchStateWorker)
        .next()
        .isDone();
    });
  });

  describe('urlDidUpdateWorker', () => {
    let sagaTest;
    let term;
    let resource;
    let index;

    beforeEach(() => {
      term = searchState.search_term;
      resource = searchState.resource;
      index = SearchUtils.getPageIndex(searchState, resource);

      sagaTest = (action) =>
        testSaga(Sagas.urlDidUpdateWorker, action)
          .next()
          .select(SearchUtils.getSearchState)
          .next(searchState);
    });

    it('calls searchAll when search term changes', () => {
      term = 'new search';
      sagaTest(urlDidUpdate(`term=${term}&resource=${resource}&index=${index}`))
        .put(searchAll(SearchType.LOAD_URL, term, resource, index, false))
        .next()
        .isDone();
    });

    it('calls updateSearchState & searchAll when filter & search term changes', () => {
      term = 'new search';
      sagaTest(
        urlDidUpdate(
          `term=${term}&resource=${resource}&index=${index}&filters=%7B"database"%3A%7B"hive"%3Atrue%7D%7D`
        )
      )
        .put(
          updateSearchState({
            // @ts-ignore: Has trouble with resource = 'table' vs explicityly being ResourceType.table
            filters: {
              [resource]: { database: { hive: true } },
            },
          })
        )
        .next()
        .put(searchAll(SearchType.LOAD_URL, term, resource, index, true))
        .next()
        .isDone();
    });

    it('calls updateSearchState when the resource has changed', () => {
      resource = ResourceType.user;
      sagaTest(urlDidUpdate(`term=${term}&resource=${resource}&index=${index}`))
        .put(updateSearchState({ resource }))
        .next()
        .isDone();
    });

    it('calls submitSearchResource when the filters changes', () => {
      sagaTest(
        urlDidUpdate(
          `term=${term}&resource=${resource}&index=${index}&filters=%7B"database"%3A%7B"bigquery"%3Atrue%7D%7D`
        )
      )
        .put(
          submitSearchResource({
            resource,
            searchTerm: term,
            resourceFilters: { database: { bigquery: true } },
            pageIndex: index,
            searchType: SearchType.LOAD_URL,
          })
        )
        .next()
        .isDone();
    });

    it('calls submitSearchResource when the index changes', () => {
      index = 10;
      sagaTest(urlDidUpdate(`term=${term}&resource=${resource}&index=${index}`))
        .put(
          submitSearchResource({
            pageIndex: index,
            searchType: SearchType.LOAD_URL,
          })
        )
        .next()
        .isDone();
    });
  });

  describe('urlDidUpdateWatcher', () => {
    it('takes every UrlDidUpdate.REQUEST with urlDidUpdateWorker', () => {
      testSaga(Sagas.urlDidUpdateWatcher)
        .next()
        .takeEvery(UrlDidUpdate.REQUEST, Sagas.urlDidUpdateWorker)
        .next()
        .isDone();
    });
  });

  describe('loadPreviousSearchWorker', () => {
    // TODO - test 'BrowserHistory.goBack' case

    it('applies the existing search state into the URL', () => {
      updateSearchUrlSpy.mockClear();

      testSaga(Sagas.loadPreviousSearchWorker)
        .next()
        .select(SearchUtils.getSearchState)
        .next(searchState)
        .isDone();

      expect(updateSearchUrlSpy).toHaveBeenCalledWith({
        term: searchState.search_term,
        resource: searchState.resource,
        index: SearchUtils.getPageIndex(searchState, searchState.resource),
        filters: searchState.filters,
      });
    });
  });

  describe('loadPreviousSearchWatcher', () => {
    it('takes every LoadPreviousSearch.REQUEST with loadPreviousSearchWorker', () => {
      testSaga(Sagas.loadPreviousSearchWatcher)
        .next()
        .takeEvery(LoadPreviousSearch.REQUEST, Sagas.loadPreviousSearchWorker)
        .next()
        .isDone();
    });
  });

  describe('inlineSearchWorker', () => {
    /* TODO - Considering some cleanup */
  });

  describe('inlineSearchWatcher', () => {
    /* TODO - Need to investigate proper test approach
    it('debounces InlineSearch.REQUEST and calls inlineSearchWorker', () => {
    });
    */
  });

  describe('selectInlineResultWorker', () => {
    /* TODO - Considering some cleanup */
  });

  describe('selectInlineResultsWatcher', () => {
    it('takes every InlineSearch.REQUEST with selectInlineResultWorker', () => {
      testSaga(Sagas.selectInlineResultsWatcher)
        .next()
        .takeEvery(InlineSearch.SELECT, Sagas.selectInlineResultWorker)
        .next()
        .isDone();
    });
  });
});
