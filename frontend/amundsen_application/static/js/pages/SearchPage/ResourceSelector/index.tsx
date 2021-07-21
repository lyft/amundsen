// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';

import {
  indexDashboardsEnabled,
  indexFeaturesEnabled,
  indexUsersEnabled,
} from 'config/config-utils';
import { GlobalState } from 'ducks/rootReducer';
import { updateSearchState } from 'ducks/search/reducer';
import {
  DashboardSearchResults,
  FeatureSearchResults,
  TableSearchResults,
  UpdateSearchStateRequest,
  UserSearchResults,
} from 'ducks/search/types';
import { ResourceType } from 'interfaces/Resources';
import {
  DASHBOARD_RESOURCE_TITLE,
  FEATURE_RESOURCE_TITLE,
  TABLE_RESOURCE_TITLE,
  USER_RESOURCE_TITLE,
} from '../constants';

const RESOURCE_SELECTOR_TITLE = 'Resource';

export interface StateFromProps {
  resource: ResourceType;
  tables: TableSearchResults;
  dashboards: DashboardSearchResults;
  users: UserSearchResults;
  features: FeatureSearchResults;
}

export interface DispatchFromProps {
  setResource: (resource: ResourceType) => UpdateSearchStateRequest;
}

export type ResourceSelectorProps = StateFromProps & DispatchFromProps;

interface ResourceOptionConfig {
  type: ResourceType;
  label: string;
  count: number;
}

export class ResourceSelector extends React.Component<ResourceSelectorProps> {
  onChange = (event) => {
    this.props.setResource(event.target.value);
  };

  renderRadioOption = (option: ResourceOptionConfig, index: number) => (
    <div key={`resource-radio-item:${index}`} className="radio">
      <label className="radio-label">
        <input
          type="radio"
          name="resource"
          value={option.type}
          checked={this.props.resource === option.type}
          onChange={this.onChange}
        />
        <span className="subtitle-2">{option.label}</span>
        <span className="body-secondary-3 pull-right">{option.count}</span>
      </label>
    </div>
  );

  render = () => {
    const resourceOptions = [
      {
        type: ResourceType.table,
        label: TABLE_RESOURCE_TITLE,
        count: this.props.tables.total_results,
      },
    ];

    if (indexDashboardsEnabled()) {
      resourceOptions.push({
        type: ResourceType.dashboard,
        label: DASHBOARD_RESOURCE_TITLE,
        count: this.props.dashboards.total_results,
      });
    }

    if (indexUsersEnabled()) {
      resourceOptions.push({
        type: ResourceType.user,
        label: USER_RESOURCE_TITLE,
        count: this.props.users.total_results,
      });
    }

    if (indexFeaturesEnabled()) {
      resourceOptions.push({
        type: ResourceType.feature,
        label: FEATURE_RESOURCE_TITLE,
        count: this.props.features.total_results,
      });
    }

    return (
      <>
        <h2 className="title-2">{RESOURCE_SELECTOR_TITLE}</h2>
        {resourceOptions.map((option, index) =>
          this.renderRadioOption(option, index)
        )}
      </>
    );
  };
}

export const mapStateToProps = (state: GlobalState) => ({
  resource: state.search.resource,
  tables: state.search.tables,
  users: state.search.users,
  dashboards: state.search.dashboards,
  features: state.search.features,
});

export const mapDispatchToProps = (dispatch: any) =>
  bindActionCreators(
    {
      setResource: (resource: ResourceType) =>
        updateSearchState({ resource, updateUrl: true }),
    },
    dispatch
  );

export default connect<StateFromProps, DispatchFromProps>(
  mapStateToProps,
  mapDispatchToProps
)(ResourceSelector);
