// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';

import { GlobalState } from 'ducks/rootReducer';
import { submitFeedback, resetFeedback } from 'ducks/feedback/reducer';
import AbstractFeedbackForm, { DispatchFromProps, StateFromProps } from '..';

import {
  COMMENTS_PLACEHOLDER,
  RATING_LABEL,
  RATING_LOW_TEXT,
  RATING_HIGH_TEXT,
  SUBMIT_TEXT,
} from '../../constants';

export class RatingFeedbackForm extends AbstractFeedbackForm {
  renderCustom() {
    const ratings = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];
    const radioButtonSet = ratings.map((rating) => (
      <div className="radio-set-item" key={`value${rating}:item`}>
        <input
          type="radio"
          id={`value${rating}:input`}
          name="rating"
          value={`${rating}`}
        />
        <label id={`value${rating}:label`} htmlFor={`value${rating}:input`}>
          {rating}
        </label>
      </div>
    ));

    return (
      <form id={AbstractFeedbackForm.FORM_ID} onSubmit={this.submitForm}>
        <input type="hidden" name="feedback-type" value="NPS Rating" />
        <div className="form-group clearfix">
          <label htmlFor="rating">{RATING_LABEL}</label>
          <div>
            <div className="radio-set">{radioButtonSet}</div>
            <div>
              <div className="nps-label pull-left text-left">
                {RATING_LOW_TEXT}
              </div>
              <div className="nps-label pull-right text-right">
                {RATING_HIGH_TEXT}
              </div>
            </div>
          </div>
        </div>
        <div className="form-group">
          <label htmlFor="comment">{COMMENTS_PLACEHOLDER}</label>
          <textarea
            className="form-control form-group"
            name="comment"
            id="comment"
            form={AbstractFeedbackForm.FORM_ID}
            rows={8}
            maxLength={2000}
            placeholder={COMMENTS_PLACEHOLDER}
          />
        </div>

        <button className="btn btn-primary" type="submit">
          {SUBMIT_TEXT}
        </button>
      </form>
    );
  }
}

export const mapStateToProps = (state: GlobalState) => ({
  sendState: state.feedback.sendState,
});

export const mapDispatchToProps = (dispatch: any) =>
  bindActionCreators({ submitFeedback, resetFeedback }, dispatch);

export default connect<StateFromProps, DispatchFromProps>(
  mapStateToProps,
  mapDispatchToProps
)(RatingFeedbackForm);
