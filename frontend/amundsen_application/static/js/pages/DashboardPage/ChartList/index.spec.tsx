// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';

import { shallow } from 'enzyme';

import ChartList, { ChartListProps } from '.';

describe('ChartList', () => {
  const setup = (propOverrides?: Partial<ChartListProps>) => {
    const props = {
      charts: [],
      ...propOverrides,
    };
    const wrapper = shallow<ChartList>(<ChartList {...props} />);
    return { props, wrapper };
  };

  describe('render', () => {
    it('returns null if no charts', () => {
      const { props, wrapper } = setup({ charts: [] });
      expect(wrapper.type()).toEqual(null);
    });

    it('returns a list item for each chart', () => {
      const { props, wrapper } = setup({ charts: ['chart1', 'chart2'] });
      props.charts.forEach((item, index) => {
        expect(wrapper.find('li').at(index).text()).toBe(item);
      });
    });
  });
});
