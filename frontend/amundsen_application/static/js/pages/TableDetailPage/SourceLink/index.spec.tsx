// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { mount } from 'enzyme';

import AvatarLabel from 'components/AvatarLabel';
import AppConfig from 'config/config';
import { ResourceType } from 'interfaces/Resources';
import SourceLink, { SourceLinkProps } from '.';

const setup = (propOverrides?: Partial<SourceLinkProps>) => {
  const props = {
    tableSource: {
      source_type: 'xyz',
      source: 'www.xyz.com',
    },
    ...propOverrides,
  };
  const wrapper = mount<typeof SourceLink>(<SourceLink {...props} />);
  return { props, wrapper };
};

describe('render SourceLink', () => {
  describe('render', () => {
    it('should render without issues', () => {
      expect(() => {
        setup();
      }).not.toThrow();
    });

    it('should render icon and source link', () => {
      const { wrapper } = setup();
      const expected = 1;
      const actual = wrapper.find('.header-link').length;

      expect(actual).toEqual(expected);
    });

    it('should render correct source link', () => {
      const { wrapper } = setup();
      const expected = 'www.xyz.com';
      const actual = wrapper
        .find('.header-link')
        .getDOMNode()
        .attributes.getNamedItem('href')?.value;

      expect(actual).toEqual(expected);
    });
  });

  describe('when supported description sources present in resource config', () => {
    beforeAll(() => {
      AppConfig.resourceConfig = {
        [ResourceType.table]: {
          displayName: 'Tables',
          supportedDescriptionSources: {
            xyz: {
              displayName: 'XYZ',
              iconPath: 'images/xyz.png',
            },
            abc: {
              displayName: 'ABC',
              iconPath: 'images/abc.png',
            },
          },
        },
        [ResourceType.dashboard]: {
          displayName: 'Dashboards',
        },
        [ResourceType.feature]: {
          displayName: 'ML Features',
        },
        [ResourceType.user]: {
          displayName: 'Users',
        },
      };
    });

    it('should render AvatarLabel', () => {
      const { wrapper } = setup();
      const expected = 1;
      const actual = wrapper.find(AvatarLabel).length;

      expect(actual).toEqual(expected);
    });

    it('should render display name and icon path present in configurations', () => {
      const { wrapper } = setup();
      const expected = { label: 'XYZ', src: 'images/xyz.png' };
      const actual = wrapper.find(AvatarLabel).props();

      expect(actual).toMatchObject(expected);
    });

    it('should render empty icon path and source type as display name', () => {
      const { wrapper } = setup({
        tableSource: {
          source_type: 'foo',
          source: 'www.bar.xz',
        },
      });
      const expected = { label: 'foo', src: '' };
      const actual = wrapper.find(AvatarLabel).props();

      expect(actual).toMatchObject(expected);
    });
  });
});
