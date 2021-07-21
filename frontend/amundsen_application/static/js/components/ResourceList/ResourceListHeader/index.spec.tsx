// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { mount } from 'enzyme';

import { ResourceType } from 'interfaces';
import ResourceListHeader, { ResourceListHeaderProps } from '.';

const setup = (propOverrides?: Partial<ResourceListHeaderProps>) => {
  const props: ResourceListHeaderProps = {
    resourceTypes: [],
    ...propOverrides,
  };
  const wrapper = mount<ResourceListHeaderProps>(
    // eslint-disable-next-line react/jsx-props-no-spreading
    <ResourceListHeader {...props} />
  );

  return { props, wrapper };
};

describe('ResourceListHeader', () => {
  describe('render', () => {
    describe('when no resourceTypes are passed', () => {
      it('renders nothing', () => {
        const { wrapper } = setup();
        const actual = wrapper.find('.resource-list-header').length;
        const expected = 0;

        expect(actual).toEqual(expected);
      });
    });

    describe('when resourceType has a user', () => {
      it('renders three resource headers', () => {
        const { wrapper } = setup({ resourceTypes: [ResourceType.user] });
        const actual = wrapper.find('.header-text').length;
        const expected = 3;

        expect(actual).toEqual(expected);
      });
    });

    describe('when resourceType has a table', () => {
      it('renders three resource headers', () => {
        const { wrapper } = setup({ resourceTypes: [ResourceType.table] });
        const actual = wrapper.find('.header-text').length;
        const expected = 3;

        expect(actual).toEqual(expected);
      });
    });

    describe('when resourceType has a feature', () => {
      it('renders three resource headers', () => {
        const { wrapper } = setup({ resourceTypes: [ResourceType.feature] });
        const actual = wrapper.find('.header-text').length;
        const expected = 4;

        expect(actual).toEqual(expected);
      });
    });

    describe('when resourceType has a dashboard', () => {
      it('renders three resource headers', () => {
        const { wrapper } = setup({ resourceTypes: [ResourceType.dashboard] });
        const actual = wrapper.find('.header-text').length;
        const expected = 3;

        expect(actual).toEqual(expected);
      });
    });
  });
});
