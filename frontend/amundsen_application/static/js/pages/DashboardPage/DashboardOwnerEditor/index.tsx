// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import { connect } from 'react-redux';

import { GlobalState } from 'ducks/rootReducer';

import OwnerEditor, {
  ComponentProps,
  StateFromProps,
} from 'components/OwnerEditor';

import { getOwnerItemPropsFromUsers } from 'utils/ownerUtils';

export const DASHBOARD_OWNER_SOURCE = 'dashboard_page_owner';

export const mapStateToProps = (state: GlobalState) => ({
  isLoading: false,
  itemProps: getOwnerItemPropsFromUsers(
    state.dashboard.dashboard.owners,
    DASHBOARD_OWNER_SOURCE
  ),
});

export default connect<StateFromProps, {}, ComponentProps>(
  mapStateToProps,
  {}
)(OwnerEditor);
