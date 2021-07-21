// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';

import './styles.scss';

export interface ChartListProps {
  charts: string[];
}

class ChartList extends React.Component<ChartListProps> {
  render() {
    const { charts } = this.props;
    if (charts.length === 0) {
      return null;
    }

    return (
      <ul className="chart-list list-group">
        {charts.map((chart, index) => (
          <li key={index} className="chart-list-item list-group-item">
            <div className="title-2 truncated">{chart}</div>
          </li>
        ))}
      </ul>
    );
  }
}

export default ChartList;
