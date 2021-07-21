// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';

import { GlobalState } from 'ducks/rootReducer';
import {
  getFeatureDescription,
  updateFeatureDescription,
} from 'ducks/feature/reducer';

import EditableText, {
  ComponentProps,
  DispatchFromProps,
  StateFromProps,
} from 'components/EditableText';

export const mapStateToProps = (state: GlobalState) => ({
  refreshValue: state.feature.feature.description,
});

export const mapDispatchToProps = (dispatch: any) =>
  bindActionCreators(
    {
      getLatestValue: getFeatureDescription,
      onSubmitValue: updateFeatureDescription,
    },
    dispatch
  );

export default connect<StateFromProps, DispatchFromProps, ComponentProps>(
  mapStateToProps,
  mapDispatchToProps
)(EditableText);
