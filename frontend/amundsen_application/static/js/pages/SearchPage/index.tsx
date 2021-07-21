// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import * as DocumentTitle from 'react-document-title';
import { RouteComponentProps } from 'react-router';
import { Search as UrlSearch } from 'history';

import PaginatedApiResourceList from 'components/ResourceList/PaginatedApiResourceList';
import ResourceListHeader from 'components/ResourceList/ResourceListHeader';
import ShimmeringResourceLoader from 'components/ShimmeringResourceLoader';

import { GlobalState } from 'ducks/rootReducer';
import { submitSearchResource, urlDidUpdate } from 'ducks/search/reducer';
import {
  DashboardSearchResults,
  FeatureSearchResults,
  SearchResults,
  SubmitSearchResourceRequest,
  TableSearchResults,
  UrlDidUpdateRequest,
  UserSearchResults,
} from 'ducks/search/types';

import { Resource, ResourceType, SearchType } from 'interfaces';
import SearchPanel from './SearchPanel';
import SearchFilter from './SearchFilter';
import ResourceSelector from './ResourceSelector';

import {
  DOCUMENT_TITLE_SUFFIX,
  PAGE_INDEX_ERROR_MESSAGE,
  RESULTS_PER_PAGE,
  SEARCH_DEFAULT_MESSAGE,
  SEARCH_ERROR_MESSAGE_PREFIX,
  SEARCH_ERROR_MESSAGE_SUFFIX,
  SEARCH_SOURCE_NAME,
  DASHBOARD_RESOURCE_TITLE,
  FEATURE_RESOURCE_TITLE,
  TABLE_RESOURCE_TITLE,
  USER_RESOURCE_TITLE,
  SEARCHPAGE_TITLE,
} from './constants';

import './styles.scss';

export interface StateFromProps {
  hasFilters: boolean;
  searchTerm: string;
  resource: ResourceType;
  isLoading: boolean;
  tables: TableSearchResults;
  dashboards: DashboardSearchResults;
  features: FeatureSearchResults;
  users: UserSearchResults;
}

export interface DispatchFromProps {
  setPageIndex: (pageIndex: number) => SubmitSearchResourceRequest;
  urlDidUpdate: (urlSearch: UrlSearch) => UrlDidUpdateRequest;
}

export type SearchPageProps = StateFromProps &
  DispatchFromProps &
  RouteComponentProps<any>;

export class SearchPage extends React.Component<SearchPageProps> {
  public static defaultProps: Partial<SearchPageProps> = {};

  componentDidMount() {
    this.props.urlDidUpdate(this.props.location.search);
  }

  componentDidUpdate(prevProps: SearchPageProps) {
    if (this.props.location.search !== prevProps.location.search) {
      this.props.urlDidUpdate(this.props.location.search);
    }
  }

  renderSearchResults = () => {
    switch (this.props.resource) {
      case ResourceType.table:
        return this.getTabContent(this.props.tables, ResourceType.table);
      case ResourceType.user:
        return this.getTabContent(this.props.users, ResourceType.user);
      case ResourceType.dashboard:
        return this.getTabContent(
          this.props.dashboards,
          ResourceType.dashboard
        );
      case ResourceType.feature:
        return this.getTabContent(this.props.features, ResourceType.feature);
      default:
        return null;
    }
  };

  generateTabLabel = (tab: ResourceType): string => {
    switch (tab) {
      case ResourceType.dashboard:
        return DASHBOARD_RESOURCE_TITLE;
      case ResourceType.feature:
        return FEATURE_RESOURCE_TITLE;
      case ResourceType.table:
        return TABLE_RESOURCE_TITLE;
      case ResourceType.user:
        return USER_RESOURCE_TITLE;
      default:
        return '';
    }
  };

  getTabContent = (results: SearchResults<Resource>, tab: ResourceType) => {
    const { hasFilters, searchTerm } = this.props;
    const { page_index, total_results } = results;
    const startIndex = RESULTS_PER_PAGE * page_index + 1;
    const tabLabel = this.generateTabLabel(tab);

    // No search input
    if (searchTerm.length === 0 && !hasFilters) {
      return (
        <div className="search-list-container">
          <div className="search-error body-placeholder">
            {SEARCH_DEFAULT_MESSAGE}
          </div>
        </div>
      );
    }

    // Check no results
    if (total_results === 0 && (searchTerm.length > 0 || hasFilters)) {
      return (
        <div className="search-list-container">
          <div className="search-error body-placeholder">
            {SEARCH_ERROR_MESSAGE_PREFIX}
            <i>{tabLabel.toLowerCase()}</i>
            {SEARCH_ERROR_MESSAGE_SUFFIX}
          </div>
        </div>
      );
    }

    // Check page_index bounds
    if (page_index < 0 || startIndex > total_results) {
      return (
        <div className="search-list-container">
          <div className="search-error body-placeholder">
            {PAGE_INDEX_ERROR_MESSAGE}
          </div>
        </div>
      );
    }

    const uniqueResourceTypes = [
      ...new Set(results.results.map(({ type }) => type)),
    ];

    return (
      <div className="search-list-container">
        <ResourceListHeader resourceTypes={uniqueResourceTypes} />
        <PaginatedApiResourceList
          activePage={page_index}
          onPagination={this.props.setPageIndex}
          itemsPerPage={RESULTS_PER_PAGE}
          slicedItems={results.results}
          source={SEARCH_SOURCE_NAME}
          totalItemsCount={total_results}
        />
      </div>
    );
  };

  renderContent = () => {
    if (this.props.isLoading) {
      return <ShimmeringResourceLoader numItems={RESULTS_PER_PAGE} />;
    }

    return this.renderSearchResults();
  };

  render() {
    const { searchTerm } = this.props;
    const innerContent = (
      <div className="search-page">
        <SearchPanel>
          <ResourceSelector />
          <SearchFilter />
        </SearchPanel>
        <main className="search-results">
          <h1 className="sr-only">{SEARCHPAGE_TITLE}</h1>
          {this.renderContent()}
        </main>
      </div>
    );
    if (searchTerm.length > 0) {
      return (
        <DocumentTitle title={`${searchTerm}${DOCUMENT_TITLE_SUFFIX}`}>
          {innerContent}
        </DocumentTitle>
      );
    }
    return innerContent;
  }
}

export const mapStateToProps = (state: GlobalState) => {
  const resourceFilters = state.search.filters[state.search.resource];
  return {
    hasFilters: resourceFilters && Object.keys(resourceFilters).length > 0,
    searchTerm: state.search.search_term,
    resource: state.search.resource,
    isLoading: state.search.isLoading,
    tables: state.search.tables,
    users: state.search.users,
    dashboards: state.search.dashboards,
    features: state.search.features,
  };
};

export const mapDispatchToProps = (dispatch: any) =>
  bindActionCreators(
    {
      urlDidUpdate,
      setPageIndex: (pageIndex: number) =>
        submitSearchResource({
          pageIndex,
          searchType: SearchType.PAGINATION,
          updateUrl: true,
        }),
    },
    dispatch
  );

export default connect<StateFromProps, DispatchFromProps>(
  mapStateToProps,
  mapDispatchToProps
)(SearchPage);
