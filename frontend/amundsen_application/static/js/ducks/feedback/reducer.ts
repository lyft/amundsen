import { SendingState } from 'interfaces';

import {
  ResetFeedback,
  ResetFeedbackRequest,
  SubmitFeedback,
  SubmitFeedbackRequest,
  SubmitFeedbackResponse,
} from './types';

/* ACTIONS */
export function submitFeedback(formData: FormData): SubmitFeedbackRequest {
  return {
    payload: {
      data: formData,
    },
    type: SubmitFeedback.REQUEST,
  };
}
export function submitFeedbackFailure(): SubmitFeedbackResponse {
  return {
    type: SubmitFeedback.FAILURE,
  };
}
export function submitFeedbackSuccess(): SubmitFeedbackResponse {
  return {
    type: SubmitFeedback.SUCCESS,
  };
}

export function resetFeedback(): ResetFeedbackRequest {
  return {
    type: ResetFeedback.REQUEST,
  };
}

/* REDUCER */
export interface FeedbackReducerState {
  sendState: SendingState;
}

const initialState: FeedbackReducerState = {
  sendState: SendingState.IDLE,
};

export default function reducer(
  state: FeedbackReducerState = initialState,
  action
): FeedbackReducerState {
  switch (action.type) {
    case SubmitFeedback.REQUEST:
      return { sendState: SendingState.WAITING };
    case SubmitFeedback.SUCCESS:
      return { sendState: SendingState.COMPLETE };
    case SubmitFeedback.FAILURE:
      return { sendState: SendingState.ERROR };
    case ResetFeedback.REQUEST:
      return { sendState: SendingState.IDLE };
    default:
      return state;
  }
}
