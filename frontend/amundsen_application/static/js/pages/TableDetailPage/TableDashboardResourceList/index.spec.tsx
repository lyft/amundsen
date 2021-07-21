// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { shallow } from 'enzyme';

import ResourceList from 'components/ResourceList';
import ShimmeringResourceLoader from 'components/ShimmeringResourceLoader';

import { dashboardSummary } from 'fixtures/metadata/dashboard';
import globalState from 'fixtures/globalState';

import {
  TableDashboardResourceList,
  TableDashboardResourceListProps,
  mapStateToProps,
} from '.';

const setup = (propOverrides?: Partial<TableDashboardResourceListProps>) => {
  const props = {
    itemsPerPage: 10,
    source: 'test',
    dashboards: [],
    isLoading: false,
    errorText: 'test',
    ...propOverrides,
  };
  const wrapper = shallow<TableDashboardResourceList>(
    // eslint-disable-next-line react/jsx-props-no-spreading
    <TableDashboardResourceList {...props} />
  );

  return { props, wrapper };
};

describe('TableDashboardResourceList', () => {
  describe('render', () => {
    it('should render without problems', () => {
      expect(() => {
        setup();
      }).not.toThrow();
    });

    it('should render the resource loader', () => {
      const { props, wrapper } = setup({ isLoading: true });
      const element = wrapper.find(ShimmeringResourceLoader);

      expect(element.length).toEqual(1);
      expect(element.props().numItems).toBe(props.itemsPerPage);
    });

    it('should render the resource list', () => {
      const { props, wrapper } = setup();
      const element = wrapper.find(ResourceList);

      expect(element.length).toEqual(1);
      expect(element.props().allItems).toBe(props.dashboards);
      expect(element.props().emptyText).toBe(props.errorText);
      expect(element.props().itemsPerPage).toBe(props.itemsPerPage);
      expect(element.props().source).toBe(props.source);
    });
  });
});

describe('mapStateToProps', () => {
  describe('when dashboards do not exist on tableMetadata state', () => {
    let result;
    beforeAll(() => {
      result = mapStateToProps(globalState);
    });

    it('sets dashboards to default', () => {
      expect(result.dashboards).toEqual([]);
    });

    it('sets isLoading to default', () => {
      expect(result.isLoading).toBe(true);
    });

    it('sets errorText to default', () => {
      expect(result.errorText).toEqual('');
    });
  });

  describe('when dashboards exist on tableMetadata state', () => {
    let result;
    let testState;
    beforeAll(() => {
      testState = {
        dashboards: {
          dashboards: [dashboardSummary],
          isLoading: false,
          errorText: '',
        },
      };
      result = mapStateToProps({
        ...globalState,
        tableMetadata: {
          ...globalState.tableMetadata,
          ...testState,
        },
      });
    });

    it('sets dashboards to default', () => {
      expect(result.dashboards).toEqual(testState.dashboards.dashboards);
    });
  });
});
