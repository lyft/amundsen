// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';

import './styles.scss';

const ColumnLineageLoader: React.FC = () => (
  <div className="column-lineage-loader">
    <div className="shimmer-loader-column">
      <div className="shimmer-loader-cell header is-shimmer-animated" />
      <div className="shimmer-loader-cell content is-shimmer-animated" />
    </div>
    <div className="shimmer-loader-column">
      <div className="shimmer-loader-cell header is-shimmer-animated" />
      <div className="shimmer-loader-cell content is-shimmer-animated" />
    </div>
  </div>
);

export default ColumnLineageLoader;
