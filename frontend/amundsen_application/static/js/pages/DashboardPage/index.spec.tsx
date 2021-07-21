// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import * as ReactMarkdown from 'react-markdown';
import * as History from 'history';
import { shallow } from 'enzyme';

import LoadingSpinner from 'components/LoadingSpinner';
import Breadcrumb from 'components/Breadcrumb';
import BookmarkIcon from 'components/Bookmark/BookmarkIcon';
import ResourceList from 'components/ResourceList';
import TabsComponent from 'components/TabsComponent';
import { dashboardMetadata } from 'fixtures/metadata/dashboard';
import { ResourceType } from 'interfaces';
import { NO_TIMESTAMP_TEXT } from '../../constants';
import ChartList from './ChartList';
import DashboardOwnerEditor from './DashboardOwnerEditor';
import ImagePreview from './ImagePreview';

import { DashboardPage, DashboardPageProps, MatchProps } from '.';

import { getMockRouterProps } from '../../fixtures/mockRouter';

import * as Constants from './constants';

const MOCK_DISPLAY_NAME = 'displayName';
const MOCK_ICON_CLASS = 'dashboard-icon';

jest.mock('config/config-utils', () => ({
  getSourceDisplayName: jest.fn(() => MOCK_DISPLAY_NAME),
  getSourceIconClass: jest.fn(() => MOCK_ICON_CLASS),
  getResourceNotices: jest.fn(() => {}),
}));
const setStateSpy = jest.spyOn(DashboardPage.prototype, 'setState');

const TEST_CLUSTER = 'gold';
const TEST_PRODUCT = 'mode';
const TEST_GROUP = '234testGroupID';
const TEST_DASHBOARD = '123DashboardID';

const setup = (
  propOverrides?: Partial<DashboardPageProps>,
  location?: Partial<History.Location>
) => {
  const routerProps = getMockRouterProps<MatchProps>(
    {
      uri: 'mode_dashboard://gold.234testGroupID/123DashboardID',
    },
    location
  );
  const props = {
    isLoading: false,
    statusCode: 200,
    dashboard: dashboardMetadata,
    getDashboard: jest.fn(),
    searchDashboardGroup: jest.fn(),
    ...routerProps,
    ...propOverrides,
  };
  const wrapper = shallow<DashboardPage>(<DashboardPage {...props} />);

  return { props, wrapper };
};

