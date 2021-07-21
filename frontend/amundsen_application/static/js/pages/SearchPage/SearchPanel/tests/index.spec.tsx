// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';

import { shallow } from 'enzyme';
import SearchPanel from '..';

describe('SearchPanel', () => {
  const resourceChild = <div>I am a resource selector</div>;
  const filterChild = <div>I am a a set of filters</div>;
  const setup = () => {
    const wrapper = shallow(
      <SearchPanel>
        {resourceChild}
        {filterChild}
      </SearchPanel>
    );
    return { wrapper };
  };

  describe('render', () => {
    let wrapper;

    beforeAll(() => {
      wrapper = setup().wrapper;
    });
    it('renders itself with correct class', () => {
      expect(wrapper.hasClass('search-control-panel')).toBe(true);
    });

    it('renders its children with correct class', () => {
      wrapper.children().forEach((child) => {
        expect(child.props().className).toEqual('section');
      });
    });

    it('renders expected children', () => {
      const children = wrapper.children();
      expect(children.at(0).contains(resourceChild)).toBe(true);
      expect(children.at(1).contains(filterChild)).toBe(true);
    });
  });
});
