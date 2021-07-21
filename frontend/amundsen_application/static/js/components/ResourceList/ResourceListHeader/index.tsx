// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';

import './styles.scss';

import { ResourceType } from 'interfaces';
import {
  RESOURCE_HEADER_TITLE,
  SOURCE_HEADER_TITLE,
  BADGES_HEADER_TITLE,
  LAST_UPDATED_HEADER_TITLE,
  ENTITY_HEADER_TITLE,
} from './constants';

export interface ResourceListHeaderProps {
  resourceTypes: ResourceType[];
}

const resourceTypeToHeaderClassMap = {
  0: 'resource-header',
  1: 'source-header',
  2: 'badge-last-run-header',
  3: 'entity-header',
};

const getResourceHeaders = (type: ResourceType) => {
  switch (type) {
    case ResourceType.dashboard:
      return [
        RESOURCE_HEADER_TITLE,
        SOURCE_HEADER_TITLE,
        LAST_UPDATED_HEADER_TITLE,
      ];
    case ResourceType.feature:
      return [
        RESOURCE_HEADER_TITLE,
        SOURCE_HEADER_TITLE,
        BADGES_HEADER_TITLE,
        ENTITY_HEADER_TITLE,
      ];
    case ResourceType.table:
      return [RESOURCE_HEADER_TITLE, SOURCE_HEADER_TITLE, BADGES_HEADER_TITLE];
    case ResourceType.user:
      return [RESOURCE_HEADER_TITLE, SOURCE_HEADER_TITLE, BADGES_HEADER_TITLE];
    default:
      return [];
  }
};

const ResourceListHeader: React.FC<ResourceListHeaderProps> = ({
  resourceTypes,
}: ResourceListHeaderProps) => {
  const headers = getResourceHeaders(resourceTypes[0]);
  if (headers.length === 0) {
    return null;
  }

  return (
    <div className="resource-list-header">
      {headers?.map((headerText, index) => (
        <span
          className={`${resourceTypeToHeaderClassMap[index]}`}
          key={`${resourceTypeToHeaderClassMap[index]}`}
        >
          <span className="header-text">{headerText}</span>
        </span>
      ))}
    </div>
  );
};

export default ResourceListHeader;
