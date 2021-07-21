// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';

import { shallow } from 'enzyme';

import AbstractFeedbackForm, {
  FeedbackFormProps,
} from 'features/Feedback/FeedbackForm';
import { SendingState } from 'interfaces';
import {
  COMMENTS_PLACEHOLDER,
  RATING_LABEL,
  RATING_LOW_TEXT,
  RATING_HIGH_TEXT,
  SUBMIT_TEXT,
} from 'features/Feedback/constants';

import globalState from 'fixtures/globalState';
import { RatingFeedbackForm, mapDispatchToProps, mapStateToProps } from '.';

describe('RatingFeedbackForm', () => {
  const setup = () => {
    const props: FeedbackFormProps = {
      sendState: SendingState.IDLE,
      submitFeedback: jest.fn(),
      resetFeedback: jest.fn(),
    };
    return shallow(<RatingFeedbackForm {...props} />);
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
        value: 'NPS Rating',
      });
    });

    describe('renders rating form group as second child', () => {
      let ratingGroup;
      let ratingComponent;
      beforeAll(() => {
        ratingGroup = form.children().at(1);
        ratingComponent = ratingGroup.children().at(1);
      });
      it('renders correct label', () => {
        expect(ratingGroup.children().at(0).find('label').text()).toEqual(
          RATING_LABEL
        );
      });

      describe('correctly renders radioButtonSet', () => {
        let radioSet;
        let ratings;
        beforeAll(() => {
          ratings = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];
          radioSet = ratingComponent.children().at(0);
        });
        it('renders radio button input for each rating', () => {
          ratings.forEach((value, index) => {
            expect(radioSet.find('input').at(index).props()).toMatchObject({
              type: 'radio',
              id: `value${value}:input`,
              name: 'rating',
              value: `${value}`,
            });
          });
        });

        it('renders label with value for each rating', () => {
          ratings.forEach((value, index) => {
            expect(radioSet.find('label').at(index).text()).toEqual(`${value}`);
          });
        });
      });

      it('renders left nps label', () => {
        expect(
          ratingComponent
            .children()
            .at(1)
            .find('.nps-label.pull-left.text-left')
            .text()
        ).toEqual(RATING_LOW_TEXT);
      });

      it('renders right nps label', () => {
        expect(
          ratingComponent
            .children()
            .at(1)
            .find('.nps-label.pull-right.text-right')
            .text()
        ).toEqual(RATING_HIGH_TEXT);
      });
    });

    it('renders textarea with correct props as third child', () => {
      expect(form.children().at(2).find('textarea').props()).toMatchObject({
        name: 'comment',
        className: 'form-control form-group',
        form: AbstractFeedbackForm.FORM_ID,
        rows: 8,
        maxLength: 2000,
        placeholder: COMMENTS_PLACEHOLDER,
      });
    });

    it('renders submit button with correct props as fourth child', () => {
      expect(form.children().at(3).find('button').props()).toMatchObject({
        className: 'btn btn-primary',
        type: 'submit',
      });
    });

    it('renders submit button with correct text', () => {
      expect(form.children().at(3).find('button').text()).toEqual(SUBMIT_TEXT);
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
