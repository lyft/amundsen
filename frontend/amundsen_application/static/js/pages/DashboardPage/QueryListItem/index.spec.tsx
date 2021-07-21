// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';

import { mount } from 'enzyme';

import QueryListItem, { QueryListItemProps } from '.';

const setup = (propOverrides?: Partial<QueryListItemProps>) => {
  const props: QueryListItemProps = {
    product: 'Mode',
    text: 'testQuery',
    url: 'http://test.url',
    name: 'testName',
    ...propOverrides,
  };
  // eslint-disable-next-line react/jsx-props-no-spreading
  const wrapper = mount(<QueryListItem {...props} />);
  return { props, wrapper };
};

describe('QueryListItem', () => {
  describe('render', () => {
    it('should render without errors', () => {
      expect(() => {
        setup();
      }).not.toThrow();
    });

    it('should render one query list item', () => {
      const { wrapper } = setup();
      const expected = 1;
      const actual = wrapper.find('.query-list-item').length;

      expect(actual).toEqual(expected);
    });

    it('should render the query name', () => {
      const { wrapper, props } = setup();
      const expected = props.name;
      const actual = wrapper.find('.query-list-item-name').text();

      expect(actual).toEqual(expected);
    });

    it('should not render the expanded content', () => {
      const { wrapper } = setup();
      const expected = 0;
      const actual = wrapper.find('.query-list-expanded-content').length;

      expect(actual).toEqual(expected);
    });

    describe('when item is expanded', () => {
      let wrapper;

      beforeAll(() => {
        ({ wrapper } = setup());

        wrapper.find('.query-list-header').simulate('click');
      });

      it('should show the query label', () => {
        const expected = 1;
        const actual = wrapper.find('.query-list-query-label').length;

        expect(actual).toEqual(expected);
      });

      it('should show the query content', () => {
        const expected = 1;
        const actual = wrapper.find('.query-list-query-content').length;

        expect(actual).toEqual(expected);
      });
    });
  });

  describe('lifetime', () => {
    describe('when clicked on the item', () => {
      it('should render the expanded content', () => {
        const { wrapper, props } = setup();
        const expected = 1;

        wrapper.find('.query-list-header').simulate('click');
        const actual = wrapper.find('.query-list-expanded-content').length;

        expect(actual).toEqual(expected);
      });

      describe('when clicking again', () => {
        it('should hide the expanded content', () => {
          const { wrapper, props } = setup();
          const expected = 0;

          wrapper.find('.query-list-header').simulate('click');
          wrapper.find('.query-list-header').simulate('click');
          const actual = wrapper.find('.query-list-expanded-content').length;

          expect(actual).toEqual(expected);
        });
      });
    });
  });
});