describe('DashboardPage', () => {
  describe('componentDidMount', () => {
    it('calls getDashboard', () => {
      const { props, wrapper } = setup();

      wrapper.instance().componentDidMount();

      expect(props.getDashboard).toHaveBeenCalled();
    });

    it('calls getDashboard with the right parameters', () => {
      const { props, wrapper } = setup();
      const expectedURI = `${TEST_PRODUCT}_dashboard://${TEST_CLUSTER}.${TEST_GROUP}/${TEST_DASHBOARD}`;
      const expectedArguments = {
        source: undefined,
        searchIndex: undefined,
        uri: expectedURI,
      };

      wrapper.instance().componentDidMount();

      expect(props.getDashboard).toHaveBeenCalledWith(expectedArguments);
    });
  });

  describe('componentDidUpdate', () => {
    let props;
    let wrapper;
    let getDashboardSpy;

    beforeEach(() => {
      ({ props, wrapper } = setup());

      getDashboardSpy = props.getDashboard;
    });

    describe('when params change', () => {
      it('calls getDashboard', () => {
        getDashboardSpy.mockClear();
        setStateSpy.mockClear();
        const newParams = {
          uri:
            'testProduct_dashboard://testCluster.testGroupID/testDashboardID',
        };
        const expectedURI = `testProduct_dashboard://testCluster.testGroupID/testDashboardID`;
        const expectedArguments = {
          searchIndex: undefined,
          source: undefined,
          uri: expectedURI,
        };

        wrapper.setProps({ match: { params: newParams } });

        expect(getDashboardSpy).toHaveBeenCalledWith(expectedArguments);
        expect(setStateSpy).toHaveBeenCalledWith({ uri: expectedURI });
      });
    });

    describe('when params do not change', () => {
      it('does not call getDashboard', () => {
        getDashboardSpy.mockClear();
        setStateSpy.mockClear();

        wrapper.instance().componentDidUpdate();

        expect(getDashboardSpy).not.toHaveBeenCalled();
        expect(setStateSpy).not.toHaveBeenCalled();
      });
    });
  });

  describe('render', () => {
    const { props, wrapper } = setup();

    it('renders the loading spinner when loading', () => {
      const { wrapper } = setup({ isLoading: true });

      expect(wrapper.find(LoadingSpinner).exists()).toBeTruthy();
    });

    it('renders a breadcrumb component', () => {
      expect(wrapper.find(Breadcrumb).exists()).toBeTruthy();
    });

    it('renders a the dashboard title', () => {
      const headerText = wrapper.find('.header-title-text').text();

      expect(headerText).toEqual(props.dashboard.name);
    });

    it('renders a bookmark icon with correct props', () => {
      const elementProps = wrapper.find(BookmarkIcon).props();

      expect(elementProps.bookmarkKey).toBe(props.dashboard.uri);
      expect(elementProps.resourceType).toBe(ResourceType.dashboard);
    });

    describe('renders description', () => {
      it('using a ReactMarkdown component', () => {
        const markdown = wrapper.find(ReactMarkdown);
        expect(markdown.exists()).toBe(true);
      });

      it('with link to add description if none exists', () => {
        const { wrapper } = setup({
          dashboard: {
            ...dashboardMetadata,
            description: '',
          },
        });
        const link = wrapper.find('a.edit-link');

        expect(link.props().href).toBe(props.dashboard.url);
        expect(link.text()).toBe(
          `${Constants.ADD_DESC_TEXT} ${MOCK_DISPLAY_NAME}`
        );
      });
    });

    it('renders owners', () => {
      const { wrapper } = setup();
      expect(wrapper.find(DashboardOwnerEditor).exists()).toBe(true);
    });

    it('renders a ResourceStatusMarker for last run state', () => {
      const expected = 1;
      const actual = wrapper
        .find('.last-run-state')
        .find('ResourceStatusMarker').length;

      expect(actual).toEqual(expected);
    });

    it('renders an ImagePreview with correct props', () => {
      expect(wrapper.find(ImagePreview).props().uri).toBe(wrapper.state().uri);
    });

    describe('renders timestamps correctly when unavailable', () => {
      const { wrapper } = setup({
        dashboard: {
          ...dashboardMetadata,
          last_run_timestamp: null,
          last_successful_run_timestamp: null,
        },
      });

      it('last_run_timestamp', () => {
        expect(wrapper.find('.last-run-timestamp').text()).toEqual(
          NO_TIMESTAMP_TEXT
        );
      });

      it('last_successful_run_timestamp', () => {
        expect(wrapper.find('.last-successful-run-timestamp').text()).toEqual(
          NO_TIMESTAMP_TEXT
        );
      });
    });
  });

  describe('renderTabs', () => {
    const { props, wrapper } = setup();

    it('returns a ResourceList', () => {
      const result = shallow(wrapper.instance().renderTabs());
      const element = result.find(ResourceList);

      expect(element.exists()).toBe(true);
      expect(element.props().allItems).toEqual(props.dashboard.tables);
    });

    it('returns a Tabs component', () => {
      const result = wrapper.instance().renderTabs();

      expect(result.type).toEqual(TabsComponent);
    });

    it('does not render ChartList if no charts', () => {
      const { wrapper } = setup({
        dashboard: {
          ...dashboardMetadata,
          chart_names: [],
        },
      });
      const result = shallow(wrapper.instance().renderTabs());

      expect(result.find(ChartList).exists()).toBe(false);
    });
  });
});
