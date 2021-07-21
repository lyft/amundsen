// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';

import { ResourceType, Badge } from 'interfaces';

import { updateSearchState } from 'ducks/search/reducer';
import { UpdateSearchStateRequest } from 'ducks/search/types';
// TODO - Dedupe or rename "components/BadgeList" and "features/BadgeList" to avoid collisions
import BadgeList from 'components/BadgeList';

export interface DispatchFromProps {
  onBadgeClick: (badgeText: string) => UpdateSearchStateRequest;
}

export interface BadgeListFeatureProps {
  badges: Badge[];
}

export const mapDispatchToProps = (dispatch: any) =>
  bindActionCreators(
    {
      onBadgeClick: (badgeText: string) =>
        updateSearchState({
          filters: {
            [ResourceType.table]: { badges: badgeText },
            [ResourceType.feature]: { badges: badgeText },
          },
          submitSearch: true,
        }),
    },
    dispatch
  );

export default connect<null, DispatchFromProps, BadgeListFeatureProps>(
  null,
  mapDispatchToProps
)(BadgeList);
