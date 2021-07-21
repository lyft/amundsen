// Copyright Contributors to the Amundsen project.	/*
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { Link } from 'react-router-dom';

import {
  getDisplayNameByResource,
  getSourceDisplayName,
} from 'config/config-utils';

import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';

import { updateSearchState } from 'ducks/search/reducer';
import { UpdateSearchStateRequest } from 'ducks/search/types';
import { logClick } from 'utils/analytics';

import { ResourceType } from 'interfaces/Resources';

import { TABLE_VIEW_TEXT } from './constants';

export interface HeaderBulletsProps {
  cluster: string;
  database: string;
  isView: boolean;
}
export interface DispatchFromProps {
  searchDatabase: (databaseText: string) => UpdateSearchStateRequest;
}

export type TableHeaderBulletsProps = HeaderBulletsProps & DispatchFromProps;

export class TableHeaderBullets extends React.Component<TableHeaderBulletsProps> {
  handleClick = (e) => {
    const databaseText = this.props.database;
    logClick(e, {
      target_type: 'database',
      label: databaseText,
    });
    this.props.searchDatabase(databaseText);
  };

  render() {
    const isViewCheck =
      this.props.isView === undefined ? false : this.props.isView;
    return (
      <ul className="header-bullets">
        <li>{getDisplayNameByResource(ResourceType.table)}</li>
        <li>
          <Link to="/search" onClick={this.handleClick}>
            {getSourceDisplayName(
              this.props.database || '',
              ResourceType.table
            )}
          </Link>
        </li>
        <li>{this.props.cluster || ''}</li>
        {isViewCheck && <li>{TABLE_VIEW_TEXT}</li>}
      </ul>
    );
  }
}

export const mapDispatchToProps = (dispatch: any) =>
  bindActionCreators(
    {
      searchDatabase: (databaseText: string) =>
        updateSearchState({
          filters: {
            [ResourceType.table]: { database: databaseText },
          },
          submitSearch: true,
        }),
    },
    dispatch
  );

export default connect<null, DispatchFromProps, HeaderBulletsProps>(
  null,
  mapDispatchToProps
)(TableHeaderBullets);
