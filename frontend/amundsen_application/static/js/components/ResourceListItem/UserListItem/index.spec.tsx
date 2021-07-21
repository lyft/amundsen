// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';

import { shallow } from 'enzyme';

import * as Avatar from 'react-avatar';
import { Link } from 'react-router-dom';

import { ResourceType } from 'interfaces';
import UserListItem, { UserListItemProps } from '.';

describe('UserListItem', () => {
  const setup = (propOverrides?: Partial<UserListItemProps>) => {
    const props: UserListItemProps = {
      logging: {
        source: 'src',
        index: 0,
      },
      user: {
        type: ResourceType.user,
        display_name: 'firstname lastname',
        email: 'test@test.com',
        employee_type: 'fulltime',
        first_name: 'firstname',
        full_name: 'firstname lastname',
        github_username: 'githubName',
        is_active: true,
        last_name: 'lastname',
        manager_fullname: 'Test Manager',
        profile_url: 'www.test.com',
        role_name: 'Tester',
        slack_id: 'www.slack.com',
        team_name: 'QA',
        user_id: 'test0',
      },
      ...propOverrides,
    };
    // eslint-disable-next-line react/jsx-props-no-spreading
    const wrapper = shallow<UserListItem>(<UserListItem {...props} />);
    return {
      props,
      wrapper,
    };
  };

  describe('renderUserInfo', () => {
    let props: UserListItemProps;
    let wrapper;
    beforeAll(() => {
      const setupResult = setup();
      props = setupResult.props;
      wrapper = setupResult.wrapper;
    });
    it('returns null if no role_name or team_name exists on', () => {
      const testUser = {
        type: ResourceType.user,
        display_name: 'firstname lastname',
        email: 'test@test.com',
        employee_type: 'fulltime',
        first_name: 'firstname',
        full_name: 'firstname lastname',
        github_username: 'githubName',
        is_active: false,
        last_name: 'lastname',
        manager_fullname: 'Test Manager',
        profile_url: 'www.test.com',
        role_name: null,
        slack_id: 'www.slack.com',
        team_name: '',
        user_id: 'test0',
      };
      expect(wrapper.instance().renderUserInfo(testUser)).toBe(null);
    });

    it('returns an array of list items for user description', () => {
      const content = wrapper.instance().renderUserInfo(props.user);
      expect(shallow(content[0]).find('li').text()).toEqual(
        props.user.role_name
      );
      expect(shallow(content[1]).find('li').text()).toEqual(
        props.user.team_name
      );
    });
  });

  describe('render', () => {
    let props: UserListItemProps;
    let wrapper;
    beforeAll(() => {
      const setupResult = setup();
      props = setupResult.props;
      wrapper = setupResult.wrapper;
    });

    it('renders item as Link', () => {
      expect(wrapper.find(Link).exists()).toBeTruthy();
    });

    describe('renders resource-info section', () => {
      let resourceInfo;
      beforeAll(() => {
        resourceInfo = wrapper.find('.resource-info');
      });

      it('renders Avatar', () => {
        expect(resourceInfo.find(Avatar).props()).toMatchObject({
          name: props.user.display_name,
          size: 24,
          round: true,
        });
      });

      it('renders user.name', () => {
        expect(resourceInfo.children().at(1).children().at(0).text()).toEqual(
          props.user.display_name
        );
      });

      it('calls renderUserInfo with correct props', () => {
        const renderUserInfoSpy = jest.spyOn(
          wrapper.instance(),
          'renderUserInfo'
        );
        wrapper.instance().forceUpdate();
        expect(renderUserInfoSpy).toHaveBeenCalledWith(props.user);
      });

      it('renders ul with list item results of renderUserInfo', () => {
        const renderUserInfoSpy = jest
          .spyOn(wrapper.instance(), 'renderUserInfo')
          .mockImplementation(() => <div>Mock Info</div>);
        wrapper.instance().forceUpdate();
        expect(
          wrapper
            .find('.resource-info')
            .children()
            .at(1)
            .children()
            .at(1)
            .find('ul')
            .children()
            .html()
        ).toEqual('<div>Mock Info</div>');
      });

      it('does not render description if renderUserInfo returns null', () => {
        const renderUserInfoSpy = jest
          .spyOn(wrapper.instance(), 'renderUserInfo')
          .mockImplementation(() => null);
        wrapper.instance().forceUpdate();
        expect(
          wrapper
            .find('.resource-info')
            .children()
            .at(1)
            .children()
            .at(1)
            .exists()
        ).toBe(false);
      });
    });

    describe('renders resource-type section', () => {
      let resourceType;
      beforeAll(() => {
        resourceType = wrapper.find('.resource-type');
      });

      it('renders resource type', () => {
        expect(resourceType.text()).toEqual('User');
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

      it('renders correct end icon', () => {
        const expectedClassName = 'icon icon-right';
        expect(resourceBadges.find('img').props().className).toEqual(
          expectedClassName
        );
      });
    });
  });

  describe('getLink', () => {
    it('getLink returns correct string', () => {
      const { props, wrapper } = setup();
      const { user, logging } = props;
      expect(wrapper.instance().getLink()).toEqual(
        `/user/${user.user_id}?index=${logging.index}&source=${logging.source}`
      );
    });
  });
});
