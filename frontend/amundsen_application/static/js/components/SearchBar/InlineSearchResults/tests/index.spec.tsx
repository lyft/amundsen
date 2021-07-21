// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';

import { mocked } from 'ts-jest/utils';
import { shallow } from 'enzyme';

import { SearchResults } from 'ducks/search/types';
import {
  ResourceType,
  DashboardResource,
  FeatureResource,
  TableResource,
  UserResource,
} from 'interfaces';

import {
  getSourceDisplayName,
  getSourceIconClass,
  indexUsersEnabled,
} from 'config/config-utils';

import globalState from 'fixtures/globalState';
import { allResourcesExample } from 'fixtures/search/inlineResults';
import * as CONSTANTS from '../constants';
import SearchItemList from '../SearchItemList';
import ResultItemList from '../ResultItemList';
import {
  InlineSearchResults,
  InlineSearchResultsProps,
  mapStateToProps,
} from '..';

jest.mock('config/config-utils', () => ({
  getDisplayNameByResource: jest.fn(),
  getSourceDisplayName: jest.fn(),
  getSourceIconClass: jest.fn(),
  indexUsersEnabled: jest.fn(),
  indexDashboardsEnabled: jest.fn(),
  indexFeaturesEnabled: jest.fn(),
}));

describe('InlineSearchResults', () => {
  const setup = (propOverrides?: Partial<InlineSearchResultsProps>) => {
    const props: InlineSearchResultsProps = {
      isLoading: false,
      dashboards: allResourcesExample.dashboards as SearchResults<DashboardResource>,
      features: allResourcesExample.features as SearchResults<FeatureResource>,
      tables: allResourcesExample.tables as SearchResults<TableResource>,
      users: allResourcesExample.users as SearchResults<UserResource>,
      className: 'testClass',
      onItemSelect: jest.fn(),
      searchTerm: 'test search',
      ...propOverrides,
    };
    const wrapper = shallow<InlineSearchResults>(
      // eslint-disable-next-line react/jsx-props-no-spreading
      <InlineSearchResults {...props} />
    );
    return { props, wrapper };
  };

  describe('getTitleForResource', () => {
    let wrapper;
    beforeAll(() => {
      wrapper = setup().wrapper;
    });
    it('returns the correct value for ResourceType.table', () => {
      const output = wrapper.instance().getTitleForResource(ResourceType.table);
      expect(output).toEqual(CONSTANTS.DATASETS);
    });
    it('returns the correct value for ResourceType.user', () => {
      const output = wrapper.instance().getTitleForResource(ResourceType.user);
      expect(output).toEqual(CONSTANTS.PEOPLE);
    });
    it('returns empty string as the default', () => {
      const output = wrapper.instance().getTitleForResource('unsupported');
      expect(output).toEqual('');
    });
  });

  describe('getTotalResultsForResource', () => {
    let props;
    let wrapper;
    beforeAll(() => {
      const setupResult = setup();
      props = setupResult.props;
      wrapper = setupResult.wrapper;
    });
    it('returns the correct value for ResourceType.table', () => {
      const output = wrapper
        .instance()
        .getTotalResultsForResource(ResourceType.table);
      expect(output).toEqual(props.tables.total_results);
    });
    it('returns the correct value for ResourceType.user', () => {
      const output = wrapper
        .instance()
        .getTotalResultsForResource(ResourceType.user);
      expect(output).toEqual(props.users.total_results);
    });
    it('returns 0 as the default', () => {
      const output = wrapper
        .instance()
        .getTotalResultsForResource('unsupported');
      expect(output).toEqual(0);
    });
  });

  describe('getResultsForResource', () => {
    let props;
    let wrapper;
    beforeAll(() => {
      const setupResult = setup();
      props = setupResult.props;
      wrapper = setupResult.wrapper;
    });
    it('returns the correct sliced results for ResourceType.table', () => {
      const output = wrapper
        .instance()
        .getResultsForResource(ResourceType.table);
      expect(output).toEqual(props.tables.results.slice(0, 2));
    });
    it('returns the correct sliced results for ResourceType.user', () => {
      const output = wrapper
        .instance()
        .getResultsForResource(ResourceType.user);
      expect(output).toEqual(props.users.results.slice(0, 2));
    });
    it('returns empty array as the default', () => {
      const output = wrapper.instance().getResultsForResource('unsupported');
      expect(output).toEqual([]);
    });
  });

  describe('getSuggestedResultsForResource', () => {
    let props;
    let wrapper;

    let mockResourceResults;
    let getResultsForResourceSpy;
    let getSuggestedResultHrefSpy;
    let mockHref;
    let getSuggestedResultIconClassSpy;
    let mockClass;
    let getSuggestedResultSubTitleSpy;
    let mockSubtitle;
    let getSuggestedResultTitleSpy;
    let mockTitle;
    let getSuggestedResultTypeSpy;
    let mockType;
    beforeAll(() => {
      const setupResult = setup();
      props = setupResult.props;
      wrapper = setupResult.wrapper;
      mockResourceResults = allResourcesExample.tables.results;
      getResultsForResourceSpy = jest
        .spyOn(wrapper.instance(), 'getResultsForResource')
        .mockImplementation(() => mockResourceResults);
      mockHref = '/test';
      getSuggestedResultHrefSpy = jest
        .spyOn(wrapper.instance(), 'getSuggestedResultHref')
        .mockImplementation(() => mockHref);
      mockClass = 'test-class';
      getSuggestedResultIconClassSpy = jest
        .spyOn(wrapper.instance(), 'getSuggestedResultIconClass')
        .mockImplementation(() => mockClass);
      mockSubtitle = 'subtitle';
      getSuggestedResultSubTitleSpy = jest
        .spyOn(wrapper.instance(), 'getSuggestedResultSubTitle')
        .mockImplementation(() => mockSubtitle);
      mockTitle = 'title';
      getSuggestedResultTitleSpy = jest
        .spyOn(wrapper.instance(), 'getSuggestedResultTitle')
        .mockImplementation(() => mockTitle);
      mockType = 'User';
      getSuggestedResultTypeSpy = jest
        .spyOn(wrapper.instance(), 'getSuggestedResultType')
        .mockImplementation(() => mockType);
      wrapper.instance().forceUpdate();
    });

    it('calls getResultsForResource with given ResourceType', () => {
      getResultsForResourceSpy.mockClear();
      const givenResource = ResourceType.user;
      wrapper.instance().getSuggestedResultsForResource(givenResource);
      expect(getResultsForResourceSpy).toHaveBeenCalledWith(givenResource);
    });

    it('calles helper methods with correct parameters for each generated suggested result', () => {
      getSuggestedResultHrefSpy.mockClear();
      getSuggestedResultIconClassSpy.mockClear();
      getSuggestedResultSubTitleSpy.mockClear();
      getSuggestedResultTitleSpy.mockClear();
      getSuggestedResultTypeSpy.mockClear();
      const givenResource = ResourceType.user;
      const output = wrapper
        .instance()
        .getSuggestedResultsForResource(givenResource);
      output.forEach((result, index) => {
        expect(getSuggestedResultHrefSpy).toHaveBeenCalledWith(
          givenResource,
          mockResourceResults[index],
          index
        );
        expect(getSuggestedResultIconClassSpy).toHaveBeenCalledWith(
          givenResource,
          mockResourceResults[index]
        );
        expect(getSuggestedResultSubTitleSpy).toHaveBeenCalledWith(
          givenResource,
          mockResourceResults[index]
        );
        expect(getSuggestedResultTitleSpy).toHaveBeenCalledWith(
          givenResource,
          mockResourceResults[index]
        );
        expect(getSuggestedResultTypeSpy).toHaveBeenCalledWith(
          givenResource,
          mockResourceResults[index]
        );
      });
    });

    it('generates a SuggestedResult using results of helper methods', () => {
      const output = wrapper
        .instance()
        .getSuggestedResultsForResource(ResourceType.user);
      output.forEach((result) => {
        expect(result.href).toEqual(mockHref);
        expect(result.iconClass).toEqual(mockClass);
        expect(result.subtitle).toEqual(mockSubtitle);
        expect(result.titleNode).toEqual(mockTitle);
        expect(result.type).toEqual(mockType);
      });
    });
  });

  describe('getSuggestedResultHref', () => {
    let props;
    let wrapper;
    beforeAll(() => {
      const setupResult = setup();
      props = setupResult.props;
      wrapper = setupResult.wrapper;
    });
    it('returns the correct href for ResourceType.dashboard', () => {
      const index = 0;
      const givenDashboard = props.dashboards.results[index];
      const expected =
        '/dashboard/product_dashboard%3A%2F%2Fcluster.group%2Fname?source=inline_search&index=0';
      const output = wrapper
        .instance()
        .getSuggestedResultHref(ResourceType.dashboard, givenDashboard, index);

      expect(output).toEqual(expected);
    });
    it('returns the correct href for ResourceType.table', () => {
      const index = 0;
      const givenTable = props.tables.results[index];
      const { cluster, database, schema, name } = givenTable;
      const output = wrapper
        .instance()
        .getSuggestedResultHref(ResourceType.table, givenTable, index);
      expect(output).toEqual(
        `/table_detail/${cluster}/${database}/${schema}/${name}?source=inline_search&index=${index}`
      );
    });
    it('returns the correct href for ResourceType.user', () => {
      const index = 0;
      const givenUser = props.users.results[index];
      const output = wrapper
        .instance()
        .getSuggestedResultHref(ResourceType.user, givenUser, index);
      expect(output).toEqual(
        `/user/${givenUser.user_id}?source=inline_search&index=${index}`
      );
    });
    it('returns empty string as the default', () => {
      const output = wrapper.instance().getSuggestedResultHref('unsupported');
      expect(output).toEqual('');
    });
  });

  describe('getSuggestedResultIconClass', () => {
    let props;
    let wrapper;
    beforeAll(() => {
      const setupResult = setup();
      props = setupResult.props;
      wrapper = setupResult.wrapper;
    });
    it('returns the results of getSourceIconClass for ResourceType.dashboard', () => {
      const mockClass = 'test-class';
      mocked(getSourceIconClass).mockImplementation(() => mockClass);
      const givenDashboard = props.dashboards.results[0];
      const output = wrapper
        .instance()
        .getSuggestedResultIconClass(ResourceType.dashboard, givenDashboard);
      expect(output).toEqual(mockClass);
      expect(getSourceIconClass).toHaveBeenCalledWith(
        givenDashboard.product,
        ResourceType.dashboard
      );
    });
    it('returns the results of getSourceIconClass for ResourceType.table', () => {
      const mockClass = 'test-class';
      mocked(getSourceIconClass).mockImplementation(() => mockClass);
      const givenTable = props.tables.results[0];
      const output = wrapper
        .instance()
        .getSuggestedResultIconClass(ResourceType.table, givenTable);
      expect(output).toEqual(mockClass);
      expect(getSourceIconClass).toHaveBeenCalledWith(
        givenTable.database,
        ResourceType.table
      );
    });
    it('returns the correct class for ResourceType.user', () => {
      const output = wrapper
        .instance()
        .getSuggestedResultIconClass(ResourceType.user, props.users.results[0]);
      expect(output).toEqual(CONSTANTS.USER_ICON_CLASS);
    });
    it('returns empty string as the default', () => {
      const output = wrapper
        .instance()
        .getSuggestedResultIconClass('unsupported');
      expect(output).toEqual('');
    });
  });

  describe('getSuggestedResultSubTitle', () => {
    let props;
    let wrapper;
    beforeAll(() => {
      const setupResult = setup();
      props = setupResult.props;
      wrapper = setupResult.wrapper;
    });
    it('returns the table description for ResourceType.dashboard', () => {
      const givenDashboard = props.dashboards.results[0];
      const output = wrapper
        .instance()
        .getSuggestedResultSubTitle(ResourceType.dashboard, givenDashboard);
      expect(output).toEqual(givenDashboard.description);
    });
    it('returns the table description for ResourceType.table', () => {
      const givenTable = props.tables.results[0];
      const output = wrapper
        .instance()
        .getSuggestedResultSubTitle(ResourceType.table, givenTable);
      expect(output).toEqual(givenTable.description);
    });
    it('returns the team name for ResourceType.user', () => {
      const givenUser = props.users.results[0];
      const output = wrapper
        .instance()
        .getSuggestedResultSubTitle(ResourceType.user, givenUser);
      expect(output).toEqual(givenUser.team_name);
    });
    it('returns empty string as the default', () => {
      const output = wrapper
        .instance()
        .getSuggestedResultSubTitle('unsupported');
      expect(output).toEqual('');
    });
  });

  describe('getSuggestedResultTitle', () => {
    let props;
    let wrapper;
    let output;
    beforeAll(() => {
      const setupResult = setup();
      props = setupResult.props;
      wrapper = setupResult.wrapper;
    });
    it('returns the group and name for ResourceType.dashboard', () => {
      const givenDashboard = props.dashboards.results[0];
      output = shallow(
        wrapper
          .instance()
          .getSuggestedResultTitle(ResourceType.dashboard, givenDashboard)
      );
      expect(output.text()).toEqual(
        `${givenDashboard.name}${givenDashboard.group_name}`
      );
    });
    it('returns the schema.name for ResourceType.table', () => {
      const givenTable = props.tables.results[0];
      output = shallow(
        wrapper
          .instance()
          .getSuggestedResultTitle(ResourceType.table, givenTable)
      );
      expect(output.text()).toEqual(`${givenTable.schema}.${givenTable.name}`);
    });
    it('returns the display_name ResourceType.user', () => {
      const givenUser = props.users.results[0];
      output = shallow(
        wrapper.instance().getSuggestedResultTitle(ResourceType.user, givenUser)
      );
      expect(output.text()).toEqual(givenUser.display_name);
    });
    it('returns empty string as the default', () => {
      output = shallow(
        wrapper.instance().getSuggestedResultTitle('unsupported')
      );
      expect(output.text()).toEqual('');
    });
  });

  describe('getSuggestedResultType', () => {
    let props;
    let wrapper;
    beforeAll(() => {
      const setupResult = setup();
      props = setupResult.props;
      wrapper = setupResult.wrapper;
    });
    it('returns the results of getSourceDisplayName for ResourceType.dashboard', () => {
      const mockName = 'Mode';
      mocked(getSourceDisplayName).mockImplementation(() => mockName);
      const givenDashboard = props.dashboards.results[0];
      const output = wrapper
        .instance()
        .getSuggestedResultType(ResourceType.dashboard, givenDashboard);
      expect(output).toEqual(mockName);
      expect(getSourceDisplayName).toHaveBeenCalledWith(
        givenDashboard.product,
        ResourceType.dashboard
      );
    });
    it('returns the results of getSourceDisplayName for ResourceType.table', () => {
      const mockName = 'Hive';
      mocked(getSourceDisplayName).mockImplementation(() => mockName);
      const givenTable = props.tables.results[0];
      const output = wrapper
        .instance()
        .getSuggestedResultType(ResourceType.table, givenTable);
      expect(output).toEqual(mockName);
      expect(getSourceDisplayName).toHaveBeenCalledWith(
        givenTable.database,
        ResourceType.table
      );
    });
    it('returns the correct type for ResourceType.user', () => {
      const output = wrapper
        .instance()
        .getSuggestedResultType(ResourceType.user, props.users.results[0]);
      expect(output).toEqual(CONSTANTS.PEOPLE_USER_TYPE);
    });
    it('returns empty string as the default', () => {
      const output = wrapper.instance().getSuggestedResultType('unsupported');
      expect(output).toEqual('');
    });
  });

  describe('renderResultsByResource', () => {
    let props;
    let wrapper;

    let mockResults;
    let getSuggestedResultsForResourceSpy;
    let mockTotal;
    let getTotalResultsForResourceSpy;
    let mockTitle;
    let getTitleForResourceSpy;

    describe('if results do not exist', () => {
      beforeAll(() => {
        const setupResult = setup();
        props = setupResult.props;
        wrapper = setupResult.wrapper;
        mockResults = [];
        getSuggestedResultsForResourceSpy = jest
          .spyOn(wrapper.instance(), 'getSuggestedResultsForResource')
          .mockImplementation(() => mockResults);
        wrapper.instance().forceUpdate();
      });

      it('calls helper methods with given resourceType', () => {
        getSuggestedResultsForResourceSpy.mockClear();
        const givenResourceType = ResourceType.dashboard;
        wrapper.instance().renderResultsByResource(givenResourceType);
        expect(getSuggestedResultsForResourceSpy).toHaveBeenCalledWith(
          givenResourceType
        );
      });

      it('renders nothing', () => {
        const givenResourceType = ResourceType.dashboard;
        expect(
          wrapper.instance().renderResultsByResource(givenResourceType)
        ).toBe(null);
      });
    });

    describe('if results exist', () => {
      beforeAll(() => {
        const setupResult = setup();
        props = setupResult.props;
        wrapper = setupResult.wrapper;
        mockResults = [
          {
            href: '/test',
            iconClass: 'test-class',
            subtitle: 'subtitle',
            title: 'title',
            type: 'User',
          },
          {
            href: '/test2',
            iconClass: 'test-class2',
            subtitle: 'subtitle2',
            title: 'title2',
            type: 'User',
          },
        ];
        getSuggestedResultsForResourceSpy = jest
          .spyOn(wrapper.instance(), 'getSuggestedResultsForResource')
          .mockImplementation(() => mockResults);
        mockTotal = 65;
        getTotalResultsForResourceSpy = jest
          .spyOn(wrapper.instance(), 'getTotalResultsForResource')
          .mockImplementation(() => mockTotal);
        mockTitle = 'Datasets';
        getTitleForResourceSpy = jest
          .spyOn(wrapper.instance(), 'getTitleForResource')
          .mockImplementation(() => mockTitle);
        wrapper.instance().forceUpdate();
      });

      it('calls helper methods with given resourceType', () => {
        getSuggestedResultsForResourceSpy.mockClear();
        getTotalResultsForResourceSpy.mockClear();
        getTitleForResourceSpy.mockClear();
        const givenResourceType = ResourceType.dashboard;
        wrapper.instance().renderResultsByResource(givenResourceType);
        expect(getSuggestedResultsForResourceSpy).toHaveBeenCalledWith(
          givenResourceType
        );
        expect(getTotalResultsForResourceSpy).toHaveBeenCalledWith(
          givenResourceType
        );
        expect(getTitleForResourceSpy).toHaveBeenCalledWith(givenResourceType);
      });

      it('renders ResultItemList with expected props', () => {
        const givenResourceType = ResourceType.dashboard;
        const content = shallow(
          wrapper.instance().renderResultsByResource(givenResourceType)
        );
        const item = content
          .find('.inline-results-section')
          .find(ResultItemList);
        const itemProps = item.props();
        expect(itemProps.onItemSelect).toEqual(props.onItemSelect);
        expect(itemProps.resourceType).toEqual(givenResourceType);
        expect(itemProps.suggestedResults).toEqual(mockResults);
        expect(itemProps.totalResults).toEqual(mockTotal);
        expect(itemProps.title).toEqual(mockTitle);
      });
    });
  });

  describe('renderResults', () => {
    let wrapper;
    let renderResultsByResourceSpy;
    beforeAll(() => {
      wrapper = setup().wrapper;
      renderResultsByResourceSpy = jest.spyOn(
        wrapper.instance(),
        'renderResultsByResource'
      );
      wrapper.update();
    });

    it('does not render anything when props.isLoading', () => {
      const { wrapper } = setup({ isLoading: true });
      expect(wrapper.instance().renderResults()).toBe(null);
    });

    describe('when !props.isLoading', () => {
      it('calls renderResultsByResource for ResourceType.table', () => {
        renderResultsByResourceSpy.mockClear();
        wrapper.instance().renderResults();
        expect(renderResultsByResourceSpy).toHaveBeenCalledWith(
          ResourceType.table
        );
      });

      describe('calls renderResultsByResource for ResourceType.user based on config', () => {
        it('does not call if indexUsersEnabled() = false', () => {
          mocked(indexUsersEnabled).mockImplementation(() => false);
          renderResultsByResourceSpy.mockClear();
          wrapper.instance().renderResults();
          expect(renderResultsByResourceSpy).not.toHaveBeenCalledWith(
            ResourceType.user
          );
        });

        it('calls if indexUsersEnabled() = true', () => {
          mocked(indexUsersEnabled).mockImplementation(() => true);
          renderResultsByResourceSpy.mockClear();
          wrapper.instance().renderResults();
          expect(renderResultsByResourceSpy).toHaveBeenCalledWith(
            ResourceType.user
          );
        });
      });
    });
  });

  describe('render', () => {
    let props;
    let wrapper;
    let renderResultsSpy;
    beforeAll(() => {
      const setupResult = setup();
      props = setupResult.props;
      wrapper = setupResult.wrapper;
      renderResultsSpy = jest.spyOn(wrapper.instance(), 'renderResults');
      wrapper.instance().forceUpdate();
    });

    it('renders a SearchItemList with correct props', () => {
      const element = wrapper.find(SearchItemList);
      expect(element.props().onItemSelect).toEqual(props.onItemSelect);
      expect(element.props().searchTerm).toEqual(props.searchTerm);
    });
    it('calls renderResults', () => {
      expect(renderResultsSpy).toHaveBeenCalled();
    });
  });

  describe('mapStateToProps', () => {
    let result;
    beforeAll(() => {
      result = mapStateToProps(globalState);
    });

    it('sets isLoading on the props', () => {
      expect(result.isLoading).toEqual(
        globalState.search.inlineResults.isLoading
      );
    });
    it('sets tables on the props', () => {
      expect(result.tables).toEqual(globalState.search.inlineResults.tables);
    });
    it('sets users on the props', () => {
      expect(result.users).toEqual(globalState.search.inlineResults.users);
    });
  });
});
