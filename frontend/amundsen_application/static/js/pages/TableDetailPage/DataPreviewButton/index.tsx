// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { Modal, OverlayTrigger, Popover } from 'react-bootstrap';
import Linkify from 'react-linkify';
import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';

import { getPreviewData } from 'ducks/tableMetadata/reducer';
import { GlobalState } from 'ducks/rootReducer';
import { PreviewDataTable } from 'features/PreviewData';
import {
  PreviewData,
  TablePreviewQueryParams,
  TableMetadata,
} from 'interfaces';
import { logClick } from 'utils/analytics';

// TODO: Use css-modules instead of 'import'
import './styles.scss';

enum LoadingStatus {
  ERROR = 'error',
  FORBIDDEN = 'forbidden',
  LOADING = 'loading',
  SUCCESS = 'success',
  UNAUTHORIZED = 'unauthorized',
  UNAVAILABLE = 'unavailable',
}

export interface StateFromProps {
  previewData: PreviewData;
  status: LoadingStatus;
  tableData: TableMetadata;
}

export interface DispatchFromProps {
  getPreviewData: (queryParams: TablePreviewQueryParams) => void;
}

export interface ComponentProps {
  modalTitle: string;
}

type DataPreviewButtonProps = StateFromProps &
  DispatchFromProps &
  ComponentProps;

interface DataPreviewButtonState {
  showModal: boolean;
}

export function getStatusFromCode(httpErrorCode: number | null) {
  switch (httpErrorCode) {
    case null:
      return LoadingStatus.LOADING;
    case 200:
      // ok
      return LoadingStatus.SUCCESS;
    case 401:
      // user is unauthorized to see content
      return LoadingStatus.UNAUTHORIZED;
    case 403:
      // user is authorized, but forbidden from resource
      return LoadingStatus.FORBIDDEN;
    case 501:
      // preview client was not configured
      return LoadingStatus.UNAVAILABLE;
    default:
      // default to generic error
      return LoadingStatus.ERROR;
  }
}

export class DataPreviewButton extends React.Component<
  DataPreviewButtonProps,
  DataPreviewButtonState
> {
  constructor(props) {
    super(props);

    this.state = {
      showModal: false,
    };
  }

  componentDidMount() {
    const { tableData } = this.props;
    this.props.getPreviewData({
      database: tableData.database,
      schema: tableData.schema,
      tableName: tableData.name,
      cluster: tableData.cluster,
    });
  }

  handleClose = () => {
    this.setState({ showModal: false });
  };

  handleClick = (e) => {
    logClick(e);
    this.setState({ showModal: true });
  };

  renderModalBody() {
    const { previewData } = this.props;

    if (this.props.status === LoadingStatus.SUCCESS) {
      return <PreviewDataTable isLoading={false} previewData={previewData} />;
    }

    if (this.props.status === LoadingStatus.UNAUTHORIZED) {
      return (
        <div>
          <Linkify>{previewData.error_text}</Linkify>
        </div>
      );
    }

    return null;
  }

  renderPreviewButton() {
    const { previewData } = this.props;

    // Based on the state, the preview button will show different things.
    let buttonText = 'Loading...';
    let disabled = true;
    let iconClass = 'icon-loading';
    let popoverText = 'The data preview is loading';

    // TODO: Setting hardcoded strings that should be customizable/translatable
    switch (this.props.status) {
      case LoadingStatus.SUCCESS:
      case LoadingStatus.UNAUTHORIZED:
        buttonText = 'Preview';
        iconClass = 'icon-preview';
        disabled = false;
        break;
      case LoadingStatus.FORBIDDEN:
        buttonText = 'Preview';
        iconClass = 'icon-preview';
        popoverText =
          previewData.error_text || 'User is forbidden to preview this data';
        break;
      case LoadingStatus.UNAVAILABLE:
        buttonText = 'Preview';
        iconClass = 'icon-preview';
        popoverText = 'This feature has not been configured by your service';
        break;
      case LoadingStatus.ERROR:
        buttonText = 'Preview';
        iconClass = 'icon-preview';
        popoverText =
          previewData.error_text ||
          'An internal server error has occurred, please contact service admin';
        break;
      default:
        break;
    }

    const previewButton = (
      <button
        id="data-preview-button"
        className="btn btn-default btn-lg"
        disabled={disabled}
        onClick={this.handleClick}
      >
        {buttonText}
      </button>
    );

    if (!disabled) {
      return previewButton;
    }

    // when button is disabled, render button with Popover
    const popoverHover = (
      <Popover id="popover-trigger-hover">{popoverText}</Popover>
    );
    return (
      <OverlayTrigger
        trigger={['hover', 'focus']}
        placement="top"
        delayHide={200}
        overlay={popoverHover}
      >
        {/* Disabled buttons don't trigger hover/focus events so we need a wrapper */}
        <div className="overlay-trigger">{previewButton}</div>
      </OverlayTrigger>
    );
  }

  render() {
    return (
      <>
        {this.renderPreviewButton()}
        <Modal show={this.state.showModal} onHide={this.handleClose}>
          <Modal.Header className="text-center" closeButton>
            <Modal.Title>{this.props.modalTitle}</Modal.Title>
          </Modal.Header>
          <Modal.Body>{this.renderModalBody()}</Modal.Body>
        </Modal>
      </>
    );
  }
}

export const mapStateToProps = (state: GlobalState) => ({
  previewData: state.tableMetadata.preview.data,
  status: getStatusFromCode(state.tableMetadata.preview.status),
  tableData: state.tableMetadata.tableData,
});

export const mapDispatchToProps = (dispatch: any) =>
  bindActionCreators({ getPreviewData }, dispatch);

export default connect<StateFromProps, DispatchFromProps, ComponentProps>(
  mapStateToProps,
  mapDispatchToProps
)(DataPreviewButton);
