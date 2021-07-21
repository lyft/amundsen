// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { shallow } from 'enzyme';

import AppConfig from 'config/config';
import globalState from 'fixtures/globalState';

import { NO_DATA_ISSUES_TEXT } from './constants';
import {
  TableIssues,
  TableIssueProps,
  mapStateToProps,
  mapDispatchToProps,
} from '.';

describe('TableIssues', () => {
  const setup = (propOverrides?: Partial<TableIssueProps>) => {
    const props: TableIssueProps = {
      isLoading: false,
      issues: [],
      tableKey: 'key',
      tableName: 'tableName',
      total: 0,
      allIssuesUrl: 'testUrl',
      getIssues: jest.fn(),
      ...propOverrides,
    };
    // eslint-disable-next-line react/jsx-props-no-spreading
    const wrapper = shallow<TableIssues>(<TableIssues {...props} />);
    return {
      props,
      wrapper,
    };
  };

  describe('render', () => {
    beforeAll(() => {
      AppConfig.issueTracking.enabled = true;
    });

    it('renders Shimmer loader if loading', () => {
      const { wrapper } = setup({ isLoading: true });
      const expected = 1;
      const actual = wrapper.find('ShimmeringIssuesLoader').length;

      expect(actual).toEqual(expected);
    });

    it('renders text if no issues', () => {
      const { wrapper } = setup({ issues: [] });
      expect(wrapper.find('.issue-banner').text()).toEqual(NO_DATA_ISSUES_TEXT);
    });

    it('renders issues if they exist', () => {
      AppConfig.issueTracking.enabled = true;
      const { wrapper } = setup({
        issues: [
          {
            issue_key: 'issue_key',
            title: 'title',
            url: 'http://url',
            status: 'Open',
            priority_display_name: 'P2',
            priority_name: 'major',
          },
        ],
      });
      expect(wrapper.find('.table-issue-link').text()).toEqual('issue_key');
      expect(wrapper.find('.issue-title-name').text()).toContain('title');
      expect(wrapper.find('.table-issue-status').text()).toContain('Open');
      expect(wrapper.find('.table-issue-priority').text()).toContain('P2');
    });

    it('renders no link to issues if no issues', () => {
      const { wrapper } = setup({
        issues: [],
        total: 0,
        allIssuesUrl: undefined,
      });
      expect(wrapper.find('.table-issue-more-issues').length).toEqual(0);
    });

    it('renders link if there are issues', () => {
      const { wrapper } = setup({
        issues: [
          {
            issue_key: 'issue_key',
            title: 'title',
            url: 'http://url',
            status: 'Open',
            priority_display_name: 'P2',
            priority_name: 'Major',
          },
        ],
        total: 1,
        allIssuesUrl: 'url',
      });
      expect(wrapper.find('.table-issue-more-issues').text()).toEqual(
        'View all 1 issues'
      );
    });
  });

  describe('mapDispatchToProps', () => {
    let dispatch;
    let props;

    beforeAll(() => {
      dispatch = jest.fn(() => Promise.resolve());
      props = mapDispatchToProps(dispatch);
    });

    it('sets getIssues on the props', () => {
      expect(props.getIssues).toBeInstanceOf(Function);
    });
  });

  describe('mapStateToProps', () => {
    let result;
    beforeAll(() => {
      result = mapStateToProps(globalState);
    });

    it('sets issues on the props', () => {
      expect(result.issues).toEqual(globalState.issue.issues);
    });

    it('sets isLoading on the props', () => {
      expect(result.isLoading).toEqual(globalState.issue.isLoading);
    });
  });
});
