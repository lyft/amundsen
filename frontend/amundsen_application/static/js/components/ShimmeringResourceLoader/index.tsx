// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import * as times from 'lodash/times';

import './styles.scss';

const DEFAULT_REPETITION = 3;

export const ShimmeringResourceItem: React.FC = () => (
  <div className="shimmer-resource-loader-item media">
    <div className="media-left media-middle">
      <div className="shimmer-resource-circle is-shimmer-animated" />
    </div>
    <div className="media-body">
      <div className="shimmer-resource-line shimmer-resource-line--1 is-shimmer-animated" />
      <div className="shimmer-resource-line shimmer-resource-line--2 is-shimmer-animated" />
    </div>
  </div>
);

export interface ShimmeringResourceLoaderProps {
  numItems?: number;
}

const ShimmeringResourceLoader: React.FC<ShimmeringResourceLoaderProps> = ({
  numItems = DEFAULT_REPETITION,
}: ShimmeringResourceLoaderProps) => (
  <div className="shimmer-resource-loader">
    {times(numItems, (idx) => (
      <ShimmeringResourceItem key={idx} />
    ))}
  </div>
);

export default ShimmeringResourceLoader;
