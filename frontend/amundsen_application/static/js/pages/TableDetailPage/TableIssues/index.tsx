// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { GlobalState } from 'ducks/rootReducer';
import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';

import { Issue } from 'interfaces';
import { getIssues } from 'ducks/issue/reducer';
import { GetIssuesRequest } from 'ducks/issue/types';
import { logClick } from 'utils/analytics';
import ReportTableIssue from '../ReportTableIssue';
import { NO_DATA_ISSUES_TEXT } from './constants';
import './styles.scss';

export interface StateFromProps {
  issues: Issue[];
  total?: number;
  allIssuesUrl?: string;
  isLoading: boolean;
}

export interface DispatchFromProps {
  getIssues: (key: string) => GetIssuesRequest;
}

export interface ComponentProps {
  tableKey: string;
  tableName: string;
}

export type TableIssueProps = StateFromProps &
  DispatchFromProps &
  ComponentProps;

const ShimmeringIssuesLoader: React.FC = () => (
  <div className="shimmer-issues">
    <div className="shimmer-issues-row shimmer-issues-line--1 is-shimmer-animated" />
    <div className="shimmer-issues-row shimmer-issues-line--2 is-shimmer-animated" />
  </div>
);

export class TableIssues extends React.Component<TableIssueProps> {
  componentDidMount() {
    const { getIssues, tableKey } = this.props;

    getIssues(tableKey);
  }

  renderIssue = (issue: Issue, index: number) => (
    <div className="issue-banner" key={`issue-${index}`}>
      <span className={`table-issue-priority ${issue.priority_name}`}>
        {issue.priority_display_name}
      </span>
      <a
        id={`table-issue-link-${index}`}
        className="table-issue-link"
        target="_blank"
        href={issue.url}
        onClick={logClick}
        rel="noreferrer"
      >
        <span>{issue.issue_key}</span>
      </a>
      <span className="issue-title-display-text truncated">
        <span className="issue-title-name">{issue.title}</span>
      </span>
      <span className="table-issue-status">{issue.status}</span>
    </div>
  );

  renderIssueTitle = () => <div className="section-title title-3">Issues</div>;

  renderIssueContent = () => {
    const { issues } = this.props;

    if (issues.length === 0) {
      return <div className="issue-banner">{NO_DATA_ISSUES_TEXT}</div>;
    }
    return issues.map(this.renderIssue);
  };

  renderIssueFooter = () => {
    const { issues, tableKey, tableName, allIssuesUrl, total } = this.props;
    const hasIssues = issues.length !== 0;

    const reportIssueLink = (
      <div className={`table-report-new-issue ${hasIssues ? 'ml-1' : ''}`}>
        <ReportTableIssue tableKey={tableKey} tableName={tableName} />
      </div>
    );

    if (!hasIssues) {
      return reportIssueLink;
    }
    return (
      <span className="table-more-issues" key="more-issue-link">
        <a
          id="more-issues-link"
          className="table-issue-more-issues"
          target="_blank"
          rel="noreferrer"
          href={allIssuesUrl}
          onClick={logClick}
        >
          View all {total} issues
        </a>
        |{reportIssueLink}
      </span>
    );
  };

  render() {
    const { isLoading } = this.props;

    if (isLoading) {
      return (
        <>
          {this.renderIssueTitle()}
          <div className="table-issues">
            <ShimmeringIssuesLoader />
          </div>
        </>
      );
    }

    return (
      <>
        {this.renderIssueTitle()}
        <div className="table-issues">{this.renderIssueContent()}</div>
        {this.renderIssueFooter()}
      </>
    );
  }
}

export const mapStateToProps = (state: GlobalState) => ({
  issues: state.issue.issues,
  total: state.issue.total,
  allIssuesUrl: state.issue.allIssuesUrl,
  isLoading: state.issue.isLoading,
});

export const mapDispatchToProps = (dispatch: any) =>
  bindActionCreators({ getIssues }, dispatch);

export default connect<StateFromProps, DispatchFromProps, ComponentProps>(
  mapStateToProps,
  mapDispatchToProps
)(TableIssues);
