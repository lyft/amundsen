// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';

import {
  getDescriptionSourceDisplayName,
  getDescriptionSourceIconPath,
} from 'config/config-utils';
import AvatarLabel from 'components/AvatarLabel';

import { TableSource } from 'interfaces';
import { logClick } from 'utils/analytics';

export interface SourceLinkProps {
  tableSource: TableSource;
}

const SourceLink: React.FC<SourceLinkProps> = ({
  tableSource,
}: SourceLinkProps) => {
  if (tableSource === null || tableSource.source === null) return null;

  return (
    <a
      className="header-link"
      href={tableSource.source}
      id="explore-source"
      onClick={logClick}
      target="_blank"
      rel="noreferrer"
    >
      <AvatarLabel
        label={getDescriptionSourceDisplayName(tableSource.source_type)}
        src={getDescriptionSourceIconPath(tableSource.source_type)}
        round={false}
      />
    </a>
  );
};

export default SourceLink;
