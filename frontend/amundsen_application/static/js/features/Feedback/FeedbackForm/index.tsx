// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import LoadingSpinner from 'components/LoadingSpinner';

import {
  ResetFeedbackRequest,
  SubmitFeedbackRequest,
} from 'ducks/feedback/types';

import { SendingState } from 'interfaces';

import { SUBMIT_FAILURE_MESSAGE, SUBMIT_SUCCESS_MESSAGE } from '../constants';

import '../styles.scss';

export interface StateFromProps {
  sendState: SendingState;
}

export interface DispatchFromProps {
  submitFeedback: (data: FormData) => SubmitFeedbackRequest;
  resetFeedback: () => ResetFeedbackRequest;
}

export type FeedbackFormProps = StateFromProps & DispatchFromProps;

abstract class AbstractFeedbackForm extends React.Component<FeedbackFormProps> {
  public static defaultProps: Partial<FeedbackFormProps> = {};

  static FORM_ID = 'feedback-form';

  submitForm = (event) => {
    event.preventDefault();
    const form = document.getElementById(
      AbstractFeedbackForm.FORM_ID
    ) as HTMLFormElement;
    const formData = new FormData(form);
    this.props.submitFeedback(formData);
  };

  render() {
    if (this.props.sendState === SendingState.WAITING) {
      return <LoadingSpinner />;
    }
    if (this.props.sendState === SendingState.COMPLETE) {
      return <div className="status-message">{SUBMIT_SUCCESS_MESSAGE}</div>;
    }
    if (this.props.sendState === SendingState.ERROR) {
      return <div className="status-message">{SUBMIT_FAILURE_MESSAGE}</div>;
    }
    return this.renderCustom();
  }

  abstract renderCustom();
}

export default AbstractFeedbackForm;
