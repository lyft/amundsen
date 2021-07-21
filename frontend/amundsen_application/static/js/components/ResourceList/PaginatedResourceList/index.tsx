// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import Pagination from 'react-js-pagination';

import ResourceListItem from 'components/ResourceListItem';
import { Resource } from 'interfaces';
import * as Constants from '../constants';

import '../styles.scss';

export interface PaginatedResourceListProps {
  allItems: Resource[];
  emptyText?: string;
  itemsPerPage: number;
  source: string;
}

interface PaginatedResourceListState {
  activePage: number;
}

class PaginatedResourceList extends React.Component<
  PaginatedResourceListProps,
  PaginatedResourceListState
> {
  public static defaultProps: Partial<PaginatedResourceListProps> = {
    emptyText: Constants.DEFAULT_EMPTY_TEXT,
  };

  constructor(props) {
    super(props);
    this.state = {
      activePage: 0,
    };
  }

  componentDidUpdate(prevProps, prevState) {
    //  Resets the activePage to the maximum possible value if page is out of bounds for the new length of allItems
    const effectivePageNum = this.state.activePage + 1;
    const { itemsPerPage, allItems } = this.props;
    const newPage = Math.ceil(allItems.length / itemsPerPage) - 1;
    if (
      itemsPerPage * effectivePageNum > allItems.length &&
      newPage !== this.state.activePage
    ) {
      this.setState({ activePage: newPage });
    }
  }

  onPagination = (rawPageNum: number) => {
    const activePage = rawPageNum - 1;
    this.setState({ activePage });
  };

  render() {
    const { allItems, emptyText, itemsPerPage, source } = this.props;
    const { activePage } = this.state;
    const allItemsCount = allItems.length;

    const startIndex = itemsPerPage * activePage;
    const itemsToRender = this.props.allItems.slice(
      startIndex,
      startIndex + itemsPerPage
    );

    return (
      <div className="paginated-resource-list">
        {allItemsCount === 0 && emptyText && (
          <div className="empty-message body-placeholder">{emptyText}</div>
        )}
        {allItemsCount > 0 && (
          <>
            <ul className="list-group">
              {itemsToRender.map((item, idx) => {
                const logging = { source, index: startIndex + idx };
                return (
                  <ResourceListItem item={item} logging={logging} key={idx} />
                );
              })}
            </ul>
            {allItemsCount > itemsPerPage && (
              <Pagination
                activePage={activePage + 1}
                itemsCountPerPage={itemsPerPage}
                totalItemsCount={allItemsCount}
                pageRangeDisplayed={Constants.PAGINATION_PAGE_RANGE}
                onChange={this.onPagination}
              />
            )}
          </>
        )}
      </div>
    );
  }
}

export default PaginatedResourceList;
