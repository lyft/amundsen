// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';

import ResourceListItem from 'components/ResourceListItem';
import { Resource } from 'interfaces';
import * as Constants from './constants';

import './styles.scss';

export interface ResourceListProps {
  source: string;
  itemsPerPage: number;
  allItems: Resource[];
  emptyText?: string;
  footerTextCollapsed?: string;
  title?: string;
}

interface ResourceListState {
  isExpanded: boolean;
}

class ResourceList extends React.Component<
  ResourceListProps,
  ResourceListState
> {
  public static defaultProps: Partial<ResourceListProps> = {
    emptyText: Constants.DEFAULT_EMPTY_TEXT,
    footerTextCollapsed: Constants.FOOTER_TEXT_COLLAPSED,
  };

  constructor(props) {
    super(props);
    this.state = {
      isExpanded: false,
    };
  }

  onViewAllToggle = () => {
    this.setState({ isExpanded: !this.state.isExpanded });
  };

  render() {
    const {
      allItems,
      emptyText,
      footerTextCollapsed,
      itemsPerPage,
      source,
      title,
    } = this.props;
    const allItemsCount = allItems.length;
    const itemsToRender = this.state.isExpanded
      ? allItems
      : allItems.slice(0, itemsPerPage);

    return (
      <div className="resource-list">
        {title && <div className="resource-list-title title-3">{title}</div>}
        {allItemsCount === 0 && emptyText && (
          <div className="empty-message body-placeholder">{emptyText}</div>
        )}
        {allItemsCount > 0 && (
          <>
            <ul className="list-group">
              {itemsToRender.map((item, index) => {
                const logging = { source, index };
                return (
                  <ResourceListItem item={item} logging={logging} key={index} />
                );
              })}
            </ul>
            <div className="resource-list-footer">
              {allItemsCount > itemsPerPage && (
                /* eslint-disable jsx-a11y/anchor-is-valid */
                <a onClick={this.onViewAllToggle} target="_blank">
                  {this.state.isExpanded
                    ? Constants.FOOTER_TEXT_EXPANDED
                    : footerTextCollapsed}
                </a>
              )}
            </div>
          </>
        )}
      </div>
    );
  }
}

export default ResourceList;
