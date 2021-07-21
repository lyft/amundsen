// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';

import { GlobalState } from 'ducks/rootReducer';
import {
  getColumnDescription,
  updateColumnDescription,
} from 'ducks/tableMetadata/reducer';

import EditableText, {
  ComponentProps,
  DispatchFromProps,
  StateFromProps,
} from 'components/EditableText';

interface ContainerOwnProps {
  columnIndex: number;
}

export const mapStateToProps = (
  state: GlobalState,
  ownProps: ContainerOwnProps
) => ({
  refreshValue:
    state.tableMetadata.tableData.columns[ownProps.columnIndex].description,
});

export const mapDispatchToProps = (
  dispatch: any,
  ownProps: ContainerOwnProps
) => {
  const getLatestValue = function (onSuccess, onFailure) {
    return getColumnDescription(ownProps.columnIndex, onSuccess, onFailure);
  };
  const onSubmitValue = function (newValue, onSuccess, onFailure) {
    return updateColumnDescription(
      newValue,
      ownProps.columnIndex,
      onSuccess,
      onFailure
    );
  };

  return bindActionCreators({ getLatestValue, onSubmitValue }, dispatch);
};

export default connect<
  StateFromProps,
  DispatchFromProps,
  ComponentProps & ContainerOwnProps
>(
  mapStateToProps,
  mapDispatchToProps
)(EditableText);
