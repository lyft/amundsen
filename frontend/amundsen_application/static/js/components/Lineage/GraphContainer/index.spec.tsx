// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { MemoryRouter } from 'react-router-dom';
import { mount } from 'enzyme';

import globalState from 'fixtures/globalState';
import { LineageItem } from 'interfaces';
import { GraphContainer } from './index';

const item: LineageItem = {
  badges: [],
  cluster: 'cluster',
  database: 'database',
  key: 'h/root',
  level: 0,
  name: 'table',
  parent: null,
  schema: 'schema',
  usage: null,
};

describe('GraphContainer', () => {
  const setup = () => {
    const props = {
      lineage: globalState.lineage.lineageTree,
      rootNode: item,
    };
    const wrapper = mount(
      <MemoryRouter>
        {/* eslint-disable-next-line react/jsx-props-no-spreading*/}
        <GraphContainer {...props} />
      </MemoryRouter>
    );
    return {
      props,
      wrapper,
    };
  };

  describe('on rendering', () => {
    it('Title is set', () => {
      const { wrapper } = setup();
      expect(wrapper.find('.header-title-text').childAt(0).text()).toBe(
        'schema.table'
      );
    });

    it('Graph is within the container', () => {
      const { wrapper } = setup();
      expect(wrapper.find('.header-title-text').childAt(0).text()).toBe(
        'schema.table'
      );
    });
  });
});
