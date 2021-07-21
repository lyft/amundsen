// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';

import { PopularResource, ResourceDict, ResourceType } from 'interfaces';

import InfoButton from 'components/InfoButton';
import PaginatedResourceList from 'components/ResourceList/PaginatedResourceList';
import TabsComponent, { TabInfo } from 'components/TabsComponent';
import ShimmeringResourceLoader from 'components/ShimmeringResourceLoader';
import {
  getDisplayNameByResource,
  indexDashboardsEnabled,
} from 'config/config-utils';

import { getPopularResources } from 'ducks/popularResources/reducer';
import { GetPopularResourcesRequest } from 'ducks/popularResources/types';
import { GlobalState } from 'ducks/rootReducer';
import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';
import {
  POPULAR_RESOURCES_LABEL,
  POPULAR_RESOURCES_INFO_TEXT,
  POPULAR_RESOURCES_SOURCE_NAME,
  POPULAR_RESOURCES_PER_PAGE,
  EMPTY_POPULAR_RESOURCES_MESSAGE,
} from './constants';

import './styles.scss';

export interface StateFromProps {
  popularResources: ResourceDict<PopularResource[]>;
  isLoaded: boolean;
}

export interface DispatchFromProps {
  getPopularResources: () => GetPopularResourcesRequest;
}

export type PopularResourcesProps = StateFromProps & DispatchFromProps;

const generateTabKey = (resource: ResourceType) =>
  `popularresourcetab:${resource}`;

const generateTabTitle = (
  resource: ResourceType,
  popularResources: ResourceDict<PopularResource[]>
): string => {
  const resources = popularResources[resource];
  if (!resources) {
    return '';
  }

  return `${getDisplayNameByResource(resource)} (${resources.length})`;
};

export class PopularResources extends React.Component<PopularResourcesProps> {
  componentDidMount() {
    // eslint-disable-next-line @typescript-eslint/no-shadow
    const { getPopularResources } = this.props;
    getPopularResources();
  }

  generateTabContent = (resource: ResourceType): JSX.Element | undefined => {
    const { popularResources } = this.props;
    const resources = popularResources[resource];

    if (!resources) {
      return undefined;
    }

    return (
      <PaginatedResourceList
        allItems={resources}
        emptyText={EMPTY_POPULAR_RESOURCES_MESSAGE}
        itemsPerPage={POPULAR_RESOURCES_PER_PAGE}
        source={POPULAR_RESOURCES_SOURCE_NAME}
      />
    );
  };

  generateTabInfo = (): TabInfo[] => {
    const tabInfo: TabInfo[] = [];
    const { popularResources } = this.props;

    tabInfo.push({
      content: this.generateTabContent(ResourceType.table),
      key: generateTabKey(ResourceType.table),
      title: generateTabTitle(ResourceType.table, popularResources),
    });

    if (indexDashboardsEnabled()) {
      tabInfo.push({
        content: this.generateTabContent(ResourceType.dashboard),
        key: generateTabKey(ResourceType.dashboard),
        title: generateTabTitle(ResourceType.dashboard, popularResources),
      });
    }

    return tabInfo;
  };

  render() {
    const { isLoaded } = this.props;
    let content = (
      <ShimmeringResourceLoader numItems={POPULAR_RESOURCES_PER_PAGE} />
    );

    if (isLoaded) {
      content = (
        <TabsComponent
          tabs={this.generateTabInfo()}
          defaultTab={generateTabKey(ResourceType.table)}
        />
      );
    }

    return (
      <article className="popular-table-list">
        <div className="popular-tables-header">
          <h2 className="popular-tables-header-text">
            {POPULAR_RESOURCES_LABEL}
          </h2>
          <InfoButton infoText={POPULAR_RESOURCES_INFO_TEXT} />
        </div>
        {content}
      </article>
    );
  }
}
export const mapStateToProps = (state: GlobalState) => ({
  popularResources: state.popularResources.popularResources,
  isLoaded: state.popularResources.popularResourcesIsLoaded,
});

export const mapDispatchToProps = (dispatch: any) =>
  bindActionCreators({ getPopularResources }, dispatch);

export default connect<StateFromProps, DispatchFromProps>(
  mapStateToProps,
  mapDispatchToProps
)(PopularResources);
