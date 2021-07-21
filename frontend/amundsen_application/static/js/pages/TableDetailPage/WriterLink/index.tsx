// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { OverlayTrigger, Popover } from 'react-bootstrap';

import AvatarLabel from 'components/AvatarLabel';
import { TableWriter } from 'interfaces';
import { logClick } from 'utils/analytics';

export interface WriterLinkProps {
  tableWriter: TableWriter;
}

const WriterLink: React.FC<WriterLinkProps> = ({
  tableWriter,
}: WriterLinkProps) => {
  if (tableWriter === null || tableWriter.application_url === null) {
    return null;
  }
  const image =
    tableWriter.name === 'Airflow' ? '/static/images/airflow.jpeg' : '';

  return (
    <OverlayTrigger
      trigger={['hover', 'focus']}
      placement="top"
      delayHide={200}
      overlay={
        <Popover id="popover-trigger-hover-focus">{tableWriter.id}</Popover>
      }
    >
      <a
        id="explore-writer"
        className="header-link"
        href={tableWriter.application_url}
        onClick={logClick}
        target="_blank"
        rel="noreferrer"
      >
        <AvatarLabel label={tableWriter.name} src={image} />
      </a>
    </OverlayTrigger>
  );
};

export default WriterLink;
