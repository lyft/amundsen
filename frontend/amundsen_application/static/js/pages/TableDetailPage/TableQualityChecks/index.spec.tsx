// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { mount, shallow } from 'enzyme';

import { GlobalState } from 'ducks/rootReducer';
import globalState from 'fixtures/globalState';

import {
  mapDispatchToProps,
  mapStateToProps,
  ShimmeringTableQualityChecks,
  TableQualityChecksProps,
  TableQualityChecksLabel,
} from '.';

const setupShimmerTest = () => {
  const wrapper = mount<{}>(<ShimmeringTableQualityChecks />);
  return { wrapper };
};

describe('ShimmeringTableQualityChecks', () => {
  let wrapper;

  describe('render', () => {
    beforeAll(() => {
      ({ wrapper } = setupShimmerTest());
    });

    it('renders a container', () => {
      const actual = wrapper.find('.shimmer-table-quality-checks').length;
      const expected = 1;
      expect(actual).toEqual(expected);
    });

    it('renders a three shimmering items', () => {
      const actual = wrapper.find('.is-shimmer-animated').length;
      const expected = 3;
      expect(actual).toEqual(expected);
    });
  });
});

describe('TableQualityChecks', () => {
  const setup = (propOverrides?: Partial<TableQualityChecksProps>) => {
    const props: TableQualityChecksProps = {
      isLoading: false,
      status: 200,
      tableKey: 'test_key',
      checks: {
        external_url: '',
        last_run_timestamp: null,
        num_checks_success: 10,
        num_checks_failed: 2,
        num_checks_total: 12,
      },
      getTableQualityChecksDispatch: jest.fn(),
      clickDataQualityLinkDispatch: jest.fn(),
      ...propOverrides,
    };
    // eslint-disable-next-line react/jsx-props-no-spreading
    const wrapper = shallow<TableQualityChecksProps>(
      <TableQualityChecksLabel {...props} />
    );
    return {
      props,
      wrapper,
    };
  };

  it('renders Shimmer loader if loading', () => {
    const { wrapper } = setup({ isLoading: true });
    const expected = 1;
    const actual = wrapper.find('ShimmeringTableQualityChecks').length;

    expect(actual).toEqual(expected);
  });

  it('renders nothing if API returns an error', () => {
    const { wrapper } = setup({ status: 404 });
    const expected = 0;
    const actual = wrapper.find('*').length;
    expect(actual).toEqual(expected);
  });

  it('renders normally', () => {
    const { wrapper } = setup();
    const expected = 1;
    const actual = wrapper.find('.table-quality-checks').length;

    expect(actual).toEqual(expected);
  });
});

describe('mapStateToProps', () => {
  let result;
  let expectedProps;
  let mockState: GlobalState;
  beforeAll(() => {
    mockState = {
      ...globalState,
      tableMetadata: {
        ...globalState.tableMetadata,
        tableQualityChecks: {
          status: 200,
          isLoading: false,
          checks: {
            external_url: '',
            last_run_timestamp: null,
            num_checks_success: 10,
            num_checks_failed: 2,
            num_checks_total: 12,
          },
        },
      },
    };
  });

  it('returns expected props from state', () => {
    result = mapStateToProps(mockState);
    expectedProps = {
      status: 200,
      isLoading: false,
      checks: {
        external_url: '',
        last_run_timestamp: null,
        num_checks_success: 10,
        num_checks_failed: 2,
        num_checks_total: 12,
      },
    };
    expect(result.status).toEqual(expectedProps.status);
    expect(result.isLoading).toEqual(expectedProps.isLoading);
    expect(result.checks).toEqual(expectedProps.checks);
  });
});

describe('mapDispatchToProps', () => {
  let dispatch;
  let result;
  beforeAll(() => {
    dispatch = jest.fn(() => Promise.resolve());
    result = mapDispatchToProps(dispatch);
  });

  it('sets getTableQualityChecksDispatch props', () => {
    expect(result.getTableQualityChecksDispatch).toBeInstanceOf(Function);
  });
  it('sets clickDataQualityLinkDispatch props', () => {
    expect(result.clickDataQualityLinkDispatch).toBeInstanceOf(Function);
  });
});
