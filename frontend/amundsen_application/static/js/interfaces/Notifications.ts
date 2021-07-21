export enum NotificationType {
  OWNER_ADDED = 'owner_added',
  OWNER_REMOVED = 'owner_removed',
  METADATA_EDITED = 'metadata_edited',
  METADATA_REQUESTED = 'metadata_requested',
  DATA_ISSUE_REPORTED = 'data_issue_reported',
}

export enum RequestMetadataType {
  COLUMN_DESCRIPTION = 'columnDescriptionRequested',
  TABLE_DESCRIPTION = 'tableDescriptionRequested',
}

export interface SendNotificationOptions {
  resource_name: string;
  resource_path: string;
  description_requested?: boolean;
  fields_requested?: boolean;
  comment?: string;
  data_issue_url?: string;
}

export interface NotificationPayload {
  recipients: string[];
  sender: string;
  notificationType: NotificationType;
  options: SendNotificationOptions;
}
