// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { connect } from 'react-redux';

import {
  getSourceDisplayName,
  getSourceIconClass,
  indexDashboardsEnabled,
  indexFeaturesEnabled,
  indexUsersEnabled,
} from 'config/config-utils';
import { buildDashboardURL } from 'utils/navigationUtils';

import { GlobalState } from 'ducks/rootReducer';
import {
  DashboardSearchResults,
  FeatureSearchResults,
  TableSearchResults,
  UserSearchResults,
} from 'ducks/search/types';

import {
  Resource,
  ResourceType,
  DashboardResource,
  FeatureResource,
  TableResource,
  UserResource,
} from 'interfaces';
import ResultItemList from './ResultItemList';
import SearchItemList from './SearchItemList';

import './styles.scss';

import * as CONSTANTS from './constants';

export interface StateFromProps {
  isLoading: boolean;
  dashboards: DashboardSearchResults;
  features: FeatureSearchResults;
  tables: TableSearchResults;
  users: UserSearchResults;
}

export interface OwnProps {
  className?: string;
  onItemSelect: (resourceType: ResourceType, updateUrl?: boolean) => void;
  searchTerm: string;
}

export type InlineSearchResultsProps = StateFromProps & OwnProps;

export interface SuggestedResult {
  href: string;
  iconClass: string;
  subtitle: string;
  titleNode: React.ReactNode;
  type: string;
}

export class InlineSearchResults extends React.Component<
  InlineSearchResultsProps,
  {}
