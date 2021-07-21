// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { mount } from 'enzyme';

import StorySection, { BlockProps } from '.';

const setup = (propOverrides?: Partial<BlockProps>) => {
  const props: BlockProps = {
    children: <span className="test-children" />,
    title: 'testTitle',
    ...propOverrides,
  };
  // eslint-disable-next-line react/jsx-props-no-spreading
  const wrapper = mount<BlockProps>(<StorySection {...props} />);

  return { props, wrapper };
};

describe('StorySection', () => {
  describe('render', () => {
    it('renders a story section', () => {
      const { wrapper } = setup();
      const actual = wrapper.find('.story-section').length;
      const expected = 1;

      expect(actual).toEqual(expected);
    });

    it('renders a header', () => {
      const { wrapper } = setup();
      const actual = wrapper.find('.text-headline-w1').length;
      const expected = 1;

      expect(actual).toEqual(expected);
    });

    it('renders the children', () => {
      const { wrapper } = setup();
      const actual = wrapper.find('.test-children').length;
      const expected = 1;

      expect(actual).toEqual(expected);
    });

    describe('when passing a text', () => {
      it('renders the text body', () => {
        const { wrapper } = setup({
          text: 'test text',
        });
        const actual = wrapper.find('.text-body-w1').length;
        const expected = 1;

        expect(actual).toEqual(expected);
      });
    });
  });
});
