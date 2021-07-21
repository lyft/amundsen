import * as React from 'react';
import { Link } from 'react-router-dom';

import { ResourceType, Lineage, LineageItem } from 'interfaces';
import { getSourceIconClass } from 'config/config-utils';
import { getLink } from 'components/ResourceListItem/TableListItem';
import Graph from 'components/Lineage/Graph';

import './styles.scss';

const CONTAINER_TITLE = 'Lineage Graph';
const BACK_TABLE_LINK = 'Back to table details';

export interface GraphContainerProps {
  lineage: Lineage;
  rootNode: LineageItem;
}

export const GraphContainer: React.FC<GraphContainerProps> = ({
  lineage,
  rootNode,
}: GraphContainerProps) => {
  const rootTitle = `${rootNode.schema}.${rootNode.name}`;

  return (
    <div className="resource-detail-layout">
      <header className="resource-header">
        <div className="header-section">
          <span
            className={
              'icon icon-header ' +
              getSourceIconClass(rootNode.database, ResourceType.table)
            }
          />
        </div>
        <div className="header-section header-title">
          <h1 className="header-title-text truncated" title={rootTitle}>
            {rootTitle}
            <span className="lineage-graph-label">{CONTAINER_TITLE}</span>
          </h1>
          <div className="lineage-graph-backlink">
            <Link
              className="resource-list-item table-list-item"
              to={getLink(rootNode, 'table-lineage-page')}
            >
              {BACK_TABLE_LINK}
            </Link>
          </div>
        </div>
        <div className="header-section header-links">
          <Link
            to={getLink(rootNode, 'table-lineage-page')}
            className="btn btn-close clear-button icon-header"
          />
        </div>
      </header>
      <div className="graph-container">
        <Graph lineage={lineage} />
      </div>
    </div>
  );
};

export default GraphContainer;
