// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';

import './styles.scss';

const ShimmeringDashboardLoader: React.FC = () => (
  <div className="dashboard-shimmer-loader">
    <div className="shimmer-loader-column">
      <div className="shimmer-loader-cell double is-shimmer-animated" />
      <div className="shimmer-loader-cell simple is-shimmer-animated" />
    </div>
    <div className="shimmer-loader-column">
      <div className="shimmer-loader-cell simple is-shimmer-animated" />
      <div className="shimmer-loader-cell double is-shimmer-animated" />
    </div>
    <div className="shimmer-loader-column">
      <div className="shimmer-loader-cell double is-shimmer-animated" />
      <div className="shimmer-loader-cell simple is-shimmer-animated" />
    </div>
  </div>
);

export default ShimmeringDashboardLoader;
