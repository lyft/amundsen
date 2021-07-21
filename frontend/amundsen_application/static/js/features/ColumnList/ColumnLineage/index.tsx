// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { connect } from 'react-redux';

import { GlobalState } from 'ducks/rootReducer';
import { initialLineageState } from 'ducks/lineage/reducer';
import { getColumnLineageLink } from 'config/config-utils';
import { TableMetadata } from 'interfaces/TableMetadata';
import { Lineage, LineageItem } from 'interfaces/Lineage';
import { logClick } from 'utils/analytics';
import ColumnLineageLoader from '../ColumnLineageLoader';
import {
  COLUMN_LINEAGE_LIST_SIZE,
  COLUMN_LINEAGE_DOWNSTREAM_TITLE,
  COLUMN_LINEAGE_UPSTREAM_TITLE,
  COLUMN_LINEAGE_MORE_TEXT,
} from '../constants';

import './styles.scss';

interface ColumnLineageListOwnProps {
  columnName: string;
  tableKey: string;
}

interface StateFromProps {
  columnLineage: Lineage;
  tableData: TableMetadata;
  isLoading: boolean;
}

type ColumnLineageListProps = ColumnLineageListOwnProps & StateFromProps;

interface LineageListProps {
  direction: string;
  lineageItems: LineageItem[];
  link: string;
  title: string;
}

const getLink = (table, direction) => {
  const { cluster, database, schema, name } = table;
  return `/table_detail/${cluster}/${database}/${schema}/${name}?source=column_lineage_${direction}`;
};

const renderLineageLinks = (entity, index, direction) => {
  if (index >= COLUMN_LINEAGE_LIST_SIZE) {
    return null;
  }
  return (
    <div>
      <a
        href={getLink(entity, direction)}
        className="body-link"
        target="_blank"
        rel="noreferrer"
        onClick={(e) =>
          logClick(e, { target_id: `column_lineage`, value: direction })
        }
      >
        {entity.schema}.{entity.name}
      </a>
    </div>
  );
};

const LineageList: React.FC<LineageListProps> = ({
  link,
  direction,
  title,
  lineageItems,
}) => (
  <div className="column-lineage-list">
    <div className="header-row">
      <span className="column-lineage-title">{title}</span>
      <a
        href={link}
        className="body-link"
        rel="noreferrer"
        target="_blank"
        onClick={(e) =>
          logClick(e, {
            target_id: `column_lineage_see_more`,
            value: direction,
          })
        }
      >
        {COLUMN_LINEAGE_MORE_TEXT}
      </a>
    </div>
    {lineageItems.map((item, index) =>
      renderLineageLinks(item, index, direction)
    )}
  </div>
);

export const ColumnLineageList: React.FC<ColumnLineageListProps> = ({
  columnName,
  columnLineage,
  tableData,
  isLoading,
}) => {
  if (isLoading) {
    return <ColumnLineageLoader />;
  }
  const { downstream_entities, upstream_entities } = columnLineage;
  const externalLink = getColumnLineageLink(tableData, columnName);
  if (!downstream_entities.length && !upstream_entities.length) {
    return null;
  }
  return (
    <article className="column-lineage-wrapper">
      {upstream_entities.length !== 0 && (
        <LineageList
          direction="upstream"
          lineageItems={upstream_entities}
          link={externalLink}
          title={COLUMN_LINEAGE_UPSTREAM_TITLE}
        />
      )}
      {downstream_entities.length !== 0 && (
        <LineageList
          direction="downstream"
          lineageItems={downstream_entities}
          link={externalLink}
          title={COLUMN_LINEAGE_DOWNSTREAM_TITLE}
        />
      )}
    </article>
  );
};

export const mapStateToProps = (
  state: GlobalState,
  ownProps: ColumnLineageListOwnProps
) => {
  const { tableData } = state.tableMetadata;
  const { columnLineageMap } = state.lineage;
  const columnStateObject = columnLineageMap[ownProps.columnName];
  const lineage =
    (columnStateObject && columnStateObject.lineageTree) || initialLineageState;
  const isLoading = columnStateObject && columnStateObject.isLoading;
  return {
    tableData,
    isLoading,
    columnLineage: lineage,
  };
};

export default connect<StateFromProps, {}, ColumnLineageListOwnProps>(
  mapStateToProps
)(ColumnLineageList);
