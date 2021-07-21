// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';

import {
  indexDashboardsEnabled,
  indexFeaturesEnabled,
  indexUsersEnabled,
} from 'config/config-utils';

import { ResourceType } from 'interfaces';

import SearchItem from './SearchItem';

import * as CONSTANTS from '../constants';

export interface SearchItemListProps {
  onItemSelect: (resourceType: ResourceType, updateUrl: boolean) => void;
  searchTerm: string;
}

class SearchItemList extends React.Component<SearchItemListProps, {}> {
  getListItemText = (resourceType: ResourceType): string => {
    switch (resourceType) {
      case ResourceType.dashboard:
        return CONSTANTS.DASHBOARD_ITEM_TEXT;
      case ResourceType.feature:
        return CONSTANTS.FEATURE_ITEM_TEXT;
      case ResourceType.table:
        return CONSTANTS.DATASETS_ITEM_TEXT;
      case ResourceType.user:
        return CONSTANTS.PEOPLE_ITEM_TEXT;
      default:
        return '';
    }
  };

  render = () => {
    const { onItemSelect, searchTerm } = this.props;
    return (
      <ul className="list-group">
        <SearchItem
          listItemText={this.getListItemText(ResourceType.table)}
          onItemSelect={onItemSelect}
          searchTerm={searchTerm}
          resourceType={ResourceType.table}
        />
        {indexDashboardsEnabled() && (
          <SearchItem
            listItemText={this.getListItemText(ResourceType.dashboard)}
            onItemSelect={onItemSelect}
            searchTerm={searchTerm}
            resourceType={ResourceType.dashboard}
          />
        )}
        {indexFeaturesEnabled() && (
          <SearchItem
            listItemText={this.getListItemText(ResourceType.feature)}
            onItemSelect={onItemSelect}
            searchTerm={searchTerm}
            resourceType={ResourceType.feature}
          />
        )}
        {indexUsersEnabled() && (
          <SearchItem
            listItemText={this.getListItemText(ResourceType.user)}
            onItemSelect={onItemSelect}
            searchTerm={searchTerm}
            resourceType={ResourceType.user}
          />
        )}
      </ul>
    );
  };
}

export default SearchItemList;
