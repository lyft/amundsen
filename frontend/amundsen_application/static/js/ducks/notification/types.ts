import {
  NotificationType,
  RequestMetadataType,
  SendNotificationOptions,
} from 'interfaces';

export enum SubmitNotification {
  REQUEST = 'amundsen/notification/SUBMIT_NOTIFICATION_REQUEST',
  SUCCESS = 'amundsen/notification/SUBMIT_NOTIFICATION_SUCCESS',
  FAILURE = 'amundsen/notification/SUBMIT_NOTIFICATION_FAILURE',
}

export interface SubmitNotificationRequest {
  type: SubmitNotification.REQUEST;
  payload: {
    recipients: string[];
    sender: string;
    notificationType: NotificationType;
    options?: SendNotificationOptions;
  };
}
export interface SubmitNotificationResponse {
  type: SubmitNotification.SUCCESS | SubmitNotification.FAILURE;
}

export enum ToggleRequest {
  OPEN = 'open',
  CLOSE = 'close',
}

export interface OpenRequestAction {
  type: ToggleRequest.OPEN;
  payload: {
    columnName?: string;
    requestMetadataType: RequestMetadataType;
  };
}

export interface CloseRequestAction {
  type: ToggleRequest.CLOSE;
}
