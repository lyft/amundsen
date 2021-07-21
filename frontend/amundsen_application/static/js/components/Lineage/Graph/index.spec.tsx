// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { shallow } from 'enzyme';

import { getDimensions, Graph } from './index';

describe('Graph', () => {
  const setup = () => {
    const lineage = {
      downstream_entities: [],
      upstream_entities: [
        {
          badges: [],
          cluster: 'gold',
          database: 'hive',
          key: 'hive://gold.test_schema/test_table1',
          level: 0,
          name: 'test_table1',
          parent: null,
          schema: 'test_schema',
          source: 'hive',
          usage: 0,
        },
      ],
    };
    const wrapper = shallow(<Graph lineage={lineage} />);
    return {
      wrapper,
    };
  };

  describe('test dimensions dreation', () => {
    it('offset the dimensions correctly', () => {
      const dimensions = getDimensions({
        width: 1920,
        height: 1080,
      } as DOMRect);
      expect(dimensions).toMatchObject({ height: 1040, width: 1720 });
    });
  });

  describe('on rendering', () => {
    it('We had the main graph div', () => {
      const { wrapper } = setup();
      expect(wrapper.find('.lineage-graph').exists()).toBe(true);
    });
  });
});
