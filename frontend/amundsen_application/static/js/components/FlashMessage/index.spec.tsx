// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';

import { shallow } from 'enzyme';

import { ImageIconType } from 'interfaces/Enums';
import FlashMessage, { FlashMessageProps } from '.';

describe('FlashMessage', () => {
  const setup = (propOverrides?: Partial<FlashMessageProps>) => {
    const props: FlashMessageProps = {
      iconClass: null,
      message: 'Test',
      onClose: jest.fn(),
      ...propOverrides,
    };
    // eslint-disable-next-line react/jsx-props-no-spreading
    const wrapper = shallow(<FlashMessage {...props} />);

    return { props, wrapper };
  };

  describe('render', () => {
    let props: FlashMessageProps;
    let wrapper;

    beforeAll(() => {
      ({ props, wrapper } = setup());
    });

    describe('iconClass logic', () => {
      it('if no iconClass, does not render img', () => {
        const expected = 0;
        const actual = wrapper.find('img').length;

        expect(actual).toEqual(expected);
      });

      it('if iconClass, renders img with correct className', () => {
        const testClass = ImageIconType.MAIL;
        const { wrapper } = setup({ iconClass: testClass });

        expect(wrapper.find('img').props()).toMatchObject({
          className: `icon ${testClass}`,
        });
      });
    });

    it('renders correct message text', () => {
      const expected = props.message;
      const actual = wrapper.find('.message').text();

      expect(actual).toEqual(expected);
    });

    it('renders correct button', () => {
      const expected = props.onClose;
      const actual = wrapper.find('button.btn.btn-close').props().onClick;

      expect(actual).toEqual(expected);
    });
  });
});
