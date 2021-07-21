import { DEFAULT_RESOURCE_TYPE, ResourceType } from 'interfaces';

import * as SearchUtils from 'ducks/search/utils';

import globalState from 'fixtures/globalState';

const searchState = globalState.search;

describe('search utils', () => {
  describe('getSearchState', () => {
    it('returns the search state', () => {
      const result = SearchUtils.getSearchState(globalState);
      expect(result).toEqual(searchState);
    });
  });

  describe('getPageIndex', () => {
    const mockState = {
      ...searchState,
      resource: ResourceType.dashboard,
      dashboards: {
        ...searchState.dashboards,
        page_index: 1,
      },
      tables: {
        ...searchState.tables,
        page_index: 2,
      },
      users: {
        ...searchState.users,
        page_index: 3,
      },
    };

    it('given ResourceType.dashboard, returns page_index for dashboards', () => {
      expect(
        SearchUtils.getPageIndex(mockState, ResourceType.dashboard)
      ).toEqual(mockState.dashboards.page_index);
    });

    it('given ResourceType.table, returns page_index for table', () => {
      expect(SearchUtils.getPageIndex(mockState, ResourceType.table)).toEqual(
        mockState.tables.page_index
      );
    });

    it('given ResourceType.user, returns page_index for users', () => {
      expect(SearchUtils.getPageIndex(mockState, ResourceType.user)).toEqual(
        mockState.users.page_index
      );
    });

    it('given no resource, returns page_index for the selected resource', () => {
      const resourceToUse = mockState[mockState.resource + 's'];
      expect(SearchUtils.getPageIndex(mockState)).toEqual(
        resourceToUse.page_index
      );
    });

    it('returns 0 if not given a supported ResourceType', () => {
      // @ts-ignore: cover default case
      expect(SearchUtils.getPageIndex(mockState, 'not valid input')).toEqual(0);
    });
  });

  describe('autoSelectResource', () => {
    const emptyMockState = {
      ...searchState,
      dashboards: {
        ...searchState.dashboards,
        total_results: 0,
      },
      tables: {
        ...searchState.tables,
        total_results: 0,
      },
      users: {
        ...searchState.users,
        total_results: 0,
      },
    };

    it('returns the DEFAULT_RESOURCE_TYPE when search results are empty', () => {
      expect(SearchUtils.autoSelectResource(emptyMockState)).toEqual(
        DEFAULT_RESOURCE_TYPE
      );
    });

    it('prefers `table` over `user` and `dashboard`', () => {
      const mockState = { ...emptyMockState };
      mockState.tables.total_results = 10;
      mockState.users.total_results = 10;
      mockState.dashboards.total_results = 10;
      expect(SearchUtils.autoSelectResource(mockState)).toEqual(
        ResourceType.table
      );
    });

    it('prefers `user` over `dashboard`', () => {
      const mockState = { ...emptyMockState };
      mockState.tables.total_results = 0;
      mockState.users.total_results = 10;
      mockState.dashboards.total_results = 10;
      expect(SearchUtils.autoSelectResource(mockState)).toEqual(
        ResourceType.user
      );
    });

    it('returns `dashboard` if there are dashboards but no other results', () => {
      const mockState = { ...emptyMockState };
      mockState.tables.total_results = 0;
      mockState.users.total_results = 0;
      mockState.dashboards.total_results = 10;
      expect(SearchUtils.autoSelectResource(mockState)).toEqual(
        ResourceType.dashboard
      );
    });
  });
});
