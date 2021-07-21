import {
  NotificationType,
  RequestMetadataType,
  SendNotificationOptions,
  SendingState,
} from 'interfaces';

import {
  SubmitNotification,
  SubmitNotificationRequest,
  SubmitNotificationResponse,
  ToggleRequest,
  CloseRequestAction,
  OpenRequestAction,
} from './types';

/* ACTIONS */
export function submitNotification(
  recipients: Array<string>,
  sender: string,
  notificationType: NotificationType,
  options?: SendNotificationOptions
): SubmitNotificationRequest {
  return {
    payload: {
      recipients,
      sender,
      notificationType,
      options,
    },
    type: SubmitNotification.REQUEST,
  };
}
export function submitNotificationFailure(): SubmitNotificationResponse {
  return {
    type: SubmitNotification.FAILURE,
  };
}
export function submitNotificationSuccess(): SubmitNotificationResponse {
  return {
    type: SubmitNotification.SUCCESS,
  };
}

export function closeRequestDescriptionDialog(): CloseRequestAction {
  return {
    type: ToggleRequest.CLOSE,
  };
}

export function openRequestDescriptionDialog(
  requestMetadataType: RequestMetadataType,
  columnName?: string
): OpenRequestAction {
  if (columnName) {
    return {
      type: ToggleRequest.OPEN,
      payload: {
        columnName,
        requestMetadataType,
      },
    };
  }
  return {
    type: ToggleRequest.OPEN,
    payload: {
      requestMetadataType,
    },
  };
}

/* REDUCER */
export interface NotificationReducerState {
  columnName?: string;
  requestMetadataType?: RequestMetadataType;
  requestIsOpen: boolean;
  sendState: SendingState;
}

const initialState: NotificationReducerState = {
  requestIsOpen: false,
  sendState: SendingState.IDLE,
};

export default function reducer(
  state: NotificationReducerState = initialState,
  action
): NotificationReducerState {
  switch (action.type) {
    case SubmitNotification.FAILURE:
      return {
        ...state,
        sendState: SendingState.ERROR,
      };
    case SubmitNotification.SUCCESS:
      return {
        ...state,
        sendState: SendingState.COMPLETE,
      };
    case SubmitNotification.REQUEST:
      return {
        ...state,
        requestIsOpen: false,
        sendState: SendingState.WAITING,
      };
    case ToggleRequest.CLOSE:
      return {
        requestIsOpen: false,
        sendState: SendingState.IDLE,
      };
    case ToggleRequest.OPEN:
      const newState = {
        requestMetadataType: (<OpenRequestAction>action).payload
          .requestMetadataType,
        requestIsOpen: true,
        sendState: SendingState.IDLE,
      };
      const { columnName } = (<OpenRequestAction>action).payload;
      if (columnName) {
        // eslint-disable-next-line @typescript-eslint/dot-notation
        newState['columnName'] = columnName;
      }
      return newState;
    default:
      return state;
  }
}