> {
  getTitleForResource = (resourceType: ResourceType): string => {
    switch (resourceType) {
      case ResourceType.dashboard:
        return CONSTANTS.DASHBOARDS;
      case ResourceType.feature:
        return CONSTANTS.FEATURES;
      case ResourceType.table:
        return CONSTANTS.DATASETS;
      case ResourceType.user:
        return CONSTANTS.PEOPLE;
      default:
        return '';
    }
  };

  getTotalResultsForResource = (resourceType: ResourceType): number => {
    switch (resourceType) {
      case ResourceType.dashboard:
        return this.props.dashboards.total_results;
      case ResourceType.feature:
        return this.props.features.total_results;
      case ResourceType.table:
        return this.props.tables.total_results;
      case ResourceType.user:
        return this.props.users.total_results;
      default:
        return 0;
    }
  };

  getResultsForResource = (resourceType: ResourceType): Resource[] => {
    switch (resourceType) {
      case ResourceType.dashboard:
        return this.props.dashboards.results.slice(0, 2);
      case ResourceType.feature:
        return this.props.features.results.slice(0, 2);
      case ResourceType.table:
        return this.props.tables.results.slice(0, 2);
      case ResourceType.user:
        return this.props.users.results.slice(0, 2);
      default:
        return [];
    }
  };

  getSuggestedResultsForResource = (
    resourceType: ResourceType
  ): SuggestedResult[] => {
    const results = this.getResultsForResource(resourceType);
    return results.map((result, index) => ({
      href: this.getSuggestedResultHref(resourceType, result, index),
      iconClass: this.getSuggestedResultIconClass(resourceType, result),
      subtitle: this.getSuggestedResultSubTitle(resourceType, result),
      titleNode: this.getSuggestedResultTitle(resourceType, result),
      type: this.getSuggestedResultType(resourceType, result),
    }));
  };

  getSuggestedResultHref = (
    resourceType: ResourceType,
    result: Resource,
    index: number
  ): string => {
    const logParams = `source=inline_search&index=${index}`;

    switch (resourceType) {
      case ResourceType.dashboard:
        const dashboard = result as DashboardResource;

        return `${buildDashboardURL(dashboard.uri)}?${logParams}`;
      case ResourceType.feature:
        const feature = result as FeatureResource;
        return `/feature/${feature.feature_group}/${feature.name}/${feature.version}?${logParams}`;
      case ResourceType.table:
        const table = result as TableResource;

        return `/table_detail/${table.cluster}/${table.database}/${table.schema}/${table.name}?${logParams}`;
      case ResourceType.user:
        const user = result as UserResource;

        return `/user/${user.user_id}?${logParams}`;
      default:
        return '';
    }
  };

  getSuggestedResultIconClass = (
    resourceType: ResourceType,
    result: Resource
  ): string => {
    let source = '';
    switch (resourceType) {
      case ResourceType.dashboard:
        const dashboard = result as DashboardResource;
        return getSourceIconClass(dashboard.product, resourceType);
      case ResourceType.feature:
        const feature = result as FeatureResource;
        if (feature.availability) {
          source =
            feature.availability.length > 0 ? feature.availability[0] : '';
        }
        return getSourceIconClass(source, resourceType);
      case ResourceType.table:
        const table = result as TableResource;
        return getSourceIconClass(table.database, resourceType);
      case ResourceType.user:
        return CONSTANTS.USER_ICON_CLASS;
      default:
        return '';
    }
  };

  getSuggestedResultSubTitle = (
    resourceType: ResourceType,
    result: Resource
  ): string => {
    switch (resourceType) {
      case ResourceType.dashboard:
        const dashboard = result as DashboardResource;
        return dashboard.description;
      case ResourceType.feature:
        const feature = result as FeatureResource;
        return feature.description;
      case ResourceType.table:
        const table = result as TableResource;
        return table.description;
      case ResourceType.user:
        const user = result as UserResource;
        return user.team_name;
      default:
        return '';
    }
  };

  getSuggestedResultTitle = (
    resourceType: ResourceType,
    result: Resource
  ): React.ReactNode => {
    switch (resourceType) {
      case ResourceType.dashboard:
        const dashboard = result as DashboardResource;
        return (
          <div className="dashboard-title">
            <div className="text-title-w2 dashboard-name">{dashboard.name}</div>
            <div className="text-title-w2 dashboard-group truncated">
              {dashboard.group_name}
            </div>
          </div>
        );
      case ResourceType.feature:
        const feature = result as FeatureResource;
        return (
          <div className="text-title-w2 truncated">
            {`${feature.feature_group}.${feature.name}`}
          </div>
        );
      case ResourceType.table:
        const table = result as TableResource;
        return (
          <div className="text-title-w2 truncated">{`${table.schema}.${table.name}`}</div>
        );
      case ResourceType.user:
        const user = result as UserResource;
        return (
          <div className="text-title-w2 truncated">{user.display_name}</div>
        );
      default:
        return <div className="text-title-w2 truncated" />;
    }
  };

  getSuggestedResultType = (
    resourceType: ResourceType,
    result: Resource
  ): string => {
    let source = '';
    switch (resourceType) {
      case ResourceType.dashboard:
        const dashboard = result as DashboardResource;
        return getSourceDisplayName(dashboard.product, resourceType);
      case ResourceType.feature:
        const feature = result as FeatureResource;
        if (feature.availability) {
          source =
            feature.availability.length > 0 ? feature.availability[0] : '';
        }
        return getSourceDisplayName(source, resourceType);
      case ResourceType.table:
        const table = result as TableResource;
        return getSourceDisplayName(table.database, resourceType);
      case ResourceType.user:
        return CONSTANTS.PEOPLE_USER_TYPE;
      default:
        return '';
    }
  };

  renderResultsByResource = (resourceType: ResourceType) => {
    const suggestedResults = this.getSuggestedResultsForResource(resourceType);
    if (suggestedResults.length === 0) {
      return null;
    }
    return (
      <div className="inline-results-section">
        <ResultItemList
          onItemSelect={this.props.onItemSelect}
          resourceType={resourceType}
          searchTerm={this.props.searchTerm}
          suggestedResults={suggestedResults}
          totalResults={this.getTotalResultsForResource(resourceType)}
          title={this.getTitleForResource(resourceType)}
        />
      </div>
    );
  };

  renderResults = () => {
    if (this.props.isLoading) {
      return null;
    }
    return (
      <>
        {this.renderResultsByResource(ResourceType.table)}
        {indexDashboardsEnabled() &&
          this.renderResultsByResource(ResourceType.dashboard)}
        {indexFeaturesEnabled() &&
          this.renderResultsByResource(ResourceType.feature)}
        {indexUsersEnabled() && this.renderResultsByResource(ResourceType.user)}
      </>
    );
  };

  render() {
    const { className = '', onItemSelect, searchTerm } = this.props;
    return (
      <div id="inline-results" className={`inline-results ${className}`}>
        <div className="inline-results-section search-item-section">
          <SearchItemList onItemSelect={onItemSelect} searchTerm={searchTerm} />
        </div>
        {this.renderResults()}
      </div>
    );
  }
}

export const mapStateToProps = (state: GlobalState) => {
  const {
    isLoading,
    dashboards,
    features,
    tables,
    users,
  } = state.search.inlineResults;
  return {
    isLoading,
    dashboards,
    features,
    tables,
    users,
  };
};

export default connect<StateFromProps, OwnProps>(mapStateToProps)(
  InlineSearchResults
);
