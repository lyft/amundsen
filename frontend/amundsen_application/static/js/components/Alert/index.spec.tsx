// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { mount } from 'enzyme';

import { NoticeSeverity } from 'config/config-types';

import Alert, { AlertProps } from '.';

const setup = (propOverrides?: Partial<AlertProps>) => {
  const props: AlertProps = {
    message: 'Test Message',
    onAction: jest.fn(),
    ...propOverrides,
  };
  // eslint-disable-next-line react/jsx-props-no-spreading
  const wrapper = mount(<Alert {...props} />);

  return {
    props,
    wrapper,
  };
};

describe('Alert', () => {
  describe('render', () => {
    it('should render an alert icon', () => {
      const { wrapper } = setup();
      const expected = 1;
      const actual = wrapper.find('.alert-triangle-svg-icon').length;

      expect(actual).toEqual(expected);
    });

    it('should render the alert message text', () => {
      const { props, wrapper } = setup();
      const expected = props.message;
      const actual = wrapper.find('.alert-message').text();

      expect(actual).toEqual(expected);
    });

    describe('when passing an action text and action handler', () => {
      it('should render the action button', () => {
        const { wrapper } = setup({ actionText: 'Action Text' });
        const expected = 1;
        const actual = wrapper.find('.btn-link').length;

        expect(actual).toEqual(expected);
      });

      it('should render the action text', () => {
        const { props, wrapper } = setup({ actionText: 'Action Text' });
        const expected = props.actionText;
        const actual = wrapper.find('.btn-link').text();

        expect(actual).toEqual(expected);
      });
    });

    describe('when passing an action text and action href', () => {
      it('should render the action link', () => {
        const { wrapper } = setup({
          actionHref: 'http://testSite.com',
          actionText: 'Action Text',
        });
        const expected = 1;
        const actual = wrapper.find('.action-link').length;

        expect(actual).toEqual(expected);
      });

      it('should render the action text', () => {
        const { props, wrapper } = setup({
          actionHref: 'http://testSite.com',
          actionText: 'Action Text',
        });
        const expected = props.actionText;
        const actual = wrapper.find('.action-link').text();

        expect(actual).toEqual(expected);
      });
    });

    describe('when passing a custom action link', () => {
      it('should render the custom action link', () => {
        const { wrapper } = setup({
          actionLink: (
            <a className="test-action-link" href="http://testSite.com">
              Custom Link
            </a>
          ),
        });
        const expected = 1;
        const actual = wrapper.find('.test-action-link').length;

        expect(actual).toEqual(expected);
      });
    });

    describe('when passing a severity', () => {
      it('should render the alert icon by default', () => {
        const { wrapper } = setup();
        const expected = 1;
        const actual = wrapper.find('.alert-triangle-svg-icon').length;

        expect(actual).toEqual(expected);
      });

      it('should render the info icon when info severity', () => {
        const { wrapper } = setup({ severity: NoticeSeverity.INFO });
        const expected = 1;
        const actual = wrapper.find('.info-svg-icon').length;

        expect(actual).toEqual(expected);
      });

      it('should render the alert icon when alert severity', () => {
        const { wrapper } = setup({ severity: NoticeSeverity.ALERT });
        const expected = 1;
        const actual = wrapper.find('.alert-triangle-svg-icon').length;

        expect(actual).toEqual(expected);
      });

      it('should render the alert icon when warning severity', () => {
        const { wrapper } = setup({ severity: NoticeSeverity.WARNING });
        const expected = 1;
        const actual = wrapper.find('.alert-triangle-svg-icon').length;

        expect(actual).toEqual(expected);
      });
    });
  });

  describe('lifetime', () => {
    describe('when clicking on the action button', () => {
      it('should call the handler', () => {
        const handlerSpy = jest.fn();
        const { wrapper } = setup({
          actionText: 'Action Text',
          onAction: handlerSpy,
        });
        const expected = 1;

        wrapper.find('button.btn-link').simulate('click');

        const actual = handlerSpy.mock.calls.length;

        expect(actual).toEqual(expected);
      });
    });
  });
});
