// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import * as DocumentTitle from 'react-document-title';
import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import { RouteComponentProps } from 'react-router';

import { getTableLineage } from 'ducks/lineage/reducer';
import { GetTableLineageRequest } from 'ducks/lineage/types';

import { Lineage, LineageItem } from 'interfaces';

import { GlobalState } from 'ducks/rootReducer';
import Breadcrumb from 'components/Breadcrumb';

import GraphLoading from 'components/Lineage/GraphLoading';
import GraphContainer from 'components/Lineage/GraphContainer';
import { buildTableKey } from 'utils/navigationUtils';

import * as Constants from './constants';

const OK_STATUS_CODE = 200;

export interface PropsFromState {
  isLoading: boolean;
  statusCode: number | null;
  lineageTree: Lineage;
}

export interface DispatchFromProps {
  tableLineageGet: (
    key: string,
    depth?: number,
    direction?: string
  ) => GetTableLineageRequest;
}

export interface MatchProps {
  cluster: string;
  database: string;
  schema: string;
  table: string;
}

export type LineagePageProps = PropsFromState &
  DispatchFromProps &
  RouteComponentProps<MatchProps>;

const PageError = () => (
  <div className="container error-label">
    <Breadcrumb />
    <label>{Constants.ERROR_MESSAGE}</label>
  </div>
);

export const LineagePage: React.FC<
  LineagePageProps & RouteComponentProps<any>
> = ({ isLoading, statusCode, tableLineageGet, lineageTree, match }) => {
  const { params } = match;
  const pageTitle = `Lineage Information | ${params.schema}.${params.table}`;
  const [tableKey] = React.useState(buildTableKey(params));

  React.useEffect(() => {
    tableLineageGet(tableKey, 5);
  }, [tableKey]);

  const hasError = statusCode !== OK_STATUS_CODE;

  const rootNode: LineageItem = {
    badges: [],
    cluster: params.cluster,
    database: params.database,
    name: params.table,
    schema: params.schema,
    key: tableKey,
    level: 0,
    parent: null,
    usage: null,
    source: 'a table',
  };

  lineageTree.upstream_entities.push(rootNode);
  lineageTree.downstream_entities.push(rootNode);

  let content: JSX.Element | null = null;
  if (isLoading) {
    content = <GraphLoading />;
  } else if (hasError) {
    content = <PageError />;
  } else {
    content = <GraphContainer rootNode={rootNode} lineage={lineageTree} />;
  }

  return (
    <DocumentTitle title={`${pageTitle} - Amundsen Table Details`}>
      {content}
    </DocumentTitle>
  );
};
export const mapStateToProps = (state: GlobalState) => ({
  isLoading: state.lineage.isLoading,
  statusCode: state.lineage.statusCode,
  lineageTree: state.lineage.lineageTree,
});

export const mapDispatchToProps = (dispatch: any) =>
  bindActionCreators({ tableLineageGet: getTableLineage }, dispatch);

export default connect<PropsFromState, DispatchFromProps>(
  mapStateToProps,
  mapDispatchToProps
)(LineagePage);
