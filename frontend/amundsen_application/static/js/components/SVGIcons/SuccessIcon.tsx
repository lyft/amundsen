// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { v4 as uuidv4 } from 'uuid';

import { IconSizes } from 'interfaces';
import { IconProps } from './types';
import { SUCCESS_FILL_COLOR } from './constants';

export const SuccessIcon: React.FC<IconProps> = ({
  size = IconSizes.REGULAR,
  fill = SUCCESS_FILL_COLOR,
}: IconProps) => {
  const id = `success_icon_${uuidv4()}`;

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 14 14"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      id={id}
    >
      <title>Success</title>
      <circle cx="7" cy="7" r="7" fill={fill} />
      <path
        d="M5.25 9.45L2.8 7L1.98334 7.81666L5.25 11.0833L12.25 4.08333L11.4333 3.26666L5.25 9.45Z"
        fill="#0C0B31"
      />
    </svg>
  );
};
