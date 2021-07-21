// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { shallow } from 'enzyme';

import ColumnLineageLoader from '.';

const setup = () => {
  const wrapper = shallow(<ColumnLineageLoader />);

  return wrapper;
};

describe('ColumnLineageLoader', () => {
  describe('render', () => {
    it('should render without errors', () => {
      expect(() => {
        setup();
      }).not.toThrow();
    });

    it('should render two columns', () => {
      const expected = 2;
      const actual = setup().find('.shimmer-loader-column').length;

      expect(actual).toEqual(expected);
    });

    it('should render four cells', () => {
      const expected = 4;
      const actual = setup().find('.shimmer-loader-cell').length;

      expect(actual).toEqual(expected);
    });
  });
});
