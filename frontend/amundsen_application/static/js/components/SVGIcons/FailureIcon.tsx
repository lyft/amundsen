// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { v4 as uuidv4 } from 'uuid';

import { IconSizes } from 'interfaces';
import { IconProps } from './types';
import { FAILURE_FILL_COLOR } from './constants';

export const FailureIcon: React.FC<IconProps> = ({
  size = IconSizes.REGULAR,
  fill = FAILURE_FILL_COLOR,
}: IconProps) => {
  const id = `failure_icon_${uuidv4()}`;

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 14 14"
      fill="none"
      id={id}
      xmlns="http://www.w3.org/2000/svg"
    >
      <title>Failure</title>
      <circle cx="7" cy="7" r="7" fill={fill} />
      <path
        d="M11.0834 3.73916L10.2609 2.91666L7.00002 6.17749L3.73919 2.91666L2.91669 3.73916L6.17752 6.99999L2.91669 10.2608L3.73919 11.0833L7.00002 7.82249L10.2609 11.0833L11.0834 10.2608L7.82252 6.99999L11.0834 3.73916Z"
        fill="#0C0B31"
      />
    </svg>
  );
};
