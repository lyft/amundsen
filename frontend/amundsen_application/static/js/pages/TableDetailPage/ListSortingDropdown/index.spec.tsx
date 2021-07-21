// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { Dropdown } from 'react-bootstrap';
import { mount } from 'enzyme';

import { SortDirection } from 'interfaces';

import ListSortingDropdown, { ListSortingDropdownProps } from '.';

const DEFAULT_SORTING = {
  sort_order: {
    name: 'Table Default',
    key: 'sort_order',
    direction: SortDirection.ascending,
  },
};
const USAGE_SORTING = {
  usage: {
    name: 'Usage Count',
    key: 'usage',
    direction: SortDirection.descending,
  },
};

const setup = (propOverrides?: Partial<ListSortingDropdownProps>) => {
  const props = {
    options: {},
    ...propOverrides,
  };
  const wrapper = mount<typeof ListSortingDropdown>(
    <ListSortingDropdown {...props} />
  );

  return { props, wrapper };
};

describe('ListSortingDropdown', () => {
  describe('render', () => {
    it('renders without issues', () => {
      expect(() => {
        setup();
      }).not.toThrow();
    });

    describe('when no options are passed', () => {
      it('does not render the component', () => {
        const { wrapper } = setup();
        const expected = 0;
        const actual = wrapper.find('.list-sorting-dropdown').length;

        expect(actual).toEqual(expected);
      });
    });

    describe('when one option is passed', () => {
      it('renders a DropDown component', () => {
        const { wrapper } = setup({ options: DEFAULT_SORTING });
        const expected = 1;
        const actual = wrapper.find(Dropdown).length;

        expect(actual).toEqual(expected);
      });

      it('renders one item', () => {
        const { wrapper } = setup({ options: DEFAULT_SORTING });
        const expected = 1;
        const actual = wrapper.find('.list-sorting-dropdown .radio-label')
          .length;

        expect(actual).toEqual(expected);
      });

      it('is selected by default', () => {
        const { wrapper } = setup({ options: DEFAULT_SORTING });
        const expected = true;
        const actual = wrapper
          .find('.list-sorting-dropdown .radio-label input')
          .prop('checked');

        expect(actual).toEqual(expected);
      });
    });

    describe('when two options are passed', () => {
      it('renders a DropDown component', () => {
        const { wrapper } = setup({
          options: { ...DEFAULT_SORTING, ...USAGE_SORTING },
        });
        const expected = 1;
        const actual = wrapper.find(Dropdown).length;

        expect(actual).toEqual(expected);
      });

      it('renders two items', () => {
        const { wrapper } = setup({
          options: { ...DEFAULT_SORTING, ...USAGE_SORTING },
        });
        const expected = 2;
        const actual = wrapper.find('.list-sorting-dropdown .radio-label')
          .length;

        expect(actual).toEqual(expected);
      });

      it('selects the first one by default', () => {
        const { wrapper } = setup({
          options: { ...DEFAULT_SORTING, ...USAGE_SORTING },
        });
        const expected = true;
        const actual = wrapper
          .find('.list-sorting-dropdown .radio-label input')
          .at(0)
          .prop('checked');

        expect(actual).toEqual(expected);
      });
    });
  });

  describe('lifetime', () => {
    describe('when selecting an option', () => {
      it('should make it the selected', () => {
        const { wrapper } = setup({
          options: { ...DEFAULT_SORTING, ...USAGE_SORTING },
        });
        const expected = true;

        wrapper
          .find('.list-sorting-dropdown .radio-label input')
          .at(1)
          .simulate('change', { target: { value: 'usage' } });

        const actual = wrapper
          .find('.list-sorting-dropdown .radio-label input')
          .at(1)
          .prop('checked');

        expect(actual).toEqual(expected);
      });

      it('should call the onChange handler', () => {
        const onChangeSpy = jest.fn();
        const { wrapper } = setup({
          onChange: onChangeSpy,
          options: { ...DEFAULT_SORTING, ...USAGE_SORTING },
        });
        const expected = 1;

        wrapper
          .find('.list-sorting-dropdown .radio-label input')
          .at(1)
          .simulate('change', { target: { value: 'usage' } });

        const actual = onChangeSpy.mock.calls.length;

        expect(actual).toEqual(expected);
      });

      it('should call the onChange handler with the proper value', () => {
        const onChangeSpy = jest.fn();
        const { wrapper } = setup({
          onChange: onChangeSpy,
          options: { ...DEFAULT_SORTING, ...USAGE_SORTING },
        });
        const expected = ['usage'];

        wrapper
          .find('.list-sorting-dropdown .radio-label input')
          .at(1)
          .simulate('change', { target: { value: 'usage' } });

        const actual = onChangeSpy.mock.calls[0];

        expect(actual).toEqual(expected);
      });
    });
  });
});
