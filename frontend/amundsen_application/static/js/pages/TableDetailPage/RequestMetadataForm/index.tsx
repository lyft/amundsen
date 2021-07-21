// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';

import {
  NotificationType,
  RequestMetadataType,
  SendNotificationOptions,
  SendingState,
  TableMetadata,
} from 'interfaces';

import FlashMessage from 'components/FlashMessage';
import { ImageIconType } from 'interfaces/Enums';

import { GlobalState } from 'ducks/rootReducer';

import {
  CloseRequestAction,
  SubmitNotificationRequest,
} from 'ducks/notification/types';
import {
  closeRequestDescriptionDialog,
  submitNotification,
} from 'ducks/notification/reducer';
import * as Constants from './constants';

import './styles.scss';

interface StateFromProps {
  columnName?: string;
  requestMetadataType?: RequestMetadataType;
  userEmail: string;
  tableMetadata: TableMetadata;
  tableOwners: string[];
  requestIsOpen: boolean;
  sendState: SendingState;
}

export interface DispatchFromProps {
  submitNotification: (
    recipients: string[],
    sender: string,
    notificationType: NotificationType,
    options?: SendNotificationOptions
  ) => SubmitNotificationRequest;
  closeRequestDescriptionDialog: () => CloseRequestAction;
}

export type RequestMetadataProps = StateFromProps & DispatchFromProps;

interface RequestMetadataState {}

export class RequestMetadataForm extends React.Component<
  RequestMetadataProps,
  RequestMetadataState
