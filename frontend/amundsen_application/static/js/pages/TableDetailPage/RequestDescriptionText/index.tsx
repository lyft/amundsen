// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';

import { connect } from 'react-redux';
import { OpenRequestAction } from 'ducks/notification/types';
import { openRequestDescriptionDialog } from 'ducks/notification/reducer';
import { bindActionCreators } from 'redux';
import { RequestMetadataType } from 'interfaces';
import { REQUEST_DESCRIPTION } from './constants';

export interface DispatchFromProps {
  openRequestDescriptionDialog: (
    requestMetadataType: RequestMetadataType
  ) => OpenRequestAction;
}

export type RequestDescriptionTextProps = DispatchFromProps;

interface RequestDescriptionTextState {}

export class RequestDescriptionText extends React.Component<
  RequestDescriptionTextProps,
  RequestDescriptionTextState
> {
  public static defaultProps: Partial<RequestDescriptionTextProps> = {};

  openRequest = () => {
    this.props.openRequestDescriptionDialog(
      RequestMetadataType.TABLE_DESCRIPTION
    );
  };

  render() {
    return (
      <a
        className="request-description body-link"
        href="JavaScript:void(0)"
        onClick={this.openRequest}
      >
        {REQUEST_DESCRIPTION}
      </a>
    );
  }
}

export const mapDispatchToProps = (dispatch: any) =>
  bindActionCreators({ openRequestDescriptionDialog }, dispatch);

export default connect<{}, DispatchFromProps>(
  null,
  mapDispatchToProps
)(RequestDescriptionText);
