export enum SubmitFeedback {
  REQUEST = 'amundsen/feedback/SUBMIT_FEEDBACK_REQUEST',
  SUCCESS = 'amundsen/feedback/SUBMIT_FEEDBACK_SUCCESS',
  FAILURE = 'amundsen/feedback/SUBMIT_FEEDBACK_FAILURE',
}
export interface SubmitFeedbackRequest {
  type: SubmitFeedback.REQUEST;
  payload: {
    data: FormData;
  };
}
export interface SubmitFeedbackResponse {
  type: SubmitFeedback.SUCCESS | SubmitFeedback.FAILURE;
}

export enum ResetFeedback {
  REQUEST = 'amundsen/feedback/RESET_FEEDBACK_REQUEST',
}
export interface ResetFeedbackRequest {
  type: ResetFeedback.REQUEST;
}
