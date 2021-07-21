// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { mount } from 'enzyme';

import ShimmeringResourceLoader, {
  ShimmeringResourceItem,
  ShimmeringResourceLoaderProps,
} from '.';

const setup = (propOverrides?: Partial<ShimmeringResourceLoaderProps>) => {
  const props: ShimmeringResourceLoaderProps = {
    ...propOverrides,
  };
  const wrapper = mount<ShimmeringResourceLoaderProps>(
    // eslint-disable-next-line react/jsx-props-no-spreading
    <ShimmeringResourceLoader {...props} />
  );

  return { props, wrapper };
};

describe('ShimmeringResourceLoader', () => {
  let wrapper;

  describe('render', () => {
    beforeAll(() => {
      ({ wrapper } = setup());
    });

    it('renders a container', () => {
      const actual = wrapper.find('.shimmer-resource-loader').length;
      const expected = 1;

      expect(actual).toEqual(expected);
    });

    it('renders three items by default', () => {
      const actual = wrapper.find(ShimmeringResourceItem).length;
      const expected = 3;

      expect(actual).toEqual(expected);
    });

    describe('when passing a numItems value', () => {
      it('renders as many items as requested', () => {
        const expected = 5;
        ({ wrapper } = setup({ numItems: expected }));
        const actual = wrapper.find(ShimmeringResourceItem).length;

        expect(actual).toEqual(expected);
      });
    });
  });
});
