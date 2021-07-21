// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';

import { shallow } from 'enzyme';
import CheckBoxItem, { CheckBoxItemProps } from '.';

describe('CheckBoxItem', () => {
  const expectedChild = <span>I am a child</span>;
  const setup = (propOverrides?: Partial<CheckBoxItemProps>) => {
    const props: CheckBoxItemProps = {
      checked: true,
      disabled: false,
      name: 'test',
      value: 'testMethod',
      onChange: jest.fn(),
      children: <div />,
      ...propOverrides,
    };
    const wrapper = shallow(
      // eslint-disable-next-line react/jsx-props-no-spreading
      <CheckBoxItem {...props}>{expectedChild}</CheckBoxItem>
    );
    return { props, wrapper };
  };

  describe('render', () => {
    let props;
    let wrapper;

    beforeAll(() => {
      const setupResult = setup();
      props = setupResult.props;
      wrapper = setupResult.wrapper;
    });

    it('renders itself with correct class', () => {
      expect(wrapper.hasClass('checkbox')).toBe(true);
    });

    it('renders itself with correct class', () => {
      expect(wrapper.find('label').hasClass('checkbox-label')).toBe(true);
    });

    it('renders input with correct props', () => {
      const input = wrapper.find('label').children().at(0);
      expect(input.exists()).toBe(true);
      expect(input.props()).toEqual({
        type: 'checkbox',
        checked: props.checked,
        disabled: props.disabled,
        name: props.name,
        onChange: props.onChange,
        value: props.value,
      });
    });

    it('renders input with default value for checked if not provided', () => {
      const { wrapper } = setup({ checked: undefined });
      expect(wrapper.find('input').props().checked).toEqual(false);
    });

    it('renders input with default value for disabled if not provided', () => {
      const { wrapper } = setup({ disabled: undefined });
      expect(wrapper.find('input').props().disabled).toEqual(false);
    });

    it('renders expected children after input', () => {
      const labelChildren = wrapper.find('label').children();
      expect(labelChildren.at(1).contains(expectedChild)).toBe(true);
    });
  });
});
