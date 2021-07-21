// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import * as Avatar from 'react-avatar';
import * as History from 'history';
import { shallow } from 'enzyme';
import { Dropdown, MenuItem } from 'react-bootstrap';
import { Link, NavLink } from 'react-router-dom';

import { getMockRouterProps } from 'fixtures/mockRouter';

import Feedback from 'features/Feedback';
import SearchBar from 'components/SearchBar';
import { logClick } from 'utils/analytics';

import AppConfig from 'config/config';

import globalState from 'fixtures/globalState';
import { NavBar, NavBarProps, mapStateToProps } from '.';

jest.mock('ducks/utilMethods', () =>
  jest.fn().mockImplementation(() => ({ logClick: jest.fn() }))
);

AppConfig.logoPath = '/test';
AppConfig.logoTitle = 'test';
AppConfig.navLinks = [
  {
    label: 'Announcements',
    href: '/announcements',
    id: 'link1',
    target: '_blank',
    use_router: true,
  },
  {
    label: 'Browse',
    href: '/browse',
    id: 'link2',
    target: '_blank',
    use_router: false,
  },
];
AppConfig.indexUsers.enabled = true;
AppConfig.mailClientFeatures.feedbackEnabled = true;

describe('NavBar', () => {
  const setup = (
    propOverrides?: Partial<NavBarProps>,
    location?: Partial<History.Location>
  ) => {
    const routerProps = getMockRouterProps<any>(null, location);
    const props: NavBarProps = {
      loggedInUser: globalState.user.loggedInUser,
      ...routerProps,
      ...propOverrides,
    };
    const wrapper = shallow<NavBar>(<NavBar {...props} />);
    return { props, wrapper };
  };

  describe('generateNavLinks', () => {
    let content;
    beforeAll(() => {
      const { props, wrapper } = setup();
      content = wrapper.instance().generateNavLinks(AppConfig.navLinks);
    });

    it('returns a NavLink w/ correct props if user_router is true', () => {
      const expectedContent = JSON.stringify(
        <NavLink
          className="title-3 border-bottom-white"
          key={0}
          to="/announcements"
          target="_blank"
          onClick={logClick}
        >
          Announcements
        </NavLink>
      );
      expect(JSON.stringify(content[0])).toEqual(expectedContent);
    });

    it('returns an anchor w/ correct props if user_router is false', () => {
      expect(shallow(content[1]).find('a').props()).toMatchObject({
        href: '/browse',
        target: '_blank',
      });
    });

    it('returns an anchor w/ correct test if user_router is false', () => {
      expect(shallow(content[1]).find('a').text()).toEqual('Browse');
    });
  });

  describe('renderSearchBar', () => {
    it('returns small SearchBar when not on home page', () => {
      const { props, wrapper } = setup(undefined, { pathname: '/search' });
      const rendered = wrapper.instance().renderSearchBar();
      if (rendered === null) {
        throw Error('rendering search bar returned null');
      }
      const searchBar = shallow(rendered).find(SearchBar);
      expect(searchBar.exists()).toBe(true);
      expect(searchBar.props()).toMatchObject({
        size: 'small',
      });
    });

    it('returns null if conditions to render search bar are not met', () => {
      const { props, wrapper } = setup(undefined, { pathname: '/' });
      expect(wrapper.instance().renderSearchBar()).toBe(null);
    });
  });

  describe('render', () => {
    let element;
    let props;
    let wrapper;
    let renderSearchBarSpy;
    const spy = jest.spyOn(NavBar.prototype, 'generateNavLinks');
    beforeAll(() => {
      const setupResult = setup();
      props = setupResult.props;
      wrapper = setupResult.wrapper;
      renderSearchBarSpy = jest.spyOn(wrapper.instance(), 'renderSearchBar');
      wrapper.instance().forceUpdate();
    });

    it('renders img with AppConfig.logoPath', () => {
      element = wrapper.find('img#logo-icon');
      expect(element.props()).toMatchObject({
        id: 'logo-icon',
        className: 'logo-icon',
        src: AppConfig.logoPath,
      });
    });

    it('renders homepage Link with correct path', () => {
      element = wrapper.find('#nav-bar-left').find(Link);
      expect(element.props().to).toEqual('/');
    });

    it('renders homepage Link with correct text', () => {
      element = wrapper.find('#nav-bar-left').find(Link).find('.title-3');
      expect(element.children().text()).toEqual('test');
    });

    it('calls generateNavLinks with correct props', () => {
      expect(spy).toHaveBeenCalledWith(AppConfig.navLinks);
    });

    it('calls renderSearchBar', () => {
      expect(renderSearchBarSpy).toHaveBeenCalled();
    });

    it('renders Feedback component', () => {
      expect(wrapper.find(Feedback).exists()).toBe(true);
    });

    it('renders Avatar for loggedInUser', () => {
      expect(wrapper.find(Avatar).props()).toMatchObject({
        name: props.loggedInUser.display_name,
        size: 32,
        round: true,
      });
    });

    describe('if indexUsers is enabled', () => {
      it('renders Avatar for loggedInUser inside of user dropdown', () => {
        expect(
          wrapper.find(Dropdown).find(Dropdown.Toggle).find(Avatar).props()
        ).toMatchObject({
          name: props.loggedInUser.display_name,
          size: 32,
          round: true,
        });
      });

      it('renders user dropdown header', () => {
        element = wrapper
          .find(Dropdown)
          .find(Dropdown.Menu)
          .find('.profile-menu-header');
        expect(element.children().at(0).text()).toEqual(
          props.loggedInUser.display_name
        );
        expect(element.children().at(1).text()).toEqual(
          props.loggedInUser.email
        );
      });

      it('renders My Profile link correctly inside of user dropdown', () => {
        element = wrapper
          .find(Dropdown)
          .find(Dropdown.Menu)
          .find(MenuItem)
          .at(0);
        expect(element.children().text()).toEqual('My Profile');
        expect(element.props().to).toEqual('/user/test0?source=navbar');
      });
    });

    describe('if indexUsers is disabled', () => {
      it('does not render a Link to the user profile', () => {
        AppConfig.indexUsers.enabled = false;
        const { wrapper } = setup();
        expect(wrapper.find('#nav-bar-avatar-link').exists()).toBe(false);
      });
    });
  });
});

describe('mapStateToProps', () => {
  let result;
  beforeEach(() => {
    result = mapStateToProps(globalState);
  });

  it('sets loggedInUser on the props', () => {
    expect(result.loggedInUser).toEqual(globalState.user.loggedInUser);
  });
});
