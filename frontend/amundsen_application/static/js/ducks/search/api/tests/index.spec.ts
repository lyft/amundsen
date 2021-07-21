import axios, { AxiosResponse } from 'axios';

import globalState from 'fixtures/globalState';

import { ResourceType, SearchType } from 'interfaces';

import * as ConfigUtils from 'config/config-utils';
import * as API from '../v0';

jest.mock('axios');

describe('searchResource', () => {
  let axiosMockGet;
  let axiosMockPost;
  let dashboardEnabledMock;
  let userEnabledMock;
  let mockSearchResponse: AxiosResponse<API.SearchAPI>;
  beforeAll(() => {
    mockSearchResponse = {
      data: {
        msg: 'Success',
        status_code: 200,
        search_term: globalState.search.search_term,
        tables: globalState.search.tables,
        users: globalState.search.users,
      },
      status: 200,
      statusText: '',
      headers: {},
      config: {},
    };
    axiosMockGet = jest
      .spyOn(axios, 'get')
      .mockImplementation(() => Promise.resolve(mockSearchResponse));
    axiosMockPost = jest
      .spyOn(axios, 'post')
      .mockImplementation(() => Promise.resolve(mockSearchResponse));
    userEnabledMock = jest
      .spyOn(ConfigUtils, 'indexUsersEnabled')
      .mockImplementation(() => true);
    dashboardEnabledMock = jest.spyOn(ConfigUtils, 'indexDashboardsEnabled');
  });

  describe('searchResource', () => {
    it('resolves with empty object if dashboard resource search not supported', async () => {
      axiosMockGet.mockClear();
      axiosMockPost.mockClear();
      const pageIndex = 0;
      const resourceType = ResourceType.dashboard;
      const term = 'test';
      expect.assertions(3);
      await API.searchResource(
        pageIndex,
        resourceType,
        term,
        undefined,
        SearchType.FILTER
      ).then((results) => {
        expect(results).toEqual({});
      });
      expect(axiosMockGet).not.toHaveBeenCalled();
      expect(axiosMockPost).not.toHaveBeenCalled();
    });

    it('resolves with empty object if user resource search not supported', async () => {
      axiosMockGet.mockClear();
      axiosMockPost.mockClear();
      userEnabledMock.mockImplementationOnce(() => false);
      const pageIndex = 0;
      const resourceType = ResourceType.user;
      const term = 'test';
      expect.assertions(3);
      await API.searchResource(
        pageIndex,
        resourceType,
        term,
        undefined,
        SearchType.FILTER
      ).then((results) => {
        expect(results).toEqual({});
      });
      expect(axiosMockGet).not.toHaveBeenCalled();
      expect(axiosMockPost).not.toHaveBeenCalled();
    });

    describe('if searching a user resource', () => {
      it('calls axios get with request for a resource', async () => {
        axiosMockGet.mockClear();
        axiosMockPost.mockClear();
        userEnabledMock.mockImplementationOnce(() => true);
        const pageIndex = 0;
        const resourceType = ResourceType.user;
        const term = 'test';
        const searchType = SearchType.SUBMIT_TERM;
        await API.searchResource(
          pageIndex,
          resourceType,
          term,
          undefined,
          searchType
        );
        expect(axiosMockGet).toHaveBeenCalledWith(
          `${API.BASE_URL}/${resourceType}?query=${term}&page_index=${pageIndex}&search_type=${searchType}`
        );
        expect(axiosMockPost).not.toHaveBeenCalled();
      });

      it('calls searchResourceHelper with api call response', async () => {
        const searchResourceHelperSpy = jest.spyOn(API, 'searchResourceHelper');
        await API.searchResource(
          0,
          ResourceType.user,
          'test',
          undefined,
          SearchType.FILTER
        );
        expect(searchResourceHelperSpy).toHaveBeenCalledWith(
          mockSearchResponse
        );
      });
    });

    describe('if not searching a user resource', () => {
      it('calls axios post with request for a table resource', async () => {
        axiosMockGet.mockClear();
        axiosMockPost.mockClear();
        const pageIndex = 0;
        const resourceType = ResourceType.table;
        const term = 'test';
        const filters = { schema: 'schema_name' };
        const searchType = SearchType.SUBMIT_TERM;
        await API.searchResource(
          pageIndex,
          resourceType,
          term,
          filters,
          searchType
        );
        expect(axiosMockGet).not.toHaveBeenCalled();
        expect(axiosMockPost).toHaveBeenCalledWith(
          `${API.BASE_URL}/${resourceType}`,
          {
            filters,
            pageIndex,
            term,
            searchType,
          }
        );
      });

      it('calls axios post with request for a dashboard resource', async () => {
        axiosMockGet.mockClear();
        axiosMockPost.mockClear();
        dashboardEnabledMock.mockImplementationOnce(() => true);
        const pageIndex = 0;
        const resourceType = ResourceType.dashboard;
        const term = 'test';
        const filters = { name: 'test' };
        const searchType = SearchType.SUBMIT_TERM;
        await API.searchResource(
          pageIndex,
          resourceType,
          term,
          filters,
          searchType
        );
        expect(axiosMockGet).not.toHaveBeenCalled();
        expect(axiosMockPost).toHaveBeenCalledWith(
          `${API.BASE_URL}/${resourceType}`,
          {
            filters,
            pageIndex,
            term,
            searchType,
          }
        );
      });

      it('calls searchResourceHelper with api call response', async () => {
        const searchResourceHelperSpy = jest.spyOn(API, 'searchResourceHelper');
        await API.searchResource(
          0,
          ResourceType.table,
          'test',
          { schema: 'schema_name' },
          SearchType.FILTER
        );
        expect(searchResourceHelperSpy).toHaveBeenCalledWith(
          mockSearchResponse
        );
      });
    });
  });

  describe('searchResourceHelper', () => {
    it('returns expected object', () => {
      expect(API.searchResourceHelper(mockSearchResponse)).toEqual({
        searchTerm: mockSearchResponse.data.search_term,
        tables: mockSearchResponse.data.tables,
        users: mockSearchResponse.data.users,
      });
    });
  });
});