> {
  public static defaultProps: Partial<RequestMetadataProps> = {};

  componentWillUnmount = () => {
    this.props.closeRequestDescriptionDialog();
  };

  closeDialog = () => {
    this.props.closeRequestDescriptionDialog();
  };

  getFlashMessageString = (): string => {
    switch (this.props.sendState) {
      case SendingState.COMPLETE:
        return Constants.SEND_SUCCESS_MESSAGE;
      case SendingState.ERROR:
        return Constants.SEND_FAILURE_MESSAGE;
      case SendingState.WAITING:
        return Constants.SEND_INPROGRESS_MESSAGE;
      default:
        return '';
    }
  };

  renderFlashMessage = () => (
    <FlashMessage
      iconClass={ImageIconType.MAIL}
      message={this.getFlashMessageString()}
      onClose={this.closeDialog}
    />
  );

  extractDataFromForm = () => {
    const form = document.getElementById('RequestForm') as HTMLFormElement;
    const formData = new FormData(form);
    const recipientString = formData.get('recipients') as string;

    return {
      comment: formData.get('comment') as string,
      fieldsRequested: formData.get('column-description') === 'on',
      descriptionRequested: formData.get('table-description') === 'on',
      sender: formData.get('sender') as string,
      recipients: recipientString.split(
        Constants.RECIPIENT_LIST_DELIMETER.trim()
      ),
    };
  };

  submitNotification = (event) => {
    event.preventDefault();
    const {
      comment,
      fieldsRequested,
      descriptionRequested,
      sender,
      recipients,
    } = this.extractDataFromForm();
    const { submitNotification, tableMetadata } = this.props;
    const { cluster, database, schema, name } = tableMetadata;

    submitNotification(
      recipients,
      sender,
      NotificationType.METADATA_REQUESTED,
      {
        comment,
        resource_name: `${schema}.${name}`,
        resource_path: `/table_detail/${cluster}/${database}/${schema}/${name}`,
        description_requested: descriptionRequested,
        fields_requested: fieldsRequested,
      }
    );
  };

  render() {
    const {
      columnName,
      requestIsOpen,
      requestMetadataType,
      sendState,
      tableOwners,
      userEmail,
    } = this.props;
    const tableDescriptionNeeded =
      requestMetadataType === RequestMetadataType.TABLE_DESCRIPTION;
    const colDescriptionNeeded =
      requestMetadataType === RequestMetadataType.COLUMN_DESCRIPTION;
    const defaultComment = columnName
      ? `${Constants.COLUMN_REQUESTED_COMMENT_PREFIX}${columnName}`
      : '';

    if (sendState !== SendingState.IDLE) {
      return (
        <div className="request-component">{this.renderFlashMessage()}</div>
      );
    }
    if (!requestIsOpen) {
      return null;
    }
    return (
      <div className="request-component expanded">
        <div id="request-metadata-title" className="form-group request-header">
          <h3 className="title">{Constants.TITLE_TEXT}</h3>
          <button
            type="button"
            className="btn btn-close"
            onClick={this.closeDialog}
          >
            <span className="sr-only">{Constants.CLOSE}</span>
          </button>
        </div>
        <form onSubmit={this.submitNotification} id="RequestForm">
          <div id="sender-form-group" className="form-group">
            <label>{Constants.FROM_LABEL}</label>
            <input
              type="email"
              autoComplete="off"
              name="sender"
              className="form-control"
              required
              value={userEmail}
              readOnly
            />
          </div>
          <div id="recipients-form-group" className="form-group">
            <label>{Constants.TO_LABEL}</label>
            <input
              type="text"
              autoComplete="off"
              name="recipients"
              className="form-control"
              required
              multiple
              defaultValue={tableOwners.join(
                Constants.RECIPIENT_LIST_DELIMETER
              )}
            />
          </div>
          <div id="request-type-form-group" className="form-group">
            <label>{Constants.REQUEST_TYPE}</label>
            <label className="select-label">
              <input
                type="checkbox"
                name="table-description"
                defaultChecked={tableDescriptionNeeded}
              />
              {Constants.TABLE_DESCRIPTION}
            </label>
            <label className="select-label">
              <input
                type="checkbox"
                name="column-description"
                defaultChecked={colDescriptionNeeded}
              />
              {Constants.COLUMN_DESCRIPTIONS}
            </label>
          </div>
          <div id="additional-comments-form-group" className="form-group">
            <label>{Constants.ADDITIONAL_DETAILS}</label>
            <textarea
              className="form-control"
              name="comment"
              placeholder={
                colDescriptionNeeded
                  ? Constants.COMMENT_PLACEHOLDER_COLUMN
                  : Constants.COMMENT_PLACEHOLDER_DEFAULT
              }
              required={colDescriptionNeeded}
              rows={8}
              maxLength={2000}
              defaultValue={defaultComment}
            />
          </div>
          <button
            id="submit-request-button"
            className="btn btn-primary submit-request-button"
            type="submit"
          >
            <img className="icon icon-send" alt="" />
            {Constants.SEND_BUTTON}
          </button>
        </form>
      </div>
    );
  }
}

export const mapStateToProps = (state: GlobalState) => {
  const userEmail = state.user.loggedInUser.email;
  const {
    columnName,
    requestMetadataType,
    requestIsOpen,
    sendState,
  } = state.notification;
  const ownerObj = state.tableMetadata.tableOwners.owners;
  const mappedProps = {
    userEmail,
    requestIsOpen,
    sendState,
    tableMetadata: state.tableMetadata.tableData,
    tableOwners: Object.keys(ownerObj),
  };
  if (columnName) {
    // eslint-disable-next-line @typescript-eslint/dot-notation
    mappedProps['columnName'] = columnName;
  }
  if (requestMetadataType) {
    // eslint-disable-next-line @typescript-eslint/dot-notation
    mappedProps['requestMetadataType'] = requestMetadataType;
  }
  return mappedProps;
};

export const mapDispatchToProps = (dispatch: any) =>
  bindActionCreators(
    { submitNotification, closeRequestDescriptionDialog },
    dispatch
  );

export default connect<StateFromProps, DispatchFromProps>(
  mapStateToProps,
  mapDispatchToProps
)(RequestMetadataForm);
