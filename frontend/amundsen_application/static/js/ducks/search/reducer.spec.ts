import { ResourceType, SearchType } from 'interfaces';

import * as NavigationUtils from 'utils/navigationUtils';

import globalState from 'fixtures/globalState';

import * as filterReducer from './filters/reducer';

import reducer, {
  getInlineResults,
  getInlineResultsDebounce,
  getInlineResultsSuccess,
  getInlineResultsFailure,
  initialState,
  initialInlineResultsState,
  loadPreviousSearch,
  resetSearchState,
  searchAll,
  searchAllFailure,
  searchAllSuccess,
  SearchReducerState,
  searchResource,
  searchResourceFailure,
  searchResourceSuccess,
  selectInlineResult,
  submitSearch,
  submitSearchResource,
  updateFromInlineResult,
  updateSearchState,
  urlDidUpdate,
} from './reducer';
import {
  LoadPreviousSearch,
  InlineSearch,
  InlineSearchResponsePayload,
  InlineSearchUpdatePayload,
  SearchAll,
  SearchAllResponsePayload,
  SearchResource,
  SearchResponsePayload,
  SubmitSearch,
  UrlDidUpdate,
} from './types';

const MOCK_TABLE_FILTER_STATE = { database: { hive: true } };
const MOCK_FILTER_STATE = {
  [ResourceType.table]: MOCK_TABLE_FILTER_STATE,
};
const filterReducerSpy = jest
  .spyOn(filterReducer, 'default')
  .mockImplementation(() => MOCK_FILTER_STATE);

jest.spyOn(NavigationUtils, 'updateSearchUrl');
const searchState = globalState.search;

