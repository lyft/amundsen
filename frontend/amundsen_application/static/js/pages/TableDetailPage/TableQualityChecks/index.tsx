// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';

import { GlobalState } from 'ducks/rootReducer';
import {
  ClickTableQualityLinkRequest,
  GetTableQualityChecksRequest,
} from 'ducks/tableMetadata/types';
import {
  clickDataQualityLink,
  getTableQualityChecks,
} from 'ducks/tableMetadata/reducer';
import { IconSizes } from 'interfaces';
import { TableQualityChecks } from 'interfaces/TableMetadata';
import { formatDateTimeShort } from 'utils/dateUtils';
import { FailureIcon } from 'components/SVGIcons/FailureIcon';
import { SuccessIcon } from 'components/SVGIcons/SuccessIcon';
import * as Constants from './constants';

import './styles.scss';

export interface StateFromProps {
  status: number | null;
  checks: TableQualityChecks;
  isLoading: boolean;
}

export interface DispatchFromProps {
  getTableQualityChecksDispatch: (key: string) => GetTableQualityChecksRequest;
  clickDataQualityLinkDispatch: () => ClickTableQualityLinkRequest;
}

export interface ComponentProps {
  tableKey: string;
}

export type TableQualityChecksProps = StateFromProps &
  DispatchFromProps &
  ComponentProps;

export const ShimmeringTableQualityChecks: React.FC = () => (
  <div className="shimmer-table-quality-checks">
    <div className="shimmer-title-row is-shimmer-animated" />
    <div className="shimmer-content-row is-shimmer-animated" />
    <div className="shimmer-content-row is-shimmer-animated" />
  </div>
);

export function generateChecksText(numFailed, numTotal) {
  if (numFailed > 0) {
    return `${numFailed} out of ${numTotal} checks failed`;
  }
  return `All ${numTotal} checks passed`;
}

function getStatusIcon(numFailed) {
  if (numFailed > 0) {
    return <FailureIcon size={IconSizes.SMALL} />;
  }
  return <SuccessIcon size={IconSizes.SMALL} />;
}

export const TableQualityChecksLabel: React.FC<TableQualityChecksProps> = ({
  getTableQualityChecksDispatch,
  clickDataQualityLinkDispatch,
  tableKey,
  isLoading,
  checks,
  status,
}) => {
  React.useEffect(() => {
    getTableQualityChecksDispatch(tableKey);
  }, []);

  if (isLoading) {
    return <ShimmeringTableQualityChecks />;
  }
  if (status !== 200 || checks.num_checks_total === 0) {
    return null;
  }
  const checkText = generateChecksText(
    checks.num_checks_failed,
    checks.num_checks_total
  );
  return (
    <section className="metadata-section table-quality-checks">
      <div className="section-title">{Constants.COMPONENT_TITLE}</div>
      <div className="checks-status">
        {getStatusIcon(checks.num_checks_failed)}
        &nbsp;
        {checkText}
      </div>
      {checks.last_run_timestamp !== null && (
        <div className="last-run-timestamp">
          {Constants.LAST_RUN_LABEL}
          <time>
            {formatDateTimeShort({
              timestamp: checks.last_run_timestamp,
            })}
          </time>
        </div>
      )}
      <a
        href={checks.external_url}
        className="body-link"
        target="_blank"
        rel="noreferrer"
        onClick={clickDataQualityLinkDispatch}
      >
        {Constants.SEE_MORE_LABEL}
      </a>
    </section>
  );
};

export const mapStateToProps = (state: GlobalState) => ({
  status: state.tableMetadata.tableQualityChecks.status,
  isLoading: state.tableMetadata.tableQualityChecks.isLoading,
  checks: state.tableMetadata.tableQualityChecks.checks,
});

export const mapDispatchToProps = (dispatch: any) =>
  bindActionCreators(
    {
      getTableQualityChecksDispatch: getTableQualityChecks,
      clickDataQualityLinkDispatch: clickDataQualityLink,
    },
    dispatch
  );

export default connect<StateFromProps, DispatchFromProps>(
  mapStateToProps,
  mapDispatchToProps
)(TableQualityChecksLabel);
