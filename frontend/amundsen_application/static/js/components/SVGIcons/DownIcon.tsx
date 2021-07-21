// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { v4 as uuidv4 } from 'uuid';

import { IconSizes } from 'interfaces';
import { IconProps } from './types';
import { DEFAULT_FILL_COLOR } from './constants';

export const DownIcon: React.FC<IconProps> = ({
  size = IconSizes.REGULAR,
  fill = DEFAULT_FILL_COLOR,
}: IconProps) => {
  const id = `down_icon_${uuidv4()}`;

  return (
    <svg width={size} height={size} viewBox="0 0 24 24">
      <title>Down</title>
      <defs>
        <path
          d="M11.987 13.73l4.051-3.918a1.017 1.017 0 011.426.012.983.983 0 01-.012 1.403l-4.733 4.578a1.013 1.013 0 01-.63.283 1.024 1.024 0 01-.814-.277l-4.833-4.59a.975.975 0 01-.018-1.397 1.026 1.026 0 011.432-.018l4.131 3.924z"
          id={id}
        />
      </defs>
      <g fill="none" fillRule="evenodd">
        <mask id="prefix__b" fill="#fff">
          <use xlinkHref={`#${id}`} />
        </mask>
        <use fill={fill} xlinkHref={`#${id}`} />
      </g>
    </svg>
  );
};
