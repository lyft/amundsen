// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import * as Avatar from 'react-avatar';

import { shallow } from 'enzyme';

import AvatarLabel, { AvatarLabelProps } from '.';

describe('AvatarLabel', () => {
  const setup = (propOverrides?: Partial<AvatarLabelProps>) => {
    const props: AvatarLabelProps = {
      ...propOverrides,
    };
    // eslint-disable-next-line react/jsx-props-no-spreading
    const wrapper = shallow(<AvatarLabel {...props} />);
    return {
      props,
      wrapper,
    };
  };

  describe('render', () => {
    let props: AvatarLabelProps;
    let wrapper;
    beforeAll(() => {
      const setupResult = setup({
        avatarClass: 'test',
        label: 'testLabel',
        labelClass: 'test',
        src: 'testSrc',
      });
      props = setupResult.props;
      wrapper = setupResult.wrapper;
    });
    it('renders Avatar with correct props', () => {
      expect(wrapper.find(Avatar).props()).toMatchObject({
        className: props.avatarClass,
        name: props.label,
        src: props.src,
        size: 24,
        round: true,
      });
    });

    describe('renders label', () => {
      let element;
      beforeAll(() => {
        element = wrapper.find('.avatar-label');
      });
      it('with correct text', () => {
        expect(element.text()).toEqual(props.label);
      });

      it('with correct style', () => {
        expect(element.props().className).toBe(
          `avatar-label body-2 ${props.labelClass}`
        );
      });
    });
  });
});
