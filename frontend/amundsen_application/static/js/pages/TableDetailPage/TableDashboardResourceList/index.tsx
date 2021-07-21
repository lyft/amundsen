// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { connect } from 'react-redux';

import ResourceList from 'components/ResourceList';
import ShimmeringResourceLoader from 'components/ShimmeringResourceLoader';

import { GlobalState } from 'ducks/rootReducer';

import { DashboardResource } from 'interfaces';

interface OwnProps {
  itemsPerPage: number;
  source: string;
}

interface StateFromProps {
  dashboards: DashboardResource[];
  isLoading: boolean;
  errorText?: string;
}

export type TableDashboardResourceListProps = StateFromProps & OwnProps;

export class TableDashboardResourceList extends React.Component<TableDashboardResourceListProps> {
  render() {
    const {
      dashboards,
      errorText,
      isLoading,
      itemsPerPage,
      source,
    } = this.props;
    let content = <ShimmeringResourceLoader numItems={itemsPerPage} />;

    if (!isLoading) {
      content = (
        <ResourceList
          allItems={dashboards}
          emptyText={errorText || undefined}
          itemsPerPage={itemsPerPage}
          source={source}
        />
      );
    }

    return content;
  }
}

export const mapStateToProps = (state: GlobalState) => {
  const relatedDashboards = state.tableMetadata.dashboards;

  return {
    dashboards: relatedDashboards ? relatedDashboards.dashboards : [],
    isLoading: relatedDashboards ? relatedDashboards.isLoading : true,
    errorText: relatedDashboards ? relatedDashboards.errorMessage : '',
  };
};

export default connect<StateFromProps, {}, OwnProps>(mapStateToProps)(
  TableDashboardResourceList
);
