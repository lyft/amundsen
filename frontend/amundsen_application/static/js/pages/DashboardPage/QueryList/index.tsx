// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { QueryResource } from 'interfaces';
import QueryListItem from '../QueryListItem';

import './styles.scss';

export interface QueryListProps {
  product: string;
  queries: QueryResource[];
}

class QueryList extends React.Component<QueryListProps> {
  render() {
    const { product, queries } = this.props;

    if (queries.length === 0) {
      return null;
    }

    const queryList = queries.map(({ name, query_text, url }) => (
      <QueryListItem
        key={`key:${name}`}
        product={product}
        text={query_text}
        url={url}
        name={name}
      />
    ));

    return (
      <ul className="query-list list-group" role="tablist">
        {queryList}
      </ul>
    );
  }
}

export default QueryList;
