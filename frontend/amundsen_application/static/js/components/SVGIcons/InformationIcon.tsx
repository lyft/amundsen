// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { v4 as uuidv4 } from 'uuid';

import { IconSizes } from 'interfaces';
import { IconProps } from './types';

const DEFAULT_FILL_COLOR = '#9191A8'; // gray40

export const InformationIcon: React.FC<IconProps> = ({
  size = IconSizes.REGULAR,
  fill = DEFAULT_FILL_COLOR,
}: IconProps) => {
  const id = `info_icon_${uuidv4()}`;

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      className="info-svg-icon"
    >
      <title>Info</title>
      <defs>
        <path
          d="M12 21a9 9 0 110-18 9 9 0 010 18zm0-2a7 7 0 100-14 7 7 0 000 14zm1-3.833c0 .46-.448.833-1 .833s-1-.373-1-.833v-3.334c0-.46.448-.833 1-.833s1 .373 1 .833v3.334zM12 10a1 1 0 110-2 1 1 0 010 2z"
          id={id}
        />
      </defs>
      <g fill="none" fillRule="evenodd">
        <mask id="prefix__b" fill="#fff">
          <use xlinkHref={`#${id}`} />
        </mask>
        <use fill={fill} fillRule="nonzero" xlinkHref={`#${id}`} />
      </g>
    </svg>
  );
};
