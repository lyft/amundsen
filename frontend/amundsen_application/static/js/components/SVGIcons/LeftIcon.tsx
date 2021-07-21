// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { v4 as uuidv4 } from 'uuid';

import { IconSizes } from 'interfaces';
import { IconProps } from './types';
import { DEFAULT_FILL_COLOR } from './constants';

export const LeftIcon: React.FC<IconProps> = ({
  size = IconSizes.REGULAR,
  fill = DEFAULT_FILL_COLOR,
}: IconProps) => {
  const id = `left_icon_${uuidv4()}`;

  return (
    <svg width={size} height={size} viewBox="0 0 24 24">
      <title>Left</title>
      <defs>
        <path
          d="M11.694 13l4.136-3.987c.4-.385 1.034-.38 1.427.013a.982.982 0 01-.013 1.401l-4.843 4.67a1.017 1.017 0 01-.857.273 1.005 1.005 0 01-.577-.28l-4.743-4.656a.99.99 0 01-.007-1.408 1.01 1.01 0 011.42-.006L11.695 13z"
          id={id}
        />
      </defs>
      <g fill="none" fillRule="evenodd">
        <mask id="prefix__b" fill="#fff">
          <use xlinkHref={`#${id}`} />
        </mask>
        <use
          fill={fill}
          transform="rotate(90 11.736 12.055)"
          xlinkHref={`#${id}`}
        />
      </g>
    </svg>
  );
};
