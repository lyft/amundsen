// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import { connect } from 'react-redux';

import { GlobalState } from 'ducks/rootReducer';

import OwnerEditor, {
  ComponentProps,
  StateFromProps,
} from 'components/OwnerEditor';

import { getOwnerItemPropsFromUsers } from 'utils/ownerUtils';
import { bindActionCreators } from 'redux';
import { updateFeatureOwner } from 'ducks/feature/reducer';

export const FEATURE_OWNER_SOURCE = 'feature_page_owner';

export const mapStateToProps = (state: GlobalState) => ({
  isLoading: state.feature.isLoadingOwners,
  itemProps: getOwnerItemPropsFromUsers(
    state.feature.feature.owners,
    FEATURE_OWNER_SOURCE
  ),
});

export const mapDispatchToProps = (dispatch: any) =>
  bindActionCreators({ onUpdateList: updateFeatureOwner }, dispatch);

export default connect<StateFromProps, {}, ComponentProps>(
  mapStateToProps,
  mapDispatchToProps
)(OwnerEditor);
