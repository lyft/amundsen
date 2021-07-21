// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import Linkify from 'react-linkify';
import { Modal } from 'react-bootstrap';

import ShimmeringDashboardLoader from '../ShimmeringDashboardLoader';

import * as Constants from './constants';
import './styles.scss';

export interface ImagePreviewProps {
  uri: string;
  redirectUrl: string;
}

interface ImagePreviewState {
  isLoading: boolean;
  hasError: boolean;
  isModalVisible: boolean;
}

type PreviewModalProps = {
  imageSrc: string;
  onClose: () => void;
};

const PreviewModal = ({ imageSrc, onClose }: PreviewModalProps) => {
  const [show, setShow] = React.useState(true);
  const handleClose = () => {
    setShow(false);
    onClose();
  };

  return (
    <Modal
      show={show}
      onHide={handleClose}
      scrollable="true"
      className="dashboard-preview-modal"
    >
      <Modal.Header closeButton>
        <Modal.Title className="text-center">
          {Constants.DASHBOARD_PREVIEW_MODAL_TITLE}
        </Modal.Title>
      </Modal.Header>
      <Modal.Body>
        <img src={imageSrc} height="auto" width="100%" alt="" />
      </Modal.Body>
    </Modal>
  );
};

export class ImagePreview extends React.Component<
  ImagePreviewProps,
  ImagePreviewState
> {
  state = {
    isLoading: true,
    hasError: false,
    isModalVisible: false,
  };

  onSuccess = () => {
    this.setState({ isLoading: false, hasError: false });
  };

  onError = (e: React.SyntheticEvent<HTMLImageElement>) => {
    this.setState({ isLoading: false, hasError: true });
  };

  handlePreviewButton = () => {
    this.setState({ isModalVisible: true });
  };

  handlePreviewModalClose = () => {
    this.setState({ isModalVisible: false });
  };

  render = () => {
    const { uri, redirectUrl } = this.props;
    const { isLoading, hasError, isModalVisible } = this.state;
    const imageSrc = `${Constants.PREVIEW_BASE}/${uri}/${Constants.PREVIEW_END}`;

    return (
      <div className="image-preview">
        {isLoading && <ShimmeringDashboardLoader />}
        {!hasError && (
          <button
            className="preview-button"
            type="button"
            onClick={this.handlePreviewButton}
          >
            <span className="sr-only">{Constants.PREVIEW_BUTTON_TEXT}</span>
            <img
              className="preview"
              style={
                isLoading ? { visibility: 'hidden' } : { visibility: 'visible' }
              }
              src={imageSrc}
              onLoad={this.onSuccess}
              onError={this.onError}
              height="auto"
              width="100%"
              alt=""
            />
          </button>
        )}
        {hasError && (
          <Linkify
            className="body-placeholder"
            properties={{ target: '_blank', rel: 'noopener noreferrer' }}
          >
            {`${Constants.ERROR_MESSAGE} ${redirectUrl}`}
          </Linkify>
        )}
        {isModalVisible && (
          <PreviewModal
            imageSrc={imageSrc}
            onClose={this.handlePreviewModalClose}
          />
        )}
      </div>
    );
  };
}

export default ImagePreview;
