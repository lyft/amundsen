// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { mount } from 'enzyme';

import { BadgeStyle } from 'config/config-types';
import * as ConfigUtils from 'config/config-utils';
import { Badge } from 'interfaces/Badges';

import * as Analytics from 'utils/analytics';

import Flag from 'components/Flag';

import BadgeList, { BadgeListProps } from '.';

const columnBadges: Badge[] = [
  {
    badge_name: 'col badge 1',
    category: 'column',
  },
  {
    badge_name: 'col badge 2',
    category: 'column',
  },
];
const badges: Badge[] = [
  {
    badge_name: 'beta',
    category: 'table_status',
  },
  {
    badge_name: 'Core Concepts',
    category: 'coco',
  },
];

const logClickSpy = jest.spyOn(Analytics, 'logClick');
logClickSpy.mockImplementation(() => null);

const setup = (propOverrides?: Partial<BadgeListProps>) => {
  const props = {
    badges,
    onBadgeClick: () => {},
    ...propOverrides,
  };
  // eslint-disable-next-line react/jsx-props-no-spreading
  const wrapper = mount<BadgeListProps>(<BadgeList {...props} />);

  return {
    props,
    wrapper,
  };
};

describe('BadgeList', () => {
  const getBadgeConfigSpy = jest.spyOn(ConfigUtils, 'getBadgeConfig');
  getBadgeConfigSpy.mockImplementation((badgeName: string) => ({
    displayName: badgeName + ' test name',
    style: BadgeStyle.PRIMARY,
  }));

  describe('render', () => {
    describe('when no badges are passed', () => {
      it('renders a badge-list element', () => {
        const { wrapper } = setup();
        const expected = 1;
        const actual = wrapper.find('.badge-list').length;

        expect(actual).toEqual(expected);
      });

      it('does not render any badges', () => {
        const { wrapper } = setup();
        const actual = wrapper.find(Flag).length;
        const expected = 0;

        expect(actual).toEqual(expected);
      });
    });

    describe('when badges are passed', () => {
      it('renders a badge-list element', () => {
        const { wrapper } = setup({ badges });
        const expected = 1;
        const actual = wrapper.find('.badge-list').length;

        expect(actual).toEqual(expected);
      });

      it('renders a .actionable-badge for each badge in the input', () => {
        const { wrapper } = setup({ badges });
        const expected = badges.length;
        const actual = wrapper.find('.actionable-badge').length;

        expect(actual).toEqual(expected);
      });
    });

    describe('when badge category is column', () => {
      it('renders a badge-list element', () => {
        const { wrapper } = setup({ badges: columnBadges });
        const expected = 1;
        const actual = wrapper.find('.badge-list').length;

        expect(actual).toEqual(expected);
      });

      it('renders a .static-badge for each badge in the input', () => {
        const { wrapper } = setup({ badges: columnBadges });
        const expected = 2;
        const actual = wrapper.find('.static-badge').length;

        expect(actual).toEqual(expected);
      });
    });
  });

  describe.only('lifetime', () => {
    describe('when clicking on a badge', () => {
      it('should log the interaction', () => {
        logClickSpy.mockClear();
        const { wrapper } = setup();

        wrapper.find('span.actionable-badge').at(0).simulate('click');
        expect(logClickSpy).toHaveBeenCalled();
      });

      it('should call the handler', () => {
        logClickSpy.mockClear();
        const handlerSpy = jest.fn();
        const { wrapper } = setup({
          onBadgeClick: handlerSpy,
        });
        const expected = 1;

        wrapper.find('span.actionable-badge').at(0).simulate('click');

        const actual = handlerSpy.mock.calls.length;

        expect(actual).toEqual(expected);
      });

      it('should call the handler with the proper badge name', () => {
        logClickSpy.mockClear();
        const handlerSpy = jest.fn();
        const { wrapper } = setup({
          onBadgeClick: handlerSpy,
        });
        const expected = 'beta test name';

        wrapper.find('span.actionable-badge').at(0).simulate('click');

        const actual = handlerSpy.mock.calls[0][0];

        expect(actual).toEqual(expected);
      });
    });
  });
});
