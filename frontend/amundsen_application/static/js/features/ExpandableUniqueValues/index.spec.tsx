// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { mount } from 'enzyme';
import { Modal } from 'react-bootstrap';

import UniqueValuesModal from './UniqueValuesModal';

import ExpandableUniqueValues, {
  ExpandableUniqueValuesProps,
  NUMBER_OF_VALUES_SUMMARY,
} from '.';
import TestDataBuilder from './testDataBuilder';

const dataBuilder = new TestDataBuilder();

const setup = (propOverrides?: Partial<ExpandableUniqueValuesProps>) => {
  const props = {
    uniqueValues: [],
    ...propOverrides,
  };
  const wrapper = mount<typeof ExpandableUniqueValues>(
    // eslint-disable-next-line react/jsx-props-no-spreading
    <ExpandableUniqueValues {...props} />
  );

  return { props, wrapper };
};

describe('ExpandableUniqueValues', () => {
  describe('render', () => {
    describe('when stats are empty', () => {
      const { uniqueValues } = dataBuilder.withEmptyUniqueValues().build();

      it('does not render the component', () => {
        const { wrapper } = setup({ uniqueValues });
        const expected = uniqueValues.length;
        const actual = wrapper.find('.unique-values').length;

        expect(actual).toEqual(expected);
      });
    });

    describe('when one unique value is passed', () => {
      const { uniqueValues } = dataBuilder.withOneUniqueValue().build();

      it('renders the component', () => {
        const { wrapper } = setup({ uniqueValues });
        const expected = 1;
        const actual = wrapper.find('.unique-values').length;

        expect(actual).toEqual(expected);
      });

      it('renders uique value title', () => {
        const { wrapper } = setup({ uniqueValues });
        const expected = 1;
        const actual = wrapper.find('.unique-values-title').length;

        expect(actual).toEqual(expected);
      });

      it('renders uique values list', () => {
        const { wrapper } = setup({ uniqueValues });
        const expected = 1;
        const actual = wrapper.find('.unique-values-list').length;

        expect(actual).toEqual(expected);
      });

      it('renders one unique value', () => {
        const { wrapper } = setup({ uniqueValues });
        const expected = uniqueValues.length;
        const actual = wrapper.find('.unique-value-item').length;

        expect(actual).toEqual(expected);
      });

      it('renders a link to see them all', () => {
        const { wrapper } = setup({ uniqueValues });
        const expected = 1;
        const actual = wrapper.find('.unique-values-expand-link').length;

        expect(actual).toEqual(expected);
      });
    });

    describe(`when the unique values are less than the limit of ${NUMBER_OF_VALUES_SUMMARY}`, () => {
      const { uniqueValues } = dataBuilder
        .withVariableNumberOfUniqueValues(NUMBER_OF_VALUES_SUMMARY - 1)
        .build();

      it(`renders ${
        NUMBER_OF_VALUES_SUMMARY - 1
      } unique values in the summary`, () => {
        const { wrapper } = setup({ uniqueValues });
        const expected = NUMBER_OF_VALUES_SUMMARY - 1;
        const actual = wrapper.find('.unique-value-item').length;

        expect(actual).toEqual(expected);
      });
    });

    describe(`when the unique values are over the limit of ${NUMBER_OF_VALUES_SUMMARY}`, () => {
      const { uniqueValues } = dataBuilder
        .withVariableNumberOfUniqueValues(NUMBER_OF_VALUES_SUMMARY + 1)
        .build();

      it(`renders ${NUMBER_OF_VALUES_SUMMARY} unique values in the summary`, () => {
        const { wrapper } = setup({ uniqueValues });
        const expected = NUMBER_OF_VALUES_SUMMARY;
        const actual = wrapper.find('.unique-value-item').length;

        expect(actual).toEqual(expected);
      });
    });
  });

  describe('lifecycle', () => {
    describe('when clicking in "see all"', () => {
      const { uniqueValues } = dataBuilder.withOneUniqueValue().build();

      it('renders the modal', () => {
        const { wrapper } = setup({ uniqueValues });
        const expected = true;

        wrapper.find('.unique-values-expand-link').simulate('click');

        const actual = wrapper.find(UniqueValuesModal).props().shouldShow;

        expect(actual).toEqual(expected);
      });
    });

    describe('when clicking in the "x" button of the modal', () => {
      const { uniqueValues } = dataBuilder.withOneUniqueValue().build();

      it('hides the modal', () => {
        const { wrapper } = setup({ uniqueValues });
        const expected = false;

        // We open the modan and then close it
        wrapper.find('.unique-values-expand-link').simulate('click');
        // @ts-ignore
        wrapper.find(Modal).invoke('onHide')();

        const actual = wrapper.find(UniqueValuesModal).props().shouldShow;

        expect(actual).toEqual(expected);
      });
    });
  });
});