describe('search reducer', () => {
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
  const expectedSearchAllResults: SearchAllResponsePayload = {
    search_term: 'testName',
    resource: ResourceType.table,
    dashboards: {
      page_index: 0,
      results: [],
      total_results: 0,
    },
    features: {
      page_index: 0,
      results: [],
      total_results: 0,
    },
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
    users: {
      page_index: 0,
      results: [],
      total_results: 0,
    },
  };

  const expectedInlineResults: InlineSearchResponsePayload = {
    dashboards: {
      page_index: 0,
      results: [],
      total_results: 0,
    },
    features: {
      page_index: 0,
      results: [],
      total_results: 0,
    },
    tables: {
      page_index: 0,
      results: [],
      total_results: 0,
    },
    users: {
      page_index: 0,
      results: [],
      total_results: 0,
    },
  };

  const inlineUpdatePayload: InlineSearchUpdatePayload = {
    searchTerm: 'testName',
    resource: ResourceType.table,
    dashboards: {
      page_index: 0,
      results: [],
      total_results: 0,
    },
    features: {
      page_index: 0,
      results: [],
      total_results: 0,
    },
    tables: {
      page_index: 0,
      results: [],
      total_results: 0,
    },
    users: {
      page_index: 0,
      results: [],
      total_results: 0,
    },
  };

  describe('actions', () => {
    it('searchAll - returns the action to search all resources without useFilters', () => {
      const term = 'test';
      const resource = ResourceType.table;
      const pageIndex = 0;
      const searchType = SearchType.SUBMIT_TERM;
      const action = searchAll(searchType, term, resource, pageIndex);
      const { payload } = action;
      expect(action.type).toBe(SearchAll.REQUEST);
      expect(payload.resource).toBe(resource);
      expect(payload.term).toBe(term);
      expect(payload.pageIndex).toBe(pageIndex);
      expect(payload.useFilters).toBe(false);
      expect(payload.searchType).toBe(searchType);
    });

    it('searchAll - returns the action to search all resources with useFilters', () => {
      const term = 'test';
      const resource = ResourceType.table;
      const pageIndex = 0;
      const searchType = SearchType.SUBMIT_TERM;
      const action = searchAll(searchType, term, resource, pageIndex, true);
      const { payload } = action;
      expect(action.type).toBe(SearchAll.REQUEST);
      expect(payload.resource).toBe(resource);
      expect(payload.term).toBe(term);
      expect(payload.pageIndex).toBe(pageIndex);
      expect(payload.useFilters).toBe(true);
      expect(payload.searchType).toBe(searchType);
    });

    it('searchAllSuccess - returns the action to process the success', () => {
      const action = searchAllSuccess(expectedSearchAllResults);
      const { payload } = action;
      expect(action.type).toBe(SearchAll.SUCCESS);
      expect(payload).toBe(expectedSearchAllResults);
    });

    it('searchAllFailure - returns the action to process the failure', () => {
      const action = searchAllFailure();
      expect(action.type).toBe(SearchAll.FAILURE);
    });

    it('searchResource - returns the action to search all resources', () => {
      const term = 'test';
      const resource = ResourceType.table;
      const pageIndex = 0;
      const searchType = SearchType.SUBMIT_TERM;
      const action = searchResource(searchType, term, resource, pageIndex);
      const { payload } = action;
      expect(action.type).toBe(SearchResource.REQUEST);
      expect(payload.resource).toBe(resource);
      expect(payload.term).toBe(term);
      expect(payload.pageIndex).toBe(pageIndex);
      expect(payload.searchType).toBe(searchType);
    });

    it('searchResourceSuccess - returns the action to process the success', () => {
      const action = searchResourceSuccess(expectedSearchResults);
      const { payload } = action;
      expect(action.type).toBe(SearchResource.SUCCESS);
      expect(payload).toBe(expectedSearchResults);
    });

    it('searchResourceFailure - returns the action to process the failure', () => {
      const action = searchResourceFailure();
      expect(action.type).toBe(SearchResource.FAILURE);
    });

    it('submitSearch - returns the action to submit a search', () => {
      const term = 'test';
      const shouldUseFilters = true;
      const action = submitSearch({
        searchTerm: term,
        useFilters: shouldUseFilters,
      });
      expect(action.type).toBe(SubmitSearch.REQUEST);
      expect(action.payload.searchTerm).toBe(term);
      expect(action.payload.useFilters).toBe(shouldUseFilters);
    });

    it('loadPreviousSearch - returns the action to load the previous search', () => {
      const action = loadPreviousSearch();
      expect(action.type).toBe(LoadPreviousSearch.REQUEST);
    });

    it('urlDidUpdate - returns the action to run when the search page URL changes', () => {
      const urlSearch = 'test url search';
      const action = urlDidUpdate(urlSearch);
      expect(action.type).toBe(UrlDidUpdate.REQUEST);
      expect(action.payload.urlSearch).toBe(urlSearch);
    });

    it('getInlineResultsSuccess - returns the action to get inline results', () => {
      const term = 'test';
      const action = getInlineResults(term);
      expect(action.type).toBe(InlineSearch.REQUEST);
      expect(action.payload.term).toBe(term);
    });

    it('getInlineResultsSuccess - returns the action to process the success', () => {
      const action = getInlineResultsSuccess(expectedInlineResults);
      const { payload } = action;
      expect(action.type).toBe(InlineSearch.SUCCESS);
      expect(payload).toBe(expectedInlineResults);
    });

    it('getInlineResultsFailure - returns the action to process the failure', () => {
      const action = getInlineResultsFailure();
      expect(action.type).toBe(InlineSearch.FAILURE);
    });

    it('selectInlineResult - returns the action to process the selection of an inline result', () => {
      const resource = ResourceType.table;
      const searchTerm = 'test;';
      const updateUrl = true;
      const action = selectInlineResult(resource, searchTerm, updateUrl);
      const { payload } = action;
      expect(action.type).toBe(InlineSearch.SELECT);
      expect(payload.resourceType).toBe(resource);
      expect(payload.searchTerm).toBe(searchTerm);
      expect(payload.updateUrl).toBe(updateUrl);
    });

    it('updateFromInlineResult - returns the action to populate the search results with existing inlineResults', () => {
      const action = updateFromInlineResult(inlineUpdatePayload);
      expect(action.type).toBe(InlineSearch.UPDATE);
      expect(action.payload).toBe(inlineUpdatePayload);
    });
  });

  describe('reducer', () => {
    let testState: SearchReducerState;
    let result;
    beforeAll(() => {
      testState = {
        ...searchState,
        filters: MOCK_FILTER_STATE,
        resource: ResourceType.user,
      };
    });
    it('should return the existing state if action is not handled', () => {
      expect(reducer(testState, { type: 'INVALID.ACTION' })).toEqual(testState);
    });

    it('should handle SearchAll.REQUEST', () => {
      const term = 'testSearch';
      expect(
        reducer(
          testState,
          searchAll(SearchType.SUBMIT_TERM, term, ResourceType.table, 0)
        )
      ).toEqual({
        ...testState,
        inlineResults: initialInlineResultsState,
        search_term: term,
        isLoading: true,
      });
    });

    it('should handle SearchAll.SUCCESS', () => {
      expect(
        reducer(testState, searchAllSuccess(expectedSearchAllResults))
      ).toEqual({
        ...initialState,
        ...expectedSearchAllResults,
        filters: testState.filters,
        inlineResults: {
          dashboards: expectedSearchAllResults.dashboards,
          features: expectedSearchAllResults.features,
          tables: expectedSearchAllResults.tables,
          users: expectedSearchAllResults.users,
          isLoading: false,
        },
      });
    });

    it('should handle SearchAll.FAILURE', () => {
      expect(reducer(testState, searchAllFailure())).toEqual({
        ...initialState,
        search_term: testState.search_term,
      });
    });

    it('should handle SearchResource.REQUEST', () => {
      expect(
        reducer(
          testState,
          searchResource(SearchType.SUBMIT_TERM, 'test', ResourceType.table, 0)
        )
      ).toEqual({
        ...testState,
        isLoading: true,
      });
    });

    it('should handle SearchResource.SUCCESS', () => {
      expect(
        reducer(testState, searchResourceSuccess(expectedSearchResults))
      ).toEqual({
        ...testState,
        ...expectedSearchResults,
        isLoading: false,
      });
    });

    it('should handle SearchResource.FAILURE', () => {
      expect(reducer(testState, searchResourceFailure())).toEqual({
        ...initialState,
        search_term: testState.search_term,
      });
    });

    it('should handle InlineSearch.UPDATE', () => {
      const {
        searchTerm,
        resource,
        dashboards,
        features,
        tables,
        users,
      } = inlineUpdatePayload;
      expect(
        reducer(testState, updateFromInlineResult(inlineUpdatePayload))
      ).toEqual({
        ...testState,
        resource,
        dashboards,
        features,
        tables,
        users,
        search_term: searchTerm,
        filters: filterReducer.initialFilterState,
      });
    });

    describe('InlineSearch', () => {
      it('should handle InlineSearch.SUCCESS', () => {
        const { dashboards, features, tables, users } = expectedInlineResults;
        expect(
          reducer(testState, getInlineResultsSuccess(expectedInlineResults))
        ).toEqual({
          ...testState,
          inlineResults: {
            dashboards,
            features,
            tables,
            users,
            isLoading: false,
          },
        });
      });

      it('should handle InlineSearch.FAILURE', () => {
        expect(reducer(testState, getInlineResultsFailure())).toEqual({
          ...testState,
          inlineResults: initialInlineResultsState,
        });
      });

      it('should handle InlineSearch.REQUEST', () => {
        const term = 'testSearch';
        expect(reducer(testState, getInlineResults(term))).toEqual({
          ...testState,
          inlineResults: {
            dashboards: initialInlineResultsState.dashboards,
            features: initialInlineResultsState.features,
            tables: initialInlineResultsState.tables,
            users: initialInlineResultsState.users,
            isLoading: true,
          },
        });
      });

      it('should handle InlineSearch.REQUEST_DEBOUNCE', () => {
        const term = 'testSearch';
        expect(reducer(testState, getInlineResultsDebounce(term))).toEqual({
          ...testState,
          inlineResults: {
            dashboards: initialInlineResultsState.dashboards,
            features: initialInlineResultsState.features,
            tables: initialInlineResultsState.tables,
            users: initialInlineResultsState.users,
            isLoading: true,
          },
        });
      });
    });

    describe('UpdateSearchState', () => {
      it('UpdateSearchState.REQUEST returns existing filter state if not provided', () => {
        result = reducer(testState, updateSearchState({ updateUrl: true }));
        expect(result.filters).toBe(testState.filters);
      });

      it('UpdateSearchState.REQUEST returns existing resource state if not provided', () => {
        result = reducer(testState, updateSearchState({ updateUrl: true }));
        expect(result.resource).toBe(testState.resource);
      });

      it('UpdateSearchState.REQUEST updates filter state if provided', () => {
        result = reducer(
          initialState,
          updateSearchState({ filters: MOCK_FILTER_STATE })
        );
        expect(result.filters).toBe(MOCK_FILTER_STATE);
      });

      it('UpdateSearchState.REQUEST updates resource state if provided', () => {
        const testResource = ResourceType.user;
        result = reducer(
          initialState,
          updateSearchState({ resource: testResource })
        );
        expect(result.resource).toEqual(testResource);
      });

      it('UpdateSearchState.RESET returns initialState', () => {
        result = reducer(testState, resetSearchState());
        expect(result).toBe(initialState);
      });
    });

    it('SubmitSearch.REQUEST updates given search term and enters isLoading state', () => {
      const searchTerm = 'testTerm';
      result = reducer(
        testState,
        submitSearch({ searchTerm, useFilters: true })
      );
      expect(result).toEqual({
        ...testState,
        isLoading: true,
        search_term: searchTerm,
      });
    });

    describe('should handle SubmitSearchResource.REQUEST', () => {
      let filterAction;
      let paginationAction;
      beforeAll(() => {
        filterAction = submitSearchResource({
          pageIndex: 0,
          searchTerm: 'hello',
          searchType: SearchType.FILTER,
          resourceFilters: MOCK_TABLE_FILTER_STATE,
        });
        paginationAction = submitSearchResource({
          pageIndex: 1,
          searchType: SearchType.PAGINATION,
        });
      });

      it('calls filter reducer with existing filters', () => {
        filterReducerSpy.mockClear();
        reducer(initialState, filterAction);

        expect(filterReducerSpy).toHaveBeenCalledWith(
          initialState.filters,
          filterAction
        );
      });

      it('updates search term if provided', () => {
        result = reducer(testState, filterAction);
        expect(result.search_term).toBe(filterAction.payload.searchTerm);
      });

      it('sets search term with existing state if provided', () => {
        result = reducer(testState, paginationAction);
        expect(result.search_term).toBe(testState.search_term);
      });
    });
  });
});
