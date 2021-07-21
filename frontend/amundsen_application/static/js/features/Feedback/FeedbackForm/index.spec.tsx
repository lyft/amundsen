// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';

import { shallow } from 'enzyme';

import LoadingSpinner from 'components/LoadingSpinner';
import { SendingState } from 'interfaces';
import { FeedbackFormProps } from '.';
import { RatingFeedbackForm } from './RatingFeedbackForm';

import { SUBMIT_FAILURE_MESSAGE, SUBMIT_SUCCESS_MESSAGE } from '../constants';

const globalAny: any = global;

const mockFormData = {
  key1: 'val1',
  key2: 'val2',
  get: jest.fn(),
};
mockFormData.get.mockImplementation((val) => mockFormData[val]);
function formDataMock() {
  this.append = jest.fn();
  return mockFormData;
}
globalAny.FormData = formDataMock;

const setup = (propOverrides?: Partial<FeedbackFormProps>) => {
  const props: FeedbackFormProps = {
    sendState: SendingState.IDLE,
    submitFeedback: jest.fn(),
    resetFeedback: jest.fn(),
    ...propOverrides,
  };
  const wrapper = shallow<RatingFeedbackForm>(
    <RatingFeedbackForm {...props} />
  );
  return { props, wrapper };
};

describe('FeedbackForm', () => {
  describe('submitForm', () => {
    it('calls submitFeedback with formData', () => {
      const { props, wrapper } = setup();

      // @ts-ignore: mocked events throw type errors
      wrapper.instance().submitForm({ preventDefault: jest.fn() });

      expect(props.submitFeedback).toHaveBeenCalledWith(mockFormData);
    });
  });

  describe('render', () => {
    it('calls renderCustom if sendState is not WAITING or COMPLETE', () => {
      const { wrapper } = setup();
      const renderCustomSpy = jest.spyOn(wrapper.instance(), 'renderCustom');

      wrapper.instance().render();

      expect(renderCustomSpy).toHaveBeenCalled();
    });

    it('renders LoadingSpinner if sendState is WAITING', () => {
      const { wrapper } = setup({ sendState: SendingState.WAITING });

      expect(wrapper.find(LoadingSpinner).exists()).toBeTruthy();
    });

    it('renders confirmation status message if sendState is COMPLETE', () => {
      const { wrapper } = setup({ sendState: SendingState.COMPLETE });

      expect(wrapper.find('div.status-message').text()).toEqual(
        SUBMIT_SUCCESS_MESSAGE
      );
    });

    it('renders failure status message if sendState is ERROR', () => {
      const { wrapper } = setup({ sendState: SendingState.ERROR });

      expect(wrapper.find('div.status-message').text()).toEqual(
        SUBMIT_FAILURE_MESSAGE
      );
    });
  });
});
