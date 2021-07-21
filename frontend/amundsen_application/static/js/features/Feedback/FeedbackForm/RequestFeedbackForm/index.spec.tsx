// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';

import { shallow } from 'enzyme';

import AbstractFeedbackForm, {
  FeedbackFormProps,
} from 'features/Feedback/FeedbackForm';
import { SendingState } from 'interfaces';
import {
  FEATURE_SUMMARY_LABEL,
  FEATURE_SUMMARY_PLACEHOLDER,
  PROPOSITION_LABEL,
  PROPOSITION_PLACEHOLDER,
  SUBJECT_LABEL,
  SUBJECT_PLACEHOLDER,
  SUBMIT_TEXT,
} from 'features/Feedback/constants';

import globalState from 'fixtures/globalState';
import { RequestFeedbackForm, mapDispatchToProps, mapStateToProps } from '.';

describe('RequestFeedbackForm', () => {
  const setup = () => {
    const props: FeedbackFormProps = {
      sendState: SendingState.IDLE,
      submitFeedback: jest.fn(),
      resetFeedback: jest.fn(),
    };
    // eslint-disable-next-line react/jsx-props-no-spreading
    return shallow(<RequestFeedbackForm {...props} />);
  };

  it('is instance of AbstractFeedbackForm', () => {
    expect(setup().instance()).toBeInstanceOf(AbstractFeedbackForm);
  });

  describe('renderCustom', () => {
    let wrapper;
    let form;
    beforeAll(() => {
      wrapper = setup();
      form = wrapper.find('form');
    });

    it('renders form with correct props', () => {
      expect(form.props()).toMatchObject({
        id: AbstractFeedbackForm.FORM_ID,
        onSubmit: wrapper.instance().submitForm,
      });
    });

    it('renders feedback-type input as first child with correct props', () => {
      expect(form.children().at(0).find('input').props()).toMatchObject({
        type: 'hidden',
        name: 'feedback-type',
        value: 'Feature Request',
      });
    });

    describe('renders subject input as second child', () => {
      it('renders correct label', () => {
        expect(form.children().at(1).find('label').text()).toEqual(
          SUBJECT_LABEL
        );
      });

      it('renders input with correct props', () => {
        expect(form.children().at(1).find('input').props()).toMatchObject({
          type: 'text',
          name: 'subject',
          className: 'form-control',
          required: true,
          placeholder: SUBJECT_PLACEHOLDER,
        });
      });
    });

    describe('renders feature-summary input as third child', () => {
      it('renders correct label', () => {
        expect(form.children().at(2).find('label').text()).toEqual(
          FEATURE_SUMMARY_LABEL
        );
      });

      it('renders textarea with correct props', () => {
        expect(form.children().at(2).find('textarea').props()).toMatchObject({
          name: 'feature-summary',
          className: 'form-control',
          required: true,
          rows: 3,
          maxLength: 2000,
          placeholder: FEATURE_SUMMARY_PLACEHOLDER,
        });
      });
    });

    describe('renders value-prop input as fourth child', () => {
      it('renders correct label', () => {
        expect(form.children().at(3).find('label').text()).toEqual(
          PROPOSITION_LABEL
        );
      });

      it('renders textarea with correct props', () => {
        expect(form.children().at(3).find('textarea').props()).toMatchObject({
          name: 'value-prop',
          className: 'form-control',
          required: true,
          rows: 5,
          maxLength: 2000,
          placeholder: PROPOSITION_PLACEHOLDER,
        });
      });
    });

    it('renders submit button with correct props', () => {
      expect(form.find('button').props()).toMatchObject({
        className: 'btn btn-primary',
        type: 'submit',
      });
    });

    it('renders submit button with correct text', () => {
      expect(form.find('button').text()).toEqual(SUBMIT_TEXT);
    });
  });
});

describe('mapDispatchToProps', () => {
  let dispatch;
  let result;
  beforeAll(() => {
    dispatch = jest.fn(() => Promise.resolve());
    result = mapDispatchToProps(dispatch);
  });

  it('sets submitFeedback on the props', () => {
    expect(result.submitFeedback).toBeInstanceOf(Function);
  });

  it('sets resetFeedback on the props', () => {
    expect(result.resetFeedback).toBeInstanceOf(Function);
  });
});

describe('mapStateToProps', () => {
  let result;
  beforeAll(() => {
    result = mapStateToProps(globalState);
  });

  it('sets sendState on the props', () => {
    expect(result.sendState).toEqual(globalState.feedback.sendState);
  });
});
