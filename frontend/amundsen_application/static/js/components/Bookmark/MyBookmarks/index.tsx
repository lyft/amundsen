// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { connect } from 'react-redux';

import { GlobalState } from 'ducks/rootReducer';

import { Bookmark, ResourceType, ResourceDict } from 'interfaces';
import {
  getDisplayNameByResource,
  indexDashboardsEnabled,
} from 'config/config-utils';
import PaginatedResourceList from 'components/ResourceList/PaginatedResourceList';
import TabsComponent, { TabInfo } from 'components/TabsComponent';
import ShimmeringResourceLoader from 'components/ShimmeringResourceLoader';
import {
  BOOKMARK_TITLE,
  BOOKMARKS_PER_PAGE,
  EMPTY_BOOKMARK_MESSAGE,
  MY_BOOKMARKS_SOURCE_NAME,
} from './constants';

import './styles.scss';

interface StateFromProps {
  myBookmarks: ResourceDict<Bookmark[]>;
  isLoaded: boolean;
}

export type MyBookmarksProps = StateFromProps;

export class MyBookmarks extends React.Component<MyBookmarksProps> {
  generateTabContent = (resource: ResourceType): JSX.Element | undefined => {
    const bookmarks = this.props.myBookmarks[resource];

    if (!bookmarks) {
      return undefined;
    }

    return (
      <PaginatedResourceList
        allItems={bookmarks}
        emptyText={EMPTY_BOOKMARK_MESSAGE}
        itemsPerPage={BOOKMARKS_PER_PAGE}
        source={MY_BOOKMARKS_SOURCE_NAME}
      />
    );
  };

  generateTabKey = (resource: ResourceType) => `bookmarktab:${resource}`;

  generateTabTitle = (resource: ResourceType): string => {
    const bookmarks = this.props.myBookmarks[resource];

    if (!bookmarks) {
      return '';
    }

    return `${getDisplayNameByResource(resource)} (${bookmarks.length})`;
  };

  generateTabInfo = (): TabInfo[] => {
    const tabInfo: TabInfo[] = [];

    tabInfo.push({
      content: this.generateTabContent(ResourceType.table),
      key: this.generateTabKey(ResourceType.table),
      title: this.generateTabTitle(ResourceType.table),
    });

    if (indexDashboardsEnabled()) {
      tabInfo.push({
        content: this.generateTabContent(ResourceType.dashboard),
        key: this.generateTabKey(ResourceType.dashboard),
        title: this.generateTabTitle(ResourceType.dashboard),
      });
    }

    return tabInfo;
  };

  render() {
    let content = <ShimmeringResourceLoader numItems={BOOKMARKS_PER_PAGE} />;

    if (this.props.isLoaded) {
      content = (
        <TabsComponent
          tabs={this.generateTabInfo()}
          defaultTab={this.generateTabKey(ResourceType.table)}
        />
      );
    }

    return (
      <article className="bookmark-list">
        <h2 className="bookmark-list-header">{BOOKMARK_TITLE}</h2>
        {content}
      </article>
    );
  }
}

export const mapStateToProps = (state: GlobalState) => ({
  myBookmarks: state.bookmarks.myBookmarks,
  isLoaded: state.bookmarks.myBookmarksIsLoaded,
});

export default connect<StateFromProps>(mapStateToProps)(MyBookmarks);
