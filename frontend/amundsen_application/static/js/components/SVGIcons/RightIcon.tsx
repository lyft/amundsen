// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { v4 as uuidv4 } from 'uuid';

import { IconSizes } from 'interfaces';
import { IconProps } from './types';
import { DEFAULT_FILL_COLOR } from './constants';

export const RightIcon: React.FC<IconProps> = ({
  size = IconSizes.REGULAR,
  fill = DEFAULT_FILL_COLOR,
}: IconProps) => {
  const id = `right_icon_${uuidv4()}`;

  return (
    <svg width={size} height={size} viewBox="0 0 24 24">
      <title>Right</title>
      <defs>
        <path
          d="M11.836 12.968l4.05-3.897a1.02 1.02 0 011.427.014.981.981 0 01-.014 1.4l-4.73 4.553c-.18.174-.409.268-.641.283a1.026 1.026 0 01-.806-.276l-4.83-4.566a.972.972 0 01-.019-1.394 1.028 1.028 0 011.434-.02l4.129 3.903z"
          id={id}
        />
      </defs>
      <g fill="none" fillRule="evenodd">
        <mask id="prefix__b" fill="#fff">
          <use xlinkHref={`#${id}`} />
        </mask>
        <use
          fill={fill}
          xlinkHref={`#${id}`}
          transform="rotate(-90 11.794 12.055)"
        />
      </g>
    </svg>
  );
};
