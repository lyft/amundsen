// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';

import { TableMetadata } from 'interfaces';
import { exploreEnabled, generateExploreUrl } from 'config/config-utils';
import { logClick } from 'utils/analytics';

export interface ExploreButtonProps {
  tableData: TableMetadata;
}

class ExploreButton extends React.Component<ExploreButtonProps> {
  render() {
    const url = generateExploreUrl(this.props.tableData);
    if (!url || !exploreEnabled()) {
      return null;
    }

    return (
      <a
        className="btn btn-default btn-lg"
        href={url}
        role="button"
        target="_blank"
        id="explore-sql"
        onClick={logClick}
        rel="noreferrer"
      >
        Explore
      </a>
    );
  }
}

export default ExploreButton;
