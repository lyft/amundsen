// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import * as DocumentTitle from 'react-document-title';
import * as Avatar from 'react-avatar';
import { shallow } from 'enzyme';
import { mocked } from 'ts-jest/utils';

import Breadcrumb from 'components/Breadcrumb';
import ResourceList from 'components/ResourceList';
import TabsComponent from 'components/TabsComponent';

import globalState from 'fixtures/globalState';
import { getMockRouterProps } from 'fixtures/mockRouter';
import { ResourceType } from 'interfaces/Resources';

import * as LogUtils from 'utils/logUtils';

import { indexDashboardsEnabled } from 'config/config-utils';
import { AVATAR_SIZE } from './constants';
import {
  mapDispatchToProps,
  mapStateToProps,
  ProfilePage,
  ProfilePageProps,
  RouteProps,
} from '.';

jest.mock('config/config-utils', () => ({
  getDisplayNameByResource: jest.fn(() => 'Resource'),
  indexDashboardsEnabled: jest.fn(),
}));

describe('ProfilePage', () => {
  const setup = (propOverrides?: Partial<ProfilePageProps>) => {
    const routerProps = getMockRouterProps<RouteProps>(
      {
        userId: 'test0',
      },
      undefined
    );
    const props: ProfilePageProps = {
      user: globalState.user.profile.user,
      resourceRelations: {
        [ResourceType.table]: {
          bookmarks: [
            {
              type: ResourceType.table,
            },
            {
              type: ResourceType.table,
            },
            {
              type: ResourceType.table,
            },
            {
              type: ResourceType.table,
            },
          ],
          read: [],
          own: [],
        },
        [ResourceType.dashboard]: {
          bookmarks: [],
          read: [],
          own: [],
        },
      },
      getUserById: jest.fn(),
      getUserOwn: jest.fn(),
      getUserRead: jest.fn(),
      getBookmarksForUser: jest.fn(),
      ...routerProps,
      ...propOverrides,
    };
    // eslint-disable-next-line react/jsx-props-no-spreading
    const wrapper = shallow<ProfilePage>(<ProfilePage {...props} />);
    return {
      props,
      wrapper,
    };
  };

  describe('componentDidMount', () => {
    it('calls loadUserInfo', () => {
      const { wrapper } = setup();
      const loadUserInfoSpy = jest.spyOn(wrapper.instance(), 'loadUserInfo');
      wrapper.instance().componentDidMount();
      expect(loadUserInfoSpy).toHaveBeenCalled();
    });
  });

  describe('componentDidUpdate', () => {
    let wrapper;
    let loadUserInfoSpy;

    beforeEach(() => {
      ({ wrapper } = setup());
      loadUserInfoSpy = jest.spyOn(wrapper.instance(), 'loadUserInfo');
    });

    it('calls loadUserInfo when userId has changes', () => {
      wrapper.setProps({ match: { params: { userId: 'newUserId' } } });
      expect(loadUserInfoSpy).toHaveBeenCalled();
    });

    it('does not call loadUserInfo when userId has not changed', () => {
      wrapper.instance().componentDidUpdate();
      expect(loadUserInfoSpy).not.toHaveBeenCalled();
    });
  });

  describe('loadUserInfo', () => {
    it('calls getLoggingParams', () => {
      const { props, wrapper } = setup();
      const getLoggingParamsSpy = jest.spyOn(LogUtils, 'getLoggingParams');

      wrapper.instance().loadUserInfo('test');

      expect(getLoggingParamsSpy).toHaveBeenCalledWith(props.location.search);
    });

    it('calls props.getUserById', () => {
      const { props } = setup();

      expect(props.getUserById).toHaveBeenCalled();
    });

    it('calls props.getUserOwn', () => {
      const { props } = setup();

      expect(props.getUserOwn).toHaveBeenCalled();
    });

    it('calls props.getUserRead', () => {
      const { props } = setup();

      expect(props.getUserRead).toHaveBeenCalled();
    });

    it('calls props.getBookmarksForUser', () => {
      const { props } = setup();

      expect(props.getBookmarksForUser).toHaveBeenCalled();
    });
  });

  describe('generateTabContent', () => {
    let props;
    let wrapper;
    let givenResource;
    let content;

    beforeAll(() => {
      ({ props, wrapper } = setup());
      givenResource = ResourceType.table;
      content = shallow(
        <div>{wrapper.instance().generateTabContent(givenResource)}</div>
      );
    });

    describe('for a resource', () => {
      it('returns a ResourceList for the own resourceRelations', () => {
        expect(content.find(ResourceList).at(0).props().allItems).toBe(
          props.resourceRelations[givenResource].own
        );
      });

      it('returns a ResourceList for the bookmarked resourceRelations', () => {
        expect(content.find(ResourceList).at(1).props().allItems).toBe(
          props.resourceRelations[givenResource].bookmarks
        );
      });

      it('returns a ResourceList for the read resourceRelations', () => {
        expect(content.find(ResourceList).at(2).props().allItems).toBe(
          props.resourceRelations[givenResource].read
        );
      });
    });

    describe('for dashboard resource', () => {
      it('does not return a ResourceList for the read resourceRelations', () => {
        content = shallow(
          <div>
            {wrapper.instance().generateTabContent(ResourceType.dashboard)}
          </div>
        );
        expect(content.find(ResourceList).at(2).exists()).toBe(false);
      });
    });
  });

  describe('generateTabKey', () => {
    it('returns string used for the tab keys', () => {
      const { wrapper } = setup();
      const givenResource = ResourceType.table;
      expect(wrapper.instance().generateTabKey(givenResource)).toEqual(
        `tab:${givenResource}`
      );
    });
  });

  describe('generateTabTitle', () => {
    it('returns string for tab title according to UI designs', () => {
      const { wrapper } = setup();
      const givenResource = ResourceType.table;

      expect(wrapper.instance().generateTabTitle(givenResource)).toEqual(
        'Resource (4)'
      );
    });
  });

  describe('generateTabInfo', () => {
    let tabInfoArray;
    let props;
    let wrapper;
    let generateTabContentSpy;
    let generateTabKeySpy;
    let generateTabTitleSpy;

    beforeAll(() => {
      ({ props, wrapper } = setup());

      generateTabContentSpy = jest
        .spyOn(wrapper.instance(), 'generateTabContent')
        .mockImplementation((input) => `${input}Content`);
      generateTabKeySpy = jest
        .spyOn(wrapper.instance(), 'generateTabKey')
        .mockImplementation((input) => `${input}Key`);
      generateTabTitleSpy = jest
        .spyOn(wrapper.instance(), 'generateTabTitle')
        .mockImplementation((input) => `${input}Title`);
    });

    describe('pushes tab info for tables', () => {
      let tableTab;

      beforeAll(() => {
        tabInfoArray = wrapper.instance().generateTabInfo();
        tableTab = tabInfoArray.find((tab) => tab.key === 'tableKey');
      });

      it('generates content for table tab info', () => {
        expect(generateTabContentSpy).toHaveBeenCalledWith(ResourceType.table);
        expect(tableTab.content).toBe('tableContent');
      });

      it('generates key for table tab info', () => {
        expect(generateTabKeySpy).toHaveBeenCalledWith(ResourceType.table);
        expect(tableTab.key).toBe('tableKey');
      });

      it('generates title for table tab info', () => {
        expect(generateTabTitleSpy).toHaveBeenCalledWith(ResourceType.table);
        expect(tableTab.title).toBe('tableTitle');
      });
    });

    describe('handle tab info for dashboards', () => {
      let dashboardTab;

      describe('if dashboards are not enabled', () => {
        it('does not render dashboard tab', () => {
          mocked(indexDashboardsEnabled).mockImplementationOnce(() => false);
          tabInfoArray = wrapper.instance().generateTabInfo();
          expect(tabInfoArray.find((tab) => tab.key === 'dashboardKey')).toBe(
            undefined
          );
        });
      });

      describe('if dashboards are enabled', () => {
        beforeAll(() => {
          mocked(indexDashboardsEnabled).mockImplementationOnce(() => true);
          tabInfoArray = wrapper.instance().generateTabInfo();
          dashboardTab = tabInfoArray.find((tab) => tab.key === 'dashboardKey');
        });

        it('generates content for table tab info', () => {
          expect(generateTabContentSpy).toHaveBeenCalledWith(
            ResourceType.dashboard
          );
          expect(dashboardTab.content).toBe('dashboardContent');
        });

        it('generates key for table tab info', () => {
          expect(generateTabKeySpy).toHaveBeenCalledWith(
            ResourceType.dashboard
          );
          expect(dashboardTab.key).toBe('dashboardKey');
        });

        it('generates title for table tab info', () => {
          expect(generateTabTitleSpy).toHaveBeenCalledWith(
            ResourceType.dashboard
          );
          expect(dashboardTab.title).toBe('dashboardTitle');
        });
      });
    });
  });

  describe('render', () => {
    let props;
    let wrapper;

    beforeAll(() => {
      ({ props, wrapper } = setup());
    });

    it('renders DocumentTitle w/ correct title', () => {
      expect(wrapper.find(DocumentTitle).props().title).toEqual(
        `${props.user.display_name} - Amundsen Profile`
      );
    });

    it('renders Breadcrumb', () => {
      expect(wrapper.find(Breadcrumb).exists()).toBe(true);
    });

    it('renders Avatar for user.display_name', () => {
      expect(wrapper.find(Avatar).props()).toMatchObject({
        name: props.user.display_name,
        size: AVATAR_SIZE,
        round: true,
      });
    });

    it('does not render Avatar if user.display_name is empty string', () => {
      const userCopy = {
        ...globalState.user.profile.user,
        display_name: '',
      };
      const { wrapper } = setup({
        user: userCopy,
      });
      expect(wrapper.find('#profile-avatar').children().exists()).toBeFalsy();
    });

    it('renders header with display_name', () => {
      expect(wrapper.find('.header-title-text').text()).toContain(
        props.user.display_name
      );
    });

    it('renders user role', () => {
      expect(wrapper.find('#user-role').text()).toEqual('Tester');
    });

    it('renders user team name', () => {
      expect(wrapper.find('#team-name').text()).toEqual('QA');
    });

    it('renders user manager', () => {
      expect(wrapper.find('#user-manager').text()).toEqual(
        'Manager: Test Manager'
      );
    });

    it('renders alumni bullet is user not active', () => {
      const userCopy = {
        ...globalState.user.profile.user,
        is_active: false,
      };
      const { wrapper } = setup({
        user: userCopy,
      });
      const expected = 1;
      expect(wrapper.find('#alumni').length).toEqual(expected);
    });

    it('renders github link with correct href', () => {
      expect(wrapper.find('#github-link').props().href).toEqual(
        'https://github.com/githubName'
      );
    });

    it('renders github link with correct text', () => {
      expect(wrapper.find('#github-link').find('span').text()).toEqual(
        'Github'
      );
    });

    it('renders Tabs w/ correct props', () => {
      const mockKey = 'test';
      const generateTabKeySpy = jest
        .spyOn(wrapper.instance(), 'generateTabKey')
        .mockImplementation(() => mockKey);
      wrapper.instance().forceUpdate();
      expect(
        wrapper.find('.profile-body').find(TabsComponent).props()
      ).toMatchObject({
        tabs: wrapper.instance().generateTabInfo(),
        defaultTab: mockKey,
      });
    });

    describe('if user.is_active', () => {
      // TODO - Uncomment when slack integration is built
      // it('renders slack link with correct href', () => {
      //   expect(wrapper.find('#slack-link').props().href).toEqual('www.slack.com');
      // });
      //
      // it('renders slack link with correct text', () => {
      //   expect(wrapper.find('#slack-link').find('span').text()).toEqual('Slack');
      // });

      it('renders email link with correct href', () => {
        expect(wrapper.find('#email-link').props().href).toEqual(
          'mailto:test@test.com'
        );
      });

      it('renders email link with correct text', () => {
        expect(
          wrapper.find('#email-link').find('.email-link-label').text()
        ).toEqual('test@test.com');
      });

      it('renders profile link with correct href', () => {
        expect(wrapper.find('#profile-link').props().href).toEqual(
          'www.test.com'
        );
      });

      it('renders profile link with correct text', () => {
        expect(
          wrapper.find('#profile-link').find('.profile-link-label').text()
        ).toEqual('Employee Profile');
      });
    });
  });
});

