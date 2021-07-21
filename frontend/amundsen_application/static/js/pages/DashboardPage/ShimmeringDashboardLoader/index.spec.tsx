// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { shallow } from 'enzyme';

import ShimmeringDashboardLoader from '.';

const setup = () => {
  const wrapper = shallow(<ShimmeringDashboardLoader />);

  return wrapper;
};

describe('ShimmeringDashboardLoader', () => {
  describe('render', () => {
    it('should render without errors', () => {
      expect(() => {
        setup();
      }).not.toThrow();
    });

    it('should render three columns', () => {
      const expected = 3;
      const actual = setup().find('.shimmer-loader-column').length;

      expect(actual).toEqual(expected);
    });

    it('should render six cells', () => {
      const expected = 6;
      const actual = setup().find('.shimmer-loader-cell').length;

      expect(actual).toEqual(expected);
    });
  });
});
