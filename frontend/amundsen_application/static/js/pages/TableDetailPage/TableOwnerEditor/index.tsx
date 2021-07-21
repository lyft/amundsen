// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';

import { GlobalState } from 'ducks/rootReducer';
import { updateTableOwner } from 'ducks/tableMetadata/owners/reducer';

import OwnerEditor, {
  ComponentProps,
  DispatchFromProps,
  StateFromProps,
} from 'components/OwnerEditor';

import { indexUsersEnabled } from 'config/config-utils';

export const mapStateToProps = (state: GlobalState) => {
  const ownerObj = state.tableMetadata.tableOwners.owners;
  const items = Object.keys(ownerObj).reduce((obj, ownerId) => {
    const { profile_url, user_id, display_name } = ownerObj[ownerId];
    let profileLink = profile_url;
    let isExternalLink = true;
    if (indexUsersEnabled()) {
      isExternalLink = false;
      profileLink = `/user/${user_id}?source=owned_by`;
    }
    obj[ownerId] = {
      label: display_name,
      link: profileLink,
      isExternal: isExternalLink,
    };
    return obj;
  }, {});

  return {
    isLoading: state.tableMetadata.tableOwners.isLoading,
    itemProps: items,
  };
};

export const mapDispatchToProps = (dispatch: any) =>
  bindActionCreators({ onUpdateList: updateTableOwner }, dispatch);

export default connect<StateFromProps, DispatchFromProps, ComponentProps>(
  mapStateToProps,
  mapDispatchToProps
)(OwnerEditor);
