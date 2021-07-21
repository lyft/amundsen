// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { mocked } from 'ts-jest/utils';
import { mount } from 'enzyme';
import { Provider } from 'react-redux';
import configureStore from 'redux-mock-store';
import { BrowserRouter } from 'react-router-dom';

import { ResourceType } from 'interfaces/Resources';
import {
  getSourceDisplayName,
  getDisplayNameByResource,
} from 'config/config-utils';
import globalState from 'fixtures/globalState';
import TableHeaderBullets, { TableHeaderBulletsProps } from '.';

const MOCK_RESOURCE_DISPLAY_NAME = 'Test';
const MOCK_DB_DISPLAY_NAME = 'AlsoTest';
const TABLE_VIEW_TEXT = 'table view';

jest.mock('config/config-utils', () => ({
  getDisplayNameByResource: jest.fn(),
  getSourceDisplayName: jest.fn(),
}));

let noDatabase;
let noCluster;
let noIsView;

const middlewares = [];
const mockStore = configureStore(middlewares);

const setup = (propOverrides?: Partial<TableHeaderBulletsProps>) => {
  const props = {
    database: 'hive',
    cluster: 'main',
    isView: true,
    ...propOverrides,
  };
  const testState = globalState;
  const wrapper = mount<TableHeaderBulletsProps>(
    <Provider store={mockStore(testState)}>
      <BrowserRouter>
        <TableHeaderBullets {...props} />
      </BrowserRouter>
    </Provider>
  );
  return { props, wrapper };
};

describe('TableHeaderBullets', () => {
  describe('when no props passed', () => {
    const { wrapper } = setup({
      database: noDatabase,
      cluster: noCluster,
      isView: noIsView,
    });
    it('renders TableHeaderBullets element', () => {
      const actual = wrapper.find('.header-bullets').length;
      const expected = 1;

      expect(actual).toEqual(expected);
    });
    it('renders TableHeaderBullets list with default props', () => {
      const actualDatabase = wrapper.find('ul').find('li').at(0).text();
      const expectedDatabase = '';
      const actualCluster = wrapper.find('ul').find('li').at(1).text();
      const expectedCluster = '';
      const actualIsView = wrapper.find('ul').find('li').at(2).text();
      const expectedIsView = '';

      expect(actualDatabase).toEqual(expectedDatabase);
      expect(actualCluster).toEqual(expectedCluster);
      expect(actualIsView).toEqual(expectedIsView);
    });
  });

  describe('when props are defined', () => {
    let props;
    let wrapper;

    beforeAll(() => {
      mocked(getSourceDisplayName).mockImplementation(
        () => MOCK_DB_DISPLAY_NAME
      );
      mocked(getDisplayNameByResource).mockImplementation(
        () => MOCK_RESOURCE_DISPLAY_NAME
      );
      const setupResult = setup();
      props = setupResult.props;
      wrapper = setupResult.wrapper;
    });

    it('renders TableHeaderBullets element', () => {
      const actual = wrapper.find('.header-bullets').length;
      const expected = 1;

      expect(actual).toEqual(expected);
    });
    it('renders a list with resource display name', () => {
      expect(getDisplayNameByResource).toHaveBeenCalledWith(ResourceType.table);
      expect(wrapper.find('ul').find('li').at(0).text()).toEqual(
        MOCK_RESOURCE_DISPLAY_NAME
      );
    });
    it('renders a list with database display name', () => {
      expect(getSourceDisplayName).toHaveBeenCalledWith(
        props.database,
        ResourceType.table
      );
      expect(wrapper.find('ul').find('li').at(1).text()).toEqual(
        MOCK_DB_DISPLAY_NAME
      );
    });
    it('renders a list with cluster', () => {
      expect(wrapper.find('ul').find('li').at(2).text()).toEqual(props.cluster);
    });
    it('renders a list with table view', () => {
      expect(wrapper.find('ul').find('li').at(3).text()).toEqual(
        TABLE_VIEW_TEXT
      );
    });
  });
});
