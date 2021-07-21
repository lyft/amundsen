// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { OverlayTrigger, Popover } from 'react-bootstrap';

import { ResourceType } from 'interfaces';

import { getSourceDisplayName } from 'config/config-utils';

import './styles.scss';
import 'features/CodeBlock/styles.scss';

export interface QueryListItemProps {
  name: string;
  product: string;
  text: string;
  url: string;
}

type GoToDashboardLinkProps = {
  product: string;
  url: string;
};

const QUERY_LABEL = 'Query';
const LINK_TOOLTIP_TEXT = 'View in';
const LazyCodeBlock = React.lazy(() => import('features/CodeBlock/index'));

const GoToDashboardLink = ({ product, url }: GoToDashboardLinkProps) => {
  const productName = getSourceDisplayName(product, ResourceType.dashboard);
  const popoverHoverFocus = (
    <Popover id="popover-trigger-hover-focus">{`${LINK_TOOLTIP_TEXT} ${productName}`}</Popover>
  );

  return (
    <OverlayTrigger
      trigger={['hover', 'focus']}
      placement="top"
      overlay={popoverHoverFocus}
    >
      <a
        className="code-block-link"
        href={url}
        target="_blank"
        rel="noopener noreferrer"
      >
        <svg className="icon" fill="none" viewBox="0 0 24 24">
          <path
            fillRule="evenodd"
            clipRule="evenodd"
            d="M9 3v2.75H5.75v12.5h12.5V15H21v6H3V3h6zm12 0v9.75h-2.75V7.892L10.544 15.6 8.4 13.456l7.707-7.707-4.607.001V3H21z"
          />
        </svg>
      </a>
    </OverlayTrigger>
  );
};

const QueryBlockShimmer = () => (
  <div className="shimmer-block">
    <div className="shimmer-line shimmer-line--1 is-shimmer-animated" />
    <div className="shimmer-line shimmer-line--2 is-shimmer-animated" />
    <div className="shimmer-line shimmer-line--3 is-shimmer-animated" />
    <div className="shimmer-line shimmer-line--4 is-shimmer-animated" />
    <div className="shimmer-line shimmer-line--5 is-shimmer-animated" />
    <div className="shimmer-line shimmer-line--6 is-shimmer-animated" />
  </div>
);

const QueryListItem = ({ product, name, text, url }: QueryListItemProps) => {
  const [isExpanded, setExpanded] = React.useState(false);
  const toggleExpand = () => {
    setExpanded(!isExpanded);
  };
  const key = `key:${name}`;

  return (
    <li className="list-group-item query-list-item" role="tab" id={key}>
      <button
        className="query-list-header"
        aria-expanded={isExpanded}
        aria-controls={key}
        type="button"
        onClick={toggleExpand}
      >
        <p className="query-list-item-name column-name">{name}</p>
      </button>
      {isExpanded && (
        <div className="query-list-expanded-content">
          <label className="query-list-query-label section-title">
            {QUERY_LABEL}:
            <div className="query-list-query-content">
              <React.Suspense fallback={<QueryBlockShimmer />}>
                <LazyCodeBlock text={text}>
                  <GoToDashboardLink product={product} url={url} />
                </LazyCodeBlock>
              </React.Suspense>
            </div>
          </label>
        </div>
      )}
    </li>
  );
};

export default QueryListItem;
