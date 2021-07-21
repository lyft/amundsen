// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { OverlayTrigger, Popover } from 'react-bootstrap';
import SanitizedHTML from 'react-sanitized-html';

import { IconSizes } from 'interfaces';
import { InformationIcon } from '../SVGIcons';

import './styles.scss';

const INFO_BUTTON_TEXT = 'More info';
const DEFAULT_PLACEMENT = 'right';

export interface InfoButtonProps {
  infoText?: string;
  title?: string;
  placement?: string;
  size?: IconSizes;
}

const InfoButton: React.FC<InfoButtonProps> = ({
  title,
  infoText,
  placement = DEFAULT_PLACEMENT,
  size = IconSizes.REGULAR,
}: InfoButtonProps) => {
  const popoverHoverFocus = (
    <Popover id="popover-trigger-hover-focus" title={title}>
      <SanitizedHTML html={infoText} />
    </Popover>
  );

  return (
    <OverlayTrigger
      trigger={['hover', 'focus']}
      placement={placement}
      overlay={popoverHoverFocus}
    >
      <button
        className={`btn info-button ${size === IconSizes.SMALL ? 'small' : ''}`}
        type="button"
      >
        <InformationIcon size={size} />
        <span className="sr-only">{INFO_BUTTON_TEXT}</span>
      </button>
    </OverlayTrigger>
  );
};

export default InfoButton;
