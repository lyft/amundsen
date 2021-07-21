// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import SanitizedHTML from 'react-sanitized-html';

import { IconSizes } from 'interfaces';
import { NoticeSeverity } from 'config/config-types';
import { AlertIcon, InformationIcon } from '../SVGIcons';

import './styles.scss';

const SEVERITY_TO_COLOR_MAP = {
  [NoticeSeverity.INFO]: '#3a97d3', // cyan50
  [NoticeSeverity.WARNING]: '#ffb146', // $amber50
  [NoticeSeverity.ALERT]: '#b8072c', // $red70
};

export interface AlertProps {
  message: string | React.ReactNode;
  severity?: NoticeSeverity;
  actionLink?: React.ReactNode;
  actionText?: string;
  actionHref?: string;
  onAction?: (event: React.MouseEvent<HTMLButtonElement>) => void;
}

const Alert: React.FC<AlertProps> = ({
  message,
  severity = NoticeSeverity.WARNING,
  onAction,
  actionText,
  actionHref,
  actionLink,
}: AlertProps) => {
  let action: null | React.ReactNode = null;

  if (actionText && onAction) {
    action = (
      <span className="alert-action">
        <button type="button" className="btn btn-link" onClick={onAction}>
          {actionText}
        </button>
      </span>
    );
  }

  if (actionText && actionHref) {
    action = (
      <span className="alert-action">
        <a className="action-link" href={actionHref}>
          {actionText}
        </a>
      </span>
    );
  }

  if (actionLink) {
    action = <span className="alert-action">{actionLink}</span>;
  }

  let iconComponent: React.ReactNode = null;
  if (severity === NoticeSeverity.INFO) {
    iconComponent = (
      <InformationIcon
        fill={SEVERITY_TO_COLOR_MAP[severity]}
        size={IconSizes.REGULAR}
      />
    );
  } else {
    iconComponent = (
      <AlertIcon
        stroke={SEVERITY_TO_COLOR_MAP[severity]}
        size={IconSizes.SMALL}
      />
    );
  }

  // If we receive a string, we want to sanitize any html inside
  const formattedMessage =
    typeof message === 'string' ? <SanitizedHTML html={message} /> : message;

  return (
    <div className="alert">
      {iconComponent}
      <p className="alert-message">{formattedMessage}</p>
      {action}
    </div>
  );
};

export default Alert;
