// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { MemoryRouter } from 'react-router-dom';
import { mount } from 'enzyme';
import { RouteComponentProps } from 'react-router';
import { getMockRouterProps } from 'fixtures/mockRouter';
import { Provider } from 'react-redux';
import configureStore from 'redux-mock-store';

import globalState from 'fixtures/globalState';

import {
  LineagePage,
  LineagePageProps,
  mapDispatchToProps,
  mapStateToProps,
} from './index';

const useEffectSpy = jest
  .spyOn(React, 'useEffect')
  .mockImplementation((f) => f());

describe('LineagePage', () => {
  const setup = (overrideState = {}) => {
    const middlewares = [];
    const testState = globalState;

    const mockStore = configureStore(middlewares);

    const routerProps = getMockRouterProps<any>({
      cluster: 'cluster',
      database: 'database',
      schema: 'schema',
      table: 'table',
    });

    const props: LineagePageProps & RouteComponentProps<any> = {
      isLoading: false,
      statusCode: 200,
      tableLineageGet: jest.fn(),
      lineageTree: {
        downstream_entities: [
          {
            badges: [],
            cluster: 'gold',
            database: 'hive',
            key: 'hive://gold.test_schema/test_table3',
            level: 1,
            name: 'test_table3',
            parent: 'dynamo://gold.test_schema/test_table2',
            schema: 'test_schema',
            source: 'hive',
            usage: 0,
          },
          {
            badges: [],
            cluster: 'gold',
            database: 'hive',
            key: "hive://gold.test_schema/test's_table4",
            level: 1,
            name: "test's_table4",
            parent: 'dynamo://gold.test_schema/test_table2',
            schema: 'test_schema',
            source: 'hive',
            usage: 0,
          },
        ],
        upstream_entities: [
          {
            badges: [
              {
                badge_name: 'beta',
                category: 'table_status',
              },
            ],
            cluster: 'gold',
            database: 'hive',
            key: 'hive://gold.test_schema/test_table1',
            level: 1,
            name: 'test_table1',
            parent: 'dynamo://gold.test_schema/test_table2',
            schema: 'test_schema',
            source: 'hive',
            usage: 1330,
          },
        ],
      },
      ...routerProps,
      ...overrideState,
    };
    const wrapper = mount(
      <MemoryRouter>
        <Provider store={mockStore(testState)}>
          {/* eslint-disable-next-line react/jsx-props-no-spreading*/}
          <LineagePage {...props} />
        </Provider>
      </MemoryRouter>
    );
    return {
      props,
      wrapper,
    };
  };

  describe('on mounting', () => {
    it('calls the use effect hook', () => {
      const { props } = setup();
      expect(useEffectSpy).toHaveBeenCalled();
      expect(props.tableLineageGet).toHaveBeenCalled();
    });
  });

  describe('on rendering', () => {
    it('displays an svg graph', () => {
      const { wrapper } = setup();
      expect(wrapper.find('Graph').exists()).toBe(true);
    });
  });

  describe('on loading', () => {
    it('displays the loader', () => {
      const { wrapper } = setup({ isLoading: true });
      expect(wrapper.find('GraphLoading').exists()).toBe(true);
    });
  });

  describe('on error', () => {
    it('displays the page error component', () => {
      const { wrapper } = setup({ statusCode: 500 });
      expect(wrapper.find('PageError').exists()).toBe(true);
    });
  });
});

describe('mapDispatchToProps', () => {
  let result;

  beforeEach(() => {
    result = mapDispatchToProps(jest.fn(() => Promise.resolve()));
  });

  it('sets tableLineageGet on the props', () => {
    expect(result.tableLineageGet).toBeInstanceOf(Function);
  });
});

describe('mapStateToProps', () => {
  let result;

  beforeEach(() => {
    result = mapStateToProps(globalState);
  });

  it('sets posts on the props', () => {
    expect(result.lineageTree).toEqual(globalState.lineage.lineageTree);
  });
});
