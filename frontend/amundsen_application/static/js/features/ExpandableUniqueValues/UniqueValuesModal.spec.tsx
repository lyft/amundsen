// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { mount } from 'enzyme';

import { Modal } from 'react-bootstrap';

import UniqueValuesModal, { UniqueValuesModalProps } from './UniqueValuesModal';
import TestDataBuilder from './testDataBuilder';

const dataBuilder = new TestDataBuilder();

const setup = (propOverrides?: Partial<UniqueValuesModalProps>) => {
  const props = {
    uniqueValues: [],
    onClose: jest.fn(),
    shouldShow: true,
    ...propOverrides,
  };
  const wrapper = mount<typeof UniqueValuesModal>(
    // eslint-disable-next-line react/jsx-props-no-spreading
    <UniqueValuesModal {...props} />
  );

  return { props, wrapper };
};

describe('UniqueValuesModal', () => {
  describe('render', () => {
    describe('when one unique value is passed', () => {
      const { uniqueValues } = dataBuilder.withOneUniqueValue().build();

      it('renders the modal', () => {
        const { wrapper } = setup({ uniqueValues });
        const expected = uniqueValues.length;
        const actual = wrapper.find(Modal).length;

        expect(actual).toEqual(expected);
      });
    });
  });

  describe('lifecycle', () => {
    describe('when calling onHide in the modal', () => {
      const { uniqueValues } = dataBuilder.withOneUniqueValue().build();

      it('calls the onClose handler', () => {
        const clickSpy = jest.fn();
        const { wrapper } = setup({ uniqueValues, onClose: clickSpy });
        const expected = 1;

        // @ts-ignore
        wrapper.find(Modal).invoke('onHide')();

        const actual = clickSpy.mock.calls.length;

        expect(actual).toEqual(expected);
      });
    });
  });
});
