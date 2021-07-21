// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';

import { GlobalState } from 'ducks/rootReducer';
import {
  getTableDescription,
  updateTableDescription,
} from 'ducks/tableMetadata/reducer';

import EditableText, {
  ComponentProps,
  DispatchFromProps,
  StateFromProps,
} from 'components/EditableText';

export const mapStateToProps = (state: GlobalState) => ({
  refreshValue: state.tableMetadata.tableData.description,
});

export const mapDispatchToProps = (dispatch: any) =>
  bindActionCreators(
    {
      getLatestValue: getTableDescription,
      onSubmitValue: updateTableDescription,
    },
    dispatch
  );

export default connect<StateFromProps, DispatchFromProps, ComponentProps>(
  mapStateToProps,
  mapDispatchToProps
)(EditableText);
