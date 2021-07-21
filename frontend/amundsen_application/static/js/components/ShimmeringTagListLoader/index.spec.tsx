// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { mount } from 'enzyme';

import ShimmeringTagListLoader, {
  ShimmeringTagItem,
  ShimmeringTagListLoaderProps,
} from '.';

const setup = (propOverrides?: Partial<ShimmeringTagListLoaderProps>) => {
  const props: ShimmeringTagListLoaderProps = {
    ...propOverrides,
  };
  const wrapper = mount<ShimmeringTagListLoaderProps>(
    // eslint-disable-next-line react/jsx-props-no-spreading
    <ShimmeringTagListLoader {...props} />
  );

  return { props, wrapper };
};

describe('ShimmeringTagListLoader', () => {
  let wrapper;

  describe('render', () => {
    beforeAll(() => {
      ({ wrapper } = setup());
    });

    it('renders a container', () => {
      const actual = wrapper.find('.shimmer-tag-list-loader').length;
      const expected = 1;

      expect(actual).toEqual(expected);
    });

    it('renders ten tags by default', () => {
      const actual = wrapper.find(ShimmeringTagItem).length;
      const expected = 10;

      expect(actual).toEqual(expected);
    });

    describe('when passing a numItems value', () => {
      it('renders as many tags as requested', () => {
        const expected = 5;
        ({ wrapper } = setup({ numItems: expected }));
        const actual = wrapper.find(ShimmeringTagItem).length;

        expect(actual).toEqual(expected);
      });
    });
  });
});
