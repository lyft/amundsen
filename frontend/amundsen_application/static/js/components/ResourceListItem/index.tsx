// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';

import {
  Resource,
  ResourceType,
  DashboardResource,
  FeatureResource,
  TableResource,
  UserResource,
} from 'interfaces';

import { LoggingParams } from './types';
import DashboardListItem from './DashboardListItem';
import FeatureListItem from './FeatureListItem';
import TableListItem from './TableListItem';
import UserListItem from './UserListItem';

import './styles.scss';

export interface ListItemProps {
  logging: LoggingParams;
  item: Resource;
}

export default class ResourceListItem extends React.Component<ListItemProps> {
  render() {
    switch (this.props.item.type) {
      case ResourceType.dashboard:
        return (
          <DashboardListItem
            dashboard={this.props.item as DashboardResource}
            logging={this.props.logging}
          />
        );
      case ResourceType.feature:
        return (
          <FeatureListItem
            feature={this.props.item as FeatureResource}
            logging={this.props.logging}
          />
        );
      case ResourceType.table:
        return (
          <TableListItem
            table={this.props.item as TableResource}
            logging={this.props.logging}
          />
        );
      case ResourceType.user:
        return (
          <UserListItem
            user={this.props.item as UserResource}
            logging={this.props.logging}
          />
        );
      default:
        return null;
    }
  }
}
