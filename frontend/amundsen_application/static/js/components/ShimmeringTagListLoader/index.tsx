// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import * as times from 'lodash/times';

import './styles.scss';

const DEFAULT_REPETITION = 10;

type ShimmeringTagItemProps = {
  index: number;
};

export const ShimmeringTagItem: React.FC<ShimmeringTagItemProps> = ({
  index,
}: ShimmeringTagItemProps) => (
  <span
    className={`shimmer-tag-loader-item shimmer-tag-loader-item--${index} is-shimmer-animated`}
  />
);

export interface ShimmeringTagListLoaderProps {
  numItems?: 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15;
}

const ShimmeringTagListLoader: React.FC<ShimmeringTagListLoaderProps> = ({
  numItems = DEFAULT_REPETITION,
}: ShimmeringTagListLoaderProps) => (
  <div className="shimmer-tag-list-loader">
    {times(numItems, (idx) => (
      <ShimmeringTagItem key={idx} index={idx} />
    ))}
  </div>
);

export default ShimmeringTagListLoader;