describe('mapDispatchToProps', () => {
  let dispatch;
  let result;

  beforeEach(() => {
    dispatch = jest.fn(() => Promise.resolve());
    result = mapDispatchToProps(dispatch);
  });

  it('sets getUserById on the props', () => {
    expect(result.getUserById).toBeInstanceOf(Function);
  });

  it('sets getUserOwn on the props', () => {
    expect(result.getUserOwn).toBeInstanceOf(Function);
  });

  it('sets getUserRead on the props', () => {
    expect(result.getUserRead).toBeInstanceOf(Function);
  });

  it('sets getBookmarksForUser on the props', () => {
    expect(result.getBookmarksForUser).toBeInstanceOf(Function);
  });
});

describe('mapStateToProps', () => {
  let result;
  beforeEach(() => {
    result = mapStateToProps(globalState);
  });

  it('sets user on the props', () => {
    expect(result.user).toEqual(globalState.user.profile.user);
  });

  describe('sets resourceRelations on the props', () => {
    it('sets relations for tables', () => {
      const tables = result.resourceRelations[ResourceType.table];
      expect(tables.bookmarks).toBe(
        globalState.bookmarks.bookmarksForUser[ResourceType.table]
      );
      expect(tables.own).toBe(globalState.user.profile.own[ResourceType.table]);
      expect(tables.read).toBe(globalState.user.profile.read);
    });

    it('sets relations for dashboards', () => {
      const dashboards = result.resourceRelations[ResourceType.dashboard];
      expect(dashboards.bookmarks).toBe(
        globalState.bookmarks.bookmarksForUser[ResourceType.dashboard]
      );
      expect(dashboards.own).toBe(
        globalState.user.profile.own[ResourceType.dashboard]
      );
    });
  });
});
