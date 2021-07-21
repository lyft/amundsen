// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { shallow } from 'enzyme';
import { Link } from 'react-router-dom';

import BookmarkIcon from 'components/Bookmark/BookmarkIcon';
import { ResourceType } from 'interfaces';

import * as ConfigUtils from 'config/config-utils';
import * as DateUtils from 'utils/dateUtils';

import { dashboardSummary } from 'fixtures/metadata/dashboard';
import { NO_TIMESTAMP_TEXT } from '../../../constants';

import * as Constants from './constants';
import DashboardListItem, { DashboardListItemProps } from './index';

const MOCK_DISPLAY_NAME = 'displayName';
const MOCK_ICON_CLASS = 'test-class';
const MOCK_DATE = 'Jan 1, 2000';

jest.mock('config/config-utils', () => ({
  getSourceDisplayName: jest.fn(() => MOCK_DISPLAY_NAME),
  getSourceIconClass: jest.fn(() => MOCK_ICON_CLASS),
}));
jest.mock('utils/dateUtils', () => ({
  formatDate: jest.fn(() => MOCK_DATE),
}));

describe('DashboardListItem', () => {
  const setup = (propOverrides?: Partial<DashboardListItemProps>) => {
    const props: DashboardListItemProps = {
      logging: { source: 'src', index: 0 },
      dashboard: dashboardSummary,
      ...propOverrides,
    };
    const wrapper = shallow<DashboardListItem>(
      // eslint-disable-next-line react/jsx-props-no-spreading
      <DashboardListItem {...props} />
    );
    return { props, wrapper };
  };

  describe('getLink', () => {
    it('getLink returns correct string', () => {
      const { props, wrapper } = setup();
      const expectedURL =
        '/dashboard/mode_dashboard%3A%2F%2Fcluster.group%2Fname?index=0&source=src';
      const actual = wrapper.instance().getLink();

      expect(actual).toEqual(expectedURL);
    });
  });

  describe('render', () => {
    let props: DashboardListItemProps;
    let wrapper;
    let element;

    beforeAll(() => {
      const setupResult = setup();
      props = setupResult.props;
      wrapper = setupResult.wrapper;
    });

    it('renders item as Link with correct redirection', () => {
      element = wrapper.find(Link);
      expect(element.props().to).toEqual(wrapper.instance().getLink());
    });

    describe('renders resource-info section', () => {
      let resourceInfo;
      beforeAll(() => {
        resourceInfo = wrapper.find('.resource-info');
      });

      it('renders start correct icon', () => {
        const startIcon = resourceInfo.find('.resource-icon');

        expect(startIcon.exists()).toBe(true);
        expect(startIcon.props().className).toEqual(
          `icon resource-icon ${MOCK_ICON_CLASS}`
        );
        expect(ConfigUtils.getSourceIconClass).toHaveBeenCalledWith(
          props.dashboard.product,
          props.dashboard.type
        );
      });

      it('renders dashboard group', () => {
        expect(resourceInfo.find('.dashboard-group').text()).toEqual(
          props.dashboard.group_name
        );
      });

      it('renders dashboard name', () => {
        expect(resourceInfo.find('.dashboard-name').text()).toEqual(
          props.dashboard.name
        );
      });

      it('renders a bookmark icon in the resource name with correct props', () => {
        const elementProps = resourceInfo
          .find('.resource-name')
          .find(BookmarkIcon)
          .props();
        expect(elementProps.bookmarkKey).toBe(props.dashboard.uri);
        expect(elementProps.resourceType).toBe(props.dashboard.type);
      });

      it('renders dashboard description', () => {
        expect(resourceInfo.children().at(1).children().at(1).text()).toEqual(
          props.dashboard.description
        );
      });
    });

    describe('renders resource-type section', () => {
      let resourceType;
      beforeAll(() => {
        resourceType = wrapper.find('.resource-type');
      });

      it('renders resource type', () => {
        expect(resourceType.text()).toEqual(MOCK_DISPLAY_NAME);
        expect(ConfigUtils.getSourceDisplayName).toHaveBeenCalledWith(
          props.dashboard.product,
          props.dashboard.type
        );
      });
    });

    describe('renders resource-badges section', () => {
      let resourceBadges;
      beforeAll(() => {
        resourceBadges = wrapper.find('.resource-badges');
      });

      it('renders resource badges section', () => {
        expect(resourceBadges.exists()).toBe(true);
      });

      describe('for successful run timestamp', () => {
        it('renders default text if it doesnt exist', () => {
          const { props, wrapper } = setup({
            dashboard: {
              group_name: 'Amundsen Team',
              group_url: 'product/group',
              name: 'Amundsen Metrics Dashboard1',
              product: 'mode',
              type: ResourceType.dashboard,
              description: 'I am a dashboard',
              uri: 'product_dashboard://cluster.group/name',
              url: 'product/name',
              cluster: 'cluster',
              last_successful_run_timestamp: 0,
            },
          });
          expect(wrapper.find('.resource-badges').find('.title-3').text()).toBe(
            Constants.LAST_RUN_TITLE
          );
          expect(
            wrapper.find('.resource-badges').find('.body-secondary-3').text()
          ).toBe(NO_TIMESTAMP_TEXT);
        });

        it('renders if timestamp exists', () => {
          expect(resourceBadges.find('.title-3').text()).toBe(
            Constants.LAST_RUN_TITLE
          );
          expect(resourceBadges.find('.body-secondary-3').text()).toBe(
            MOCK_DATE
          );
          expect(DateUtils.formatDate).toHaveBeenCalledWith({
            epochTimestamp: props.dashboard.last_successful_run_timestamp,
          });
        });
      });

      it('renders correct end icon', () => {
        const expectedClassName = 'icon icon-right';
        expect(resourceBadges.find('img').props().className).toEqual(
          expectedClassName
        );
      });
    });
  });
});
